#!/bin/bash

# Update system
yum update -y

# Install Python 3.11
yum install -y python3.11 python3.11-pip

# Create application directory
mkdir -p /opt/task-manager/backend
cd /opt/task-manager

# Install required packages from requirements.txt
# Note: Copy requirements.txt to /opt/task-manager/backend/ before running this script
# Or install directly:
pip3.11 install fastapi==0.104.1 uvicorn[standard]==0.24.0 boto3==1.29.7 python-multipart==0.0.6 pydantic==2.5.0

# Create systemd service file
cat > /etc/systemd/system/task-manager.service << 'EOF'
[Unit]
Description=Cloud Task Manager FastAPI Application
After=network.target

[Service]
Type=simple
User=ec2-user
WorkingDirectory=/opt/task-manager/backend
Environment="PYTHONUNBUFFERED=1"
Environment="PORT=3000"
Environment="DYNAMO_TABLE=TasksTable"
Environment="UPLOADS_BUCKET=taskmanager-uploads-zainrajper"
Environment="AWS_REGION=us-east-1"
ExecStart=/usr/bin/python3.11 -m uvicorn main:app --host 0.0.0.0 --port 3000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Note: You'll need to copy your application files to /opt/task-manager/backend
# The service expects:
# - /opt/task-manager/backend/main.py
# - /opt/task-manager/backend/routes/
# - /opt/task-manager/backend/services/
# - /opt/task-manager/backend/models/
# - /opt/task-manager/backend/requirements.txt

# Enable and start the service
systemctl daemon-reload
systemctl enable task-manager.service
systemctl start task-manager.service

# Check service status
systemctl status task-manager.service

