#!/bin/bash

# Story Publishing Platform - Bash Deployment Script  
# Optimized for 1GB RAM, 1 vCPU server

set -e  # Exit on any error

# Configuration
DOMAIN="${1:-localhost}"
MONGO_URL="${2:-mongodb://localhost:27017}"
DB_NAME="${3:-story_platform_prod}"
PORT="${4:-80}"
ADMIN_PASSWORD="${5:-admin123}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color

echo -e "${CYAN}🚀 Story Publishing Platform Deployment${NC}"
echo -e "${CYAN}=======================================${NC}"

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker not found. Please install Docker first.${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Docker found${NC}"

# Check if Yarn is available for frontend build
BUILD_FRONTEND=true
if ! command -v yarn &> /dev/null; then
    echo -e "${YELLOW}⚠️  Yarn not found. Using pre-built frontend if available.${NC}"
    BUILD_FRONTEND=false
else
    echo -e "${GREEN}✅ Yarn found${NC}"
fi

# Stop and remove existing container
echo -e "${YELLOW}🛑 Stopping existing container...${NC}"
docker stop story-platform 2>/dev/null || true
docker rm story-platform 2>/dev/null || true

# Build React frontend if Yarn is available
if [ "$BUILD_FRONTEND" = true ]; then
    echo -e "${BLUE}🔨 Building React frontend...${NC}"
    cd frontend
    
    # Install dependencies
    echo -e "📦 Installing frontend dependencies..."
    yarn install
    
    # Build production files
    echo -e "🏗️  Building production files..."
    yarn build
    
    cd ..
    echo -e "${GREEN}✅ Frontend build completed${NC}"
else
    if [ ! -d "frontend/build" ]; then
        echo -e "${RED}❌ No frontend build found and Yarn not available${NC}"
        echo -e "${RED}Please run 'yarn build' in frontend directory first${NC}"
        exit 1
    fi
fi

# Create optimized Dockerfile
echo -e "${BLUE}📄 Creating optimized Dockerfile...${NC}"
cat > Dockerfile << 'EOF'
FROM python:3.9-slim

# Set environment variables for optimization
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONHASHSEED=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

WORKDIR /app

# Copy backend files
COPY backend/ ./backend/
COPY frontend/build/ ./frontend/build/

# Install Python dependencies
RUN pip install --no-cache-dir -r backend/requirements.txt

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/ || exit 1

# Expose port
EXPOSE 8000

# Run the application
CMD ["python", "-m", "uvicorn", "backend.server:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
EOF

# Create .dockerignore for optimization
echo -e "${BLUE}📄 Creating .dockerignore...${NC}"
cat > .dockerignore << 'EOF'
**/.git
**/node_modules
**/.env.local
**/.env.development
**/.env.test.local
**/.env.production.local
**/coverage
**/build
**/.nyc_output
frontend/src
frontend/public
**/*.log
**/.DS_Store
**/Thumbs.db
EOF

# Build Docker image
echo -e "${BLUE}🐳 Building Docker image...${NC}"
docker build -t story-platform . --no-cache

echo -e "${GREEN}✅ Docker image built successfully${NC}"

# Generate secure secret key
SECRET_KEY="change-this-secret-key-in-production-$(date +%s | sha256sum | head -c 32)"

# Run Docker container with resource limits
echo -e "${BLUE}🚀 Starting optimized container...${NC}"
CONTAINER_ID=$(docker run -d \
    --name story-platform \
    -p ${PORT}:8000 \
    --memory=800m \
    --cpus=1.0 \
    --restart unless-stopped \
    -e MONGO_URL="$MONGO_URL" \
    -e DB_NAME="$DB_NAME" \
    -e SECRET_KEY="$SECRET_KEY" \
    story-platform)

echo -e "${GREEN}✅ Container started successfully!${NC}"
echo -e "${CYAN}🆔 Container ID: $CONTAINER_ID${NC}"

# Wait for container to be ready
echo -e "${YELLOW}⏳ Waiting for service to start...${NC}"
sleep 5

# Health check
MAX_ATTEMPTS=12
ATTEMPT=0
HEALTHY=false

while [ $ATTEMPT -lt $MAX_ATTEMPTS ] && [ "$HEALTHY" = false ]; do
    if curl -f -s "http://localhost:$PORT/api/" > /dev/null 2>&1; then
        HEALTHY=true
        echo -e "${GREEN}✅ Service is healthy!${NC}"
    else
        ATTEMPT=$((ATTEMPT + 1))
        echo -e "${YELLOW}⏳ Attempt $ATTEMPT/$MAX_ATTEMPTS - waiting for service...${NC}"
        sleep 5
    fi
done

if [ "$HEALTHY" = false ]; then
    echo -e "${RED}❌ Service failed to start properly${NC}"
    echo -e "${YELLOW}📋 Container logs:${NC}"
    docker logs story-platform
    exit 1
fi

# Display deployment information
echo ""
echo -e "${GREEN}🎉 DEPLOYMENT SUCCESSFUL!${NC}"
echo -e "${GREEN}=========================${NC}"
echo -e "${CYAN}🌐 URL: http://$DOMAIN:$PORT${NC}"
echo -e "${CYAN}👤 Admin Login: admin / $ADMIN_PASSWORD${NC}"
echo -e "${CYAN}🗄️  Database: $MONGO_URL${NC}"
echo -e "${CYAN}📊 Memory Limit: 800MB${NC}"
echo -e "${CYAN}🔧 CPU Limit: 1.0${NC}"
echo ""
echo -e "${YELLOW}📋 Useful Commands:${NC}"
echo -e "${WHITE}  View logs:     docker logs story-platform -f${NC}"
echo -e "${WHITE}  Stop service:  docker stop story-platform${NC}"
echo -e "${WHITE}  Start service: docker start story-platform${NC}"
echo -e "${WHITE}  Remove:        docker rm -f story-platform${NC}"
echo -e "${WHITE}  Stats:         docker stats story-platform${NC}"
echo ""
echo -e "${RED}⚠️  Remember to change admin password in production!${NC}"