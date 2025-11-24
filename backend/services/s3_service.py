import boto3
import os
from typing import Optional
from botocore.exceptions import ClientError
from fastapi import UploadFile


class S3Service:
    def __init__(self):
        self.bucket_name = os.getenv("UPLOADS_BUCKET", "taskmanager-uploads-zainrajper")
        self.region = os.getenv("AWS_REGION", "us-east-1")
        self.s3_client = boto3.client("s3", region_name=self.region)

    def upload_file(self, file: UploadFile, task_id: str) -> str:
        """Upload a file to S3 and return the URL"""
        try:
            # Use the original filename (it already includes the extension)
            filename = file.filename or 'attachment'
            s3_key = f"tasks/{task_id}/{filename}"

            # Read file content
            file_content = file.file.read()

            # Upload to S3
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=file_content,
                ContentType=file.content_type or "application/octet-stream"
            )

            # Generate URL
            url = f"https://{self.bucket_name}.s3.{self.region}.amazonaws.com/{s3_key}"
            return url
        except ClientError as e:
            raise Exception(f"Error uploading file to S3: {str(e)}")

    def delete_file(self, url: str) -> bool:
        """Delete a file from S3 given its URL"""
        try:
            # Extract key from URL
            # URL format: https://bucket-name.s3.region.amazonaws.com/key
            if url.startswith(f"https://{self.bucket_name}.s3"):
                # Split on .amazonaws.com/ to get the key, then remove any query parameters
                key_with_params = url.split(f".amazonaws.com/")[-1]
                # Remove query parameters if present (for presigned URLs)
                key = key_with_params.split('?')[0]
                self.s3_client.delete_object(Bucket=self.bucket_name, Key=key)
                return True
            return False
        except ClientError as e:
            raise Exception(f"Error deleting file from S3: {str(e)}")

    def generate_presigned_url(self, url: str, expiration: int = 3600) -> Optional[str]:
        """Generate a presigned URL for accessing a private S3 object"""
        try:
            # Extract key from URL
            # URL format: https://bucket-name.s3.region.amazonaws.com/key
            # Handle both presigned URLs (with query params) and regular URLs
            if url.startswith(f"https://{self.bucket_name}.s3"):
                # Split on .amazonaws.com/ to get the key, then remove any query parameters
                key_with_params = url.split(f".amazonaws.com/")[-1]
                # Remove query parameters if present (for already presigned URLs)
                key = key_with_params.split('?')[0]
                
                # Generate presigned URL
                presigned_url = self.s3_client.generate_presigned_url(
                    'get_object',
                    Params={'Bucket': self.bucket_name, 'Key': key},
                    ExpiresIn=expiration
                )
                return presigned_url
            return None
        except ClientError as e:
            raise Exception(f"Error generating presigned URL: {str(e)}")

