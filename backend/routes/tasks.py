from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from typing import Optional, List
from uuid import uuid4
from datetime import datetime
import os

from models.task import Task, TaskCreate, TaskUpdate
from services.dynamo_service import DynamoService
from services.s3_service import S3Service

router = APIRouter()
dynamo_service = DynamoService()
s3_service = S3Service()


def _convert_to_presigned_url(task: dict) -> dict:
    """Convert attachmentUrl to presigned URL if it exists"""
    if task.get("attachmentUrl"):
        try:
            presigned_url = s3_service.generate_presigned_url(task["attachmentUrl"])
            if presigned_url:
                task["attachmentUrl"] = presigned_url
        except:
            pass  # Keep original URL if presigned URL generation fails
    return task


@router.post("/tasks", response_model=Task, status_code=201)
async def create_task(
    title: str = Form(...),
    description: str = Form(...),
    status: str = Form(default="pending"),
    file: Optional[UploadFile] = File(None)
):
    """Create a new task"""
    try:
        # Validate status
        if status not in ["pending", "done"]:
            raise HTTPException(status_code=400, detail="Status must be 'pending' or 'done'")

        # Generate task ID and timestamp
        task_id = str(uuid4())
        created_at = datetime.utcnow().isoformat() + "Z"

        # Upload file to S3 if provided
        attachment_url = None
        if file:
            attachment_url = s3_service.upload_file(file, task_id)

        # Create task data
        task_data = {
            "taskId": task_id,
            "title": title,
            "description": description,
            "status": status,
            "createdAt": created_at,
            "attachmentUrl": attachment_url
        }

        # Save to DynamoDB
        created_task = dynamo_service.create_task(task_data)
        return created_task

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tasks", response_model=List[Task])
async def get_all_tasks():
    """Get all tasks"""
    try:
        tasks = dynamo_service.get_all_tasks()
        # Convert attachment URLs to presigned URLs
        tasks = [_convert_to_presigned_url(task) for task in tasks]
        return tasks
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tasks/{task_id}", response_model=Task)
async def get_task(task_id: str):
    """Get a task by ID"""
    try:
        task = dynamo_service.get_task(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        # Convert attachment URL to presigned URL
        task = _convert_to_presigned_url(task)
        return task
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/tasks/{task_id}", response_model=Task)
async def update_task(
    task_id: str,
    title: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    status: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None)
):
    """Update a task"""
    try:
        # Check if task exists
        existing_task = dynamo_service.get_task(task_id)
        if not existing_task:
            raise HTTPException(status_code=404, detail="Task not found")

        # Validate status if provided
        if status and status not in ["pending", "done"]:
            raise HTTPException(status_code=400, detail="Status must be 'pending' or 'done'")

        # Prepare update data
        update_data = {}
        if title is not None:
            update_data["title"] = title
        if description is not None:
            update_data["description"] = description
        if status is not None:
            update_data["status"] = status

        # Handle file upload
        if file:
            # Delete old file if exists
            if existing_task.get("attachmentUrl"):
                try:
                    s3_service.delete_file(existing_task["attachmentUrl"])
                except:
                    pass  # Continue even if deletion fails

            # Upload new file
            attachment_url = s3_service.upload_file(file, task_id)
            update_data["attachmentUrl"] = attachment_url

        # Update task
        if update_data:
            updated_task = dynamo_service.update_task(task_id, update_data)
            # Convert attachment URL to presigned URL
            updated_task = _convert_to_presigned_url(updated_task)
            return updated_task
        else:
            # Convert attachment URL to presigned URL even if no update
            existing_task = _convert_to_presigned_url(existing_task)
            return existing_task

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/tasks/{task_id}", status_code=204)
async def delete_task(task_id: str):
    """Delete a task"""
    try:
        # Check if task exists
        existing_task = dynamo_service.get_task(task_id)
        if not existing_task:
            raise HTTPException(status_code=404, detail="Task not found")

        # Delete attachment from S3 if exists
        if existing_task.get("attachmentUrl"):
            try:
                s3_service.delete_file(existing_task["attachmentUrl"])
            except:
                pass  # Continue even if deletion fails

        # Delete task from DynamoDB
        dynamo_service.delete_task(task_id)
        return None

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tasks/{task_id}/attachment")
async def get_attachment_url(task_id: str):
    """Get a presigned URL for a task's attachment"""
    try:
        task = dynamo_service.get_task(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        attachment_url = task.get("attachmentUrl")
        if not attachment_url:
            raise HTTPException(status_code=404, detail="Task has no attachment")
        
        presigned_url = s3_service.generate_presigned_url(attachment_url)
        if not presigned_url:
            raise HTTPException(status_code=500, detail="Failed to generate presigned URL")
        
        return {"url": presigned_url}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

