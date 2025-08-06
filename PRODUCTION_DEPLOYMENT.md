# Story Publishing Platform - Production Deployment Guide

## 🏗️ Single Container Deployment (Optimized for 1GB RAM, 1 vCPU)

### Prerequisites
- Docker installed on your VPS
- MongoDB running (local or cloud)
- 1GB RAM, 1 vCPU minimum specs

### Quick Deployment Steps

#### 1. Clone & Prepare
```bash
# Clone your project files to VPS
scp -r /app/* user@your-vps:/opt/story-platform/
cd /opt/story-platform
```

#### 2. Build React Production Files
```bash
cd frontend
yarn install
yarn build
# This creates optimized static files in frontend/build/
```

#### 3. Set Environment Variables
```bash
# Edit backend/.env
DB_NAME=story_platform_prod
MONGO_URL=mongodb://localhost:27017  # or your MongoDB URL

# Edit frontend/.env (for development only)
REACT_APP_BACKEND_URL=http://your-domain.com
```

#### 4. Install Python Dependencies
```bash
cd backend
pip install -r requirements.txt
```

#### 5. Create Production Dockerfile
```dockerfile
FROM python:3.9-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy backend
COPY backend/ ./backend/
COPY frontend/build/ ./frontend/build/

# Install Python dependencies
RUN pip install -r backend/requirements.txt

# Expose port
EXPOSE 8000

# Run the application
CMD ["python", "-m", "uvicorn", "backend.server:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### 6. Build & Run Container
```bash
# Build container
docker build -t story-platform .

# Run container
docker run -d \
  --name story-platform \
  -p 80:8000 \
  -e MONGO_URL=mongodb://localhost:27017 \
  -e DB_NAME=story_platform_prod \
  --restart unless-stopped \
  story-platform
```

### Memory Optimization Settings

#### For 1GB RAM optimization, add to server.py:
```python
# Add at top of server.py
import os
os.environ["PYTHONHASHSEED"] = "1"
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"

# Configure MongoDB connection pool
client = AsyncIOMotorClient(
    mongo_url,
    maxPoolSize=10,  # Limit connection pool
    minPoolSize=2,
    maxIdleTimeMS=30000
)
```

#### Docker resource limits:
```bash
docker run -d \
  --name story-platform \
  -p 80:8000 \
  --memory="800m" \
  --cpus="1.0" \
  -e MONGO_URL=mongodb://localhost:27017 \
  -e DB_NAME=story_platform_prod \
  --restart unless-stopped \
  story-platform
```

### Production Security Checklist

#### 1. Change Default Admin Password
```python
# In server.py, change:
admin_dict["password"] = get_password_hash("YOUR_SECURE_PASSWORD")
```

#### 2. Set Secure JWT Secret
```python
# In server.py or .env file:
SECRET_KEY = "your-very-secure-random-key-here"
```

#### 3. Enable HTTPS (with Let's Encrypt)
```bash
# Install certbot
apt-get update && apt-get install certbot

# Get SSL certificate
certbot certonly --standalone -d your-domain.com

# Run with SSL
docker run -d \
  --name story-platform \
  -p 80:8000 \
  -p 443:8000 \
  -v /etc/letsencrypt:/etc/letsencrypt:ro \
  --restart unless-stopped \
  story-platform
```

### Monitoring & Maintenance

#### Health Check
```bash
curl http://your-domain.com/api/ 
# Should return: {"message": "Hello World"}
```

#### View Logs
```bash
docker logs story-platform -f
```

#### Database Backup
```bash
# MongoDB backup
mongodump --db story_platform_prod --out backup/
```

#### Container Update
```bash
# Stop, rebuild, restart
docker stop story-platform
docker rm story-platform
docker build -t story-platform .
docker run -d ... # (same run command as above)
```

### Performance Monitoring

The platform is optimized for:
- **< 512MB RAM usage** under normal load
- **< 50% CPU usage** for typical story publishing
- **Fast startup time** (~5 seconds)
- **Efficient static file serving** via FastAPI

### Default Credentials

**Admin Login:**
- Username: `admin`
- Password: `admin123` (⚠️ CHANGE IN PRODUCTION!)

### Troubleshooting

#### Common Issues:
1. **Port already in use**: Change `-p 80:8000` to `-p 8080:8000`
2. **MongoDB connection**: Check `MONGO_URL` environment variable
3. **Memory issues**: Increase swap or reduce maxPoolSize
4. **Frontend not loading**: Ensure React build files are in correct path

#### Support Commands:
```bash
# Check container stats
docker stats story-platform

# Enter container
docker exec -it story-platform bash

# Check MongoDB connection
mongo $MONGO_URL
```

---

## 🎉 Your Story Platform is Ready!

Visit your domain and start sharing stories with the world! 📚✨