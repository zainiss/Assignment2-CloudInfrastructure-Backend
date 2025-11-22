import boto3
import os
from typing import List, Optional
from botocore.exceptions import ClientError


class DynamoService:
    def __init__(self):
        self.table_name = os.getenv("DYNAMO_TABLE", "TasksTable")
        self.region = os.getenv("AWS_REGION", "us-east-1")
        self.dynamodb = boto3.resource("dynamodb", region_name=self.region)
        self.table = self.dynamodb.Table(self.table_name)

    def create_task(self, task_data: dict) -> dict:
        """Create a new task in DynamoDB"""
        try:
            self.table.put_item(Item=task_data)
            return task_data
        except ClientError as e:
            raise Exception(f"Error creating task: {str(e)}")

    def get_task(self, task_id: str) -> Optional[dict]:
        """Get a task by ID"""
        try:
            response = self.table.get_item(Key={"taskId": task_id})
            return response.get("Item")
        except ClientError as e:
            raise Exception(f"Error getting task: {str(e)}")

    def get_all_tasks(self) -> List[dict]:
        """Get all tasks"""
        try:
            response = self.table.scan()
            return response.get("Items", [])
        except ClientError as e:
            raise Exception(f"Error getting tasks: {str(e)}")

    def update_task(self, task_id: str, update_data: dict) -> Optional[dict]:
        """Update a task"""
        try:
            # Build update expression
            update_expression_parts = []
            expression_attribute_names = {}
            expression_attribute_values = {}

            for key, value in update_data.items():
                if value is not None:
                    update_expression_parts.append(f"#{key} = :{key}")
                    expression_attribute_names[f"#{key}"] = key
                    expression_attribute_values[f":{key}"] = value

            if not update_expression_parts:
                return self.get_task(task_id)

            update_expression = "SET " + ", ".join(update_expression_parts)

            response = self.table.update_item(
                Key={"taskId": task_id},
                UpdateExpression=update_expression,
                ExpressionAttributeNames=expression_attribute_names,
                ExpressionAttributeValues=expression_attribute_values,
                ReturnValues="ALL_NEW"
            )
            return response.get("Attributes")
        except ClientError as e:
            raise Exception(f"Error updating task: {str(e)}")

    def delete_task(self, task_id: str) -> bool:
        """Delete a task"""
        try:
            self.table.delete_item(Key={"taskId": task_id})
            return True
        except ClientError as e:
            raise Exception(f"Error deleting task: {str(e)}")

