import boto3
import os
from typing import Optional
from botocore.exceptions import ClientError
from fastapi import UploadFile
from botocore.config import Config
from urllib.parse import urlparse


class S3Service:
    def __init__(self):
        self.bucket_name = os.getenv("UPLOADS_BUCKET", "taskmanager-uploads-zainrajper")
        self.region = os.getenv("AWS_REGION", "us-east-1")
        # Configure S3 client with signature version v4 for presigned URLs
        config = Config(signature_version='s3v4', region_name=self.region)
        self.s3_client = boto3.client("s3", region_name=self.region, config=config)

    def upload_file(self, file: UploadFile, task_id: str) -> str:
        """Upload a file to S3 and return the S3 key (not URL)"""
        try:
            # Generate a unique filename
            file_extension = os.path.splitext(file.filename)[1] if file.filename else ""
            s3_key = f"tasks/{task_id}/{file.filename or 'attachment'}{file_extension}"

            # Read file content
            file_content = file.file.read()

            # Upload to S3
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=file_content,
                ContentType=file.content_type or "application/octet-stream"
            )

            # Return S3 key instead of URL (we'll generate presigned URLs on retrieval)
            return s3_key
        except ClientError as e:
            raise Exception(f"Error uploading file to S3: {str(e)}")

    def get_presigned_url(self, s3_key: str, expiration: int = 3600) -> Optional[str]:
        """Generate a presigned URL for downloading a file from S3"""
        try:
            if not s3_key:
                return None
            
            # Handle both S3 keys and legacy URLs
            key = self._extract_key_from_url_or_key(s3_key)
            if not key:
                return None

            # Generate presigned URL using get_object operation
            presigned_url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': key
                },
                ExpiresIn=expiration
            )
            return presigned_url
        except ClientError as e:
            raise Exception(f"Error generating presigned URL: {str(e)}")

    def _extract_key_from_url_or_key(self, url_or_key: str) -> Optional[str]:
        """Extract S3 key from URL or return the key if it's already a key"""
        if not url_or_key:
            return None
        
        # If it's already a key (starts with "tasks/"), return as is
        if url_or_key.startswith("tasks/"):
            return url_or_key
        
        # If it's a URL, extract the key
        try:
            # Handle different URL formats
            if url_or_key.startswith("https://"):
                # Format: https://bucket-name.s3.region.amazonaws.com/key
                if f".amazonaws.com/" in url_or_key:
                    key = url_or_key.split(".amazonaws.com/")[-1]
                    return key
                # Format: https://s3.region.amazonaws.com/bucket-name/key
                elif f"s3.{self.region}.amazonaws.com/{self.bucket_name}/" in url_or_key:
                    key = url_or_key.split(f"{self.bucket_name}/")[-1]
                    return key
                # Try parsing as URL
                parsed = urlparse(url_or_key)
                if parsed.path:
                    # Remove leading slash
                    key = parsed.path.lstrip('/')
                    return key
            # If it starts with s3://, extract key
            elif url_or_key.startswith("s3://"):
                # Format: s3://bucket-name/key
                key = url_or_key.replace(f"s3://{self.bucket_name}/", "")
                return key
        except Exception:
            pass
        
        # If we can't parse it, assume it's already a key
        return url_or_key

    def delete_file(self, url_or_key: str) -> bool:
        """Delete a file from S3 given its URL or key"""
        try:
            key = self._extract_key_from_url_or_key(url_or_key)
            if not key:
                return False
            
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=key)
            return True
        except ClientError as e:
            raise Exception(f"Error deleting file from S3: {str(e)}")

