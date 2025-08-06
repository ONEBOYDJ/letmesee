# Story Publishing Platform - PowerShell Deployment Script
# Optimized for 1GB RAM, 1 vCPU server

param(
    [string]$Domain = "localhost",
    [string]$MongoUrl = "mongodb://localhost:27017",
    [string]$DbName = "story_platform_prod",
    [int]$Port = 80,
    [string]$AdminPassword = "admin123"
)

Write-Host "🚀 Story Publishing Platform Deployment" -ForegroundColor Cyan
Write-Host "=======================================" -ForegroundColor Cyan

# Check if Docker is installed
try {
    docker --version | Out-Null
    Write-Host "✅ Docker found" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker not found. Please install Docker first." -ForegroundColor Red
    exit 1
}

# Check if Node.js/Yarn is available for frontend build
$buildFrontend = $true
try {
    yarn --version | Out-Null
    Write-Host "✅ Yarn found" -ForegroundColor Green
} catch {
    Write-Host "⚠️  Yarn not found. Using pre-built frontend if available." -ForegroundColor Yellow
    $buildFrontend = $false
}

# Stop and remove existing container
Write-Host "🛑 Stopping existing container..." -ForegroundColor Yellow
docker stop story-platform 2>$null
docker rm story-platform 2>$null

# Build React frontend if Yarn is available
if ($buildFrontend) {
    Write-Host "🔨 Building React frontend..." -ForegroundColor Blue
    Set-Location "frontend"
    
    # Install dependencies
    Write-Host "📦 Installing frontend dependencies..."
    yarn install
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Frontend dependency installation failed" -ForegroundColor Red
        exit 1
    }
    
    # Build production files
    Write-Host "🏗️  Building production files..."
    yarn build
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Frontend build failed" -ForegroundColor Red
        exit 1
    }
    
    Set-Location ".."
    Write-Host "✅ Frontend build completed" -ForegroundColor Green
} else {
    if (!(Test-Path "frontend/build")) {
        Write-Host "❌ No frontend build found and Yarn not available" -ForegroundColor Red
        Write-Host "Please run 'yarn build' in frontend directory first" -ForegroundColor Red
        exit 1
    }
}

# Create Dockerfile
Write-Host "📄 Creating optimized Dockerfile..." -ForegroundColor Blue
@"
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
"@ | Out-File -FilePath "Dockerfile" -Encoding UTF8

# Create .dockerignore for optimization
Write-Host "📄 Creating .dockerignore..." -ForegroundColor Blue
@"
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
"@ | Out-File -FilePath ".dockerignore" -Encoding UTF8

# Build Docker image
Write-Host "🐳 Building Docker image..." -ForegroundColor Blue
docker build -t story-platform . --no-cache
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Docker build failed" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Docker image built successfully" -ForegroundColor Green

# Run Docker container with resource limits
Write-Host "🚀 Starting optimized container..." -ForegroundColor Blue
$dockerArgs = @(
    "run", "-d",
    "--name", "story-platform",
    "-p", "${Port}:8000",
    "--memory=800m",
    "--cpus=1.0",
    "--restart", "unless-stopped",
    "-e", "MONGO_URL=$MongoUrl",
    "-e", "DB_NAME=$DbName",
    "-e", "SECRET_KEY=change-this-secret-key-in-production-$(Get-Random)",
    "story-platform"
)

$containerId = docker @dockerArgs
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to start container" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Container started successfully!" -ForegroundColor Green
Write-Host "🆔 Container ID: $containerId" -ForegroundColor Cyan

# Wait for container to be ready
Write-Host "⏳ Waiting for service to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# Health check
$maxAttempts = 12
$attempt = 0
$healthy = $false

while ($attempt -lt $maxAttempts -and !$healthy) {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:$Port/api/" -TimeoutSec 5 -ErrorAction Stop
        if ($response.StatusCode -eq 200) {
            $healthy = $true
            Write-Host "✅ Service is healthy!" -ForegroundColor Green
        }
    } catch {
        $attempt++
        Write-Host "⏳ Attempt $attempt/$maxAttempts - waiting for service..." -ForegroundColor Yellow
        Start-Sleep -Seconds 5
    }
}

if (!$healthy) {
    Write-Host "❌ Service failed to start properly" -ForegroundColor Red
    Write-Host "📋 Container logs:" -ForegroundColor Yellow
    docker logs story-platform
    exit 1
}

# Display deployment information
Write-Host ""
Write-Host "🎉 DEPLOYMENT SUCCESSFUL!" -ForegroundColor Green
Write-Host "=========================" -ForegroundColor Green
Write-Host "🌐 URL: http://$Domain:$Port" -ForegroundColor Cyan
Write-Host "👤 Admin Login: admin / $AdminPassword" -ForegroundColor Cyan
Write-Host "🗄️  Database: $MongoUrl" -ForegroundColor Cyan
Write-Host "📊 Memory Limit: 800MB" -ForegroundColor Cyan
Write-Host "🔧 CPU Limit: 1.0" -ForegroundColor Cyan
Write-Host ""
Write-Host "📋 Useful Commands:" -ForegroundColor Yellow
Write-Host "  View logs:     docker logs story-platform -f" -ForegroundColor White
Write-Host "  Stop service:  docker stop story-platform" -ForegroundColor White
Write-Host "  Start service: docker start story-platform" -ForegroundColor White
Write-Host "  Remove:        docker rm -f story-platform" -ForegroundColor White
Write-Host "  Stats:         docker stats story-platform" -ForegroundColor White
Write-Host ""
Write-Host "⚠️  Remember to change admin password in production!" -ForegroundColor Red