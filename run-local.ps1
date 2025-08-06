# Story Publishing Platform - Local Development Script for Windows 11
# Run this script to test everything locally with one command

param(
    [int]$Port = 8080,
    [switch]$WithMongoDB = $false
)

# Colors for PowerShell output
$Red = "Red"
$Green = "Green" 
$Yellow = "Yellow"
$Cyan = "Cyan"
$White = "White"

Write-Host "🚀 Story Publishing Platform - Local Test" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan

# Check if Docker Desktop is running
try {
    $dockerInfo = docker info 2>$null
    if ($LASTEXITCODE -ne 0) {
        throw "Docker not running"
    }
    Write-Host "✅ Docker Desktop is running" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker Desktop not running. Please start Docker Desktop first." -ForegroundColor Red
    Write-Host "💡 Download from: https://www.docker.com/products/docker-desktop" -ForegroundColor Yellow
    exit 1
}

# Stop any existing containers
Write-Host "🛑 Cleaning up existing containers..." -ForegroundColor Yellow
docker stop story-platform-local 2>$null | Out-Null
docker rm story-platform-local 2>$null | Out-Null
docker stop mongodb-local 2>$null | Out-Null  
docker rm mongodb-local 2>$null | Out-Null

# Start MongoDB container if requested
$MongoUrl = "mongodb://mongodb:27017"
if ($WithMongoDB) {
    Write-Host "🗄️  Starting local MongoDB..." -ForegroundColor Cyan
    docker run -d --name mongodb-local -p 27017:27017 mongo:latest
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Failed to start MongoDB container" -ForegroundColor Red
        exit 1
    }
    Write-Host "✅ MongoDB started on port 27017" -ForegroundColor Green
    $MongoUrl = "mongodb://host.docker.internal:27017"
    Start-Sleep -Seconds 3
} else {
    Write-Host "📝 Using MongoDB connection: mongodb://host.docker.internal:27017" -ForegroundColor Yellow
    Write-Host "💡 If you don't have MongoDB, run with -WithMongoDB flag" -ForegroundColor Yellow
}

# Check if we need to build frontend
$buildFrontend = $true
if (!(Test-Path "frontend\node_modules") -or !(Test-Path "frontend\build")) {
    Write-Host "🔨 Building frontend for the first time..." -ForegroundColor Blue
    
    # Check for Node.js/Yarn
    try {
        yarn --version | Out-Null
        Write-Host "✅ Yarn found" -ForegroundColor Green
    } catch {
        Write-Host "❌ Yarn not found. Installing Node.js and Yarn..." -ForegroundColor Red
        Write-Host "💡 Please install Node.js from https://nodejs.org/" -ForegroundColor Yellow
        Write-Host "💡 Then run: npm install -g yarn" -ForegroundColor Yellow
        exit 1
    }
    
    # Build frontend
    Set-Location "frontend"
    Write-Host "📦 Installing dependencies..." -ForegroundColor Blue
    yarn install
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Frontend installation failed" -ForegroundColor Red
        Set-Location ".."
        exit 1
    }
    
    Write-Host "🏗️  Building production files..." -ForegroundColor Blue
    yarn build  
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Frontend build failed" -ForegroundColor Red
        Set-Location ".."
        exit 1
    }
    
    Set-Location ".."
    Write-Host "✅ Frontend ready" -ForegroundColor Green
} else {
    Write-Host "✅ Frontend already built" -ForegroundColor Green
}

# Create local Dockerfile
Write-Host "📄 Creating local Dockerfile..." -ForegroundColor Blue
@"
FROM python:3.9-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY backend/ ./backend/
COPY frontend/build/ ./frontend/build/

RUN pip install -r backend/requirements.txt

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "backend.server:app", "--host", "0.0.0.0", "--port", "8000"]
"@ | Out-File -FilePath "Dockerfile.local" -Encoding UTF8

# Build Docker image
Write-Host "🐳 Building local Docker image..." -ForegroundColor Blue
docker build -f Dockerfile.local -t story-platform-local .
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Docker build failed" -ForegroundColor Red
    exit 1
}

# Run the container
Write-Host "🚀 Starting local development server..." -ForegroundColor Blue
$containerId = docker run -d `
    --name story-platform-local `
    -p ${Port}:8000 `
    -e "MONGO_URL=$MongoUrl" `
    -e "DB_NAME=story_platform_local" `
    -e "SECRET_KEY=local-development-secret-key" `
    story-platform-local

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to start container" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Container started!" -ForegroundColor Green
Write-Host "🆔 Container ID: $containerId" -ForegroundColor Cyan

# Wait for startup
Write-Host "⏳ Waiting for service to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# Health check with retries
$maxAttempts = 10
$attempt = 0
$healthy = $false
$testUrl = "http://localhost:$Port/api/"

while ($attempt -lt $maxAttempts -and !$healthy) {
    try {
        $response = Invoke-WebRequest -Uri $testUrl -TimeoutSec 5 -ErrorAction Stop
        if ($response.StatusCode -eq 200) {
            $healthy = $true
            Write-Host "✅ Service is healthy and ready!" -ForegroundColor Green
        }
    } catch {
        $attempt++
        Write-Host "⏳ Attempt $attempt/$maxAttempts - service starting..." -ForegroundColor Yellow
        Start-Sleep -Seconds 3
    }
}

if (!$healthy) {
    Write-Host "❌ Service failed to start" -ForegroundColor Red
    Write-Host "📋 Container logs:" -ForegroundColor Yellow
    docker logs story-platform-local
    Write-Host ""
    Write-Host "🔧 Troubleshooting:" -ForegroundColor Yellow
    Write-Host "  - Check if MongoDB is running" -ForegroundColor White
    Write-Host "  - Try running with -WithMongoDB flag" -ForegroundColor White
    exit 1
}

# Success! Show connection info
Write-Host ""
Write-Host "🎉 LOCAL DEVELOPMENT READY!" -ForegroundColor Green
Write-Host "===========================" -ForegroundColor Green
Write-Host ""
Write-Host "🌐 Website:      http://localhost:$Port" -ForegroundColor Cyan
Write-Host "🔗 API:          http://localhost:$Port/api/" -ForegroundColor Cyan  
Write-Host "👤 Admin Login:  admin / admin123" -ForegroundColor Cyan
Write-Host ""
Write-Host "🎯 Test the platform:" -ForegroundColor Yellow
Write-Host "  1. Go to http://localhost:$Port" -ForegroundColor White
Write-Host "  2. Click 'Need an account? Sign up'" -ForegroundColor White
Write-Host "  3. Register a new user" -ForegroundColor White
Write-Host "  4. Write a story with the rich editor" -ForegroundColor White
Write-Host "  5. Login as admin (admin/admin123) to approve" -ForegroundColor White
Write-Host "  6. Check public stories page" -ForegroundColor White
Write-Host ""
Write-Host "🛠️  Development commands:" -ForegroundColor Yellow
Write-Host "  View logs:    docker logs story-platform-local -f" -ForegroundColor White
Write-Host "  Stop:         docker stop story-platform-local" -ForegroundColor White
Write-Host "  Restart:      docker restart story-platform-local" -ForegroundColor White
Write-Host "  Clean up:     docker rm -f story-platform-local" -ForegroundColor White
if ($WithMongoDB) {
    Write-Host "  Stop MongoDB: docker stop mongodb-local" -ForegroundColor White
}
Write-Host ""

# Auto-open browser
$openBrowser = Read-Host "🌐 Open browser automatically? (y/n)"
if ($openBrowser -eq 'y' -or $openBrowser -eq 'Y' -or $openBrowser -eq '') {
    Start-Process "http://localhost:$Port"
    Write-Host "🚀 Browser opened!" -ForegroundColor Green
}

Write-Host ""
Write-Host "✨ Happy coding! Your story platform is ready for testing." -ForegroundColor Green