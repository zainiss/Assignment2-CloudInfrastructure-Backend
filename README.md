# Cloud Task Manager Backend

A FastAPI-based backend for a Cloud Task Manager application with AWS DynamoDB and S3 integration.

## Features

- Full CRUD operations for tasks
- File upload support with S3 storage
- DynamoDB for task persistence
- Health check endpoint
- RESTful API design

## Project Structure

```
backend/
  ├── main.py                 # FastAPI application entry point
  ├── routes/
  │   └── tasks.py           # Task CRUD endpoints
  ├── services/
  │   ├── dynamo_service.py  # DynamoDB operations
  │   └── s3_service.py      # S3 file operations
  ├── models/
  │   └── task.py            # Task data models
  └── requirements.txt        # Python dependencies
```

## API Endpoints

- `POST /tasks` - Create a new task (supports file upload)
- `GET /tasks` - Get all tasks
- `GET /tasks/{taskId}` - Get a specific task
- `PUT /tasks/{taskId}` - Update a task (supports file upload)
- `DELETE /tasks/{taskId}` - Delete a task
- `GET /health` - Health check endpoint

## Environment Variables

- `DYNAMO_TABLE` - DynamoDB table name (default: "TasksTable")
- `UPLOADS_BUCKET` - S3 bucket name (default: "taskmanager-uploads-zainrajper")
- `AWS_REGION` - AWS region (default: "us-east-1")
- `PORT` - Server port (default: 3000)

## Local Setup

1. Install dependencies:
```bash
cd backend
pip install -r requirements.txt
```

2. Set environment variables:
```bash
export DYNAMO_TABLE=TasksTable
export UPLOADS_BUCKET=taskmanager-uploads-zainrajper
export AWS_REGION=us-east-1
export PORT=3000
```

3. Configure AWS credentials (via AWS CLI or environment variables)

4. Run the application:
```bash
python main.py
```

Or using uvicorn directly:
```bash
uvicorn main:app --host 0.0.0.0 --port 3000
```

## EC2 Deployment

1. Copy the entire `backend/` directory to `/opt/task-manager/backend/` on your EC2 instance
2. Use the provided `user-data.sh` script during EC2 instance launch
3. Ensure your EC2 instance has an IAM role with permissions for:
   - DynamoDB (read/write access to TasksTable)
   - S3 (read/write access to the uploads bucket)

## Task Model

Each task contains:
- `taskId` (UUID string) - Auto-generated
- `title` (string) - Task title
- `description` (string) - Task description
- `status` (string) - Either "pending" or "done"
- `createdAt` (ISO timestamp) - Auto-generated
- `attachmentUrl` (optional string) - S3 URL if file is uploaded

## File Uploads

Files can be uploaded when creating or updating tasks. Files are stored in S3 under the path: `tasks/{taskId}/{filename}`

