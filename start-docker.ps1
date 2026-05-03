# start-docker.ps1
# Convenience script to start Docker Desktop and wait for it to be ready,
# then optionally build and run docker-compose
# Usage: .\start-docker.ps1
#        .\start-docker.ps1 -Up          (also runs docker-compose up -d)
#        .\start-docker.ps1 -Build       (also runs docker-compose build)

param(
    [switch]$Up,
    [switch]$Build
)

$ErrorActionPreference = "Stop"

Write-Host "`n╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║       Kuldeep Chatbot — Docker Desktop Startup Helper         ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════════╝`n" -ForegroundColor Cyan

# Check if Docker Desktop is installed
$dockerApp = "$env:ProgramFiles\Docker\Docker\Docker Desktop.exe"
if (-not (Test-Path $dockerApp)) {
    $dockerApp = "C:\Program Files\Docker\Docker\Docker Desktop.exe"
}

if (-not (Test-Path $dockerApp)) {
    Write-Host "❌ Docker Desktop not found at: $dockerApp" -ForegroundColor Red
    Write-Host "   Please install Docker Desktop from: https://www.docker.com/products/docker-desktop" -ForegroundColor Yellow
    exit 1
}

Write-Host "🐳 Starting Docker Desktop..." -ForegroundColor Blue
Start-Process $dockerApp

Write-Host "⏳ Waiting for Docker daemon to be ready (this may take 30-60 seconds)..." -ForegroundColor Yellow

$maxAttempts = 60
$attempt = 0
while ($attempt -lt $maxAttempts) {
    try {
        $result = docker ps 2>$null
        Write-Host "✅ Docker daemon is ready!" -ForegroundColor Green
        break
    }
    catch {
        $attempt++
        Write-Host "   Attempt $attempt/$maxAttempts..." -NoNewline
        Start-Sleep -Seconds 1
        Write-Host "`r" -NoNewline
    }
}

if ($attempt -eq $maxAttempts) {
    Write-Host "`n❌ Docker daemon failed to start after $maxAttempts seconds" -ForegroundColor Red
    Write-Host "   Try restarting Docker Desktop manually and checking the logs" -ForegroundColor Yellow
    exit 1
}

# Check if user is logged in
Write-Host "🔐 Checking Docker login..." -ForegroundColor Blue
$output = docker info 2>&1
if ($output -like "*not logged in*") {
    Write-Host "⚠️  You are not logged in to Docker Hub" -ForegroundColor Yellow
    docker login
}

Write-Host "`n✅ Docker is ready!`n" -ForegroundColor Green

if ($Build) {
    Write-Host "🔨 Building Docker images (this will take a few minutes)..." -ForegroundColor Blue
    docker-compose build
    Write-Host "✅ Build complete!`n" -ForegroundColor Green
}

if ($Up) {
    Write-Host "🚀 Starting containers..." -ForegroundColor Blue
    docker-compose up -d
    Write-Host "`n✅ Containers started!`n" -ForegroundColor Green
    Write-Host "📍 Access your app at:" -ForegroundColor Cyan
    Write-Host "   Frontend:  http://localhost:3000" -ForegroundColor Cyan
    Write-Host "   Backend:   http://localhost:5000" -ForegroundColor Cyan
    Write-Host "   Health:    http://localhost:5000/api/health`n" -ForegroundColor Cyan
}

Write-Host "💡 Quick commands:" -ForegroundColor Yellow
Write-Host "   View logs:    docker-compose logs -f" -ForegroundColor Gray
Write-Host "   Stop:         docker-compose stop" -ForegroundColor Gray
Write-Host "   Down:         docker-compose down" -ForegroundColor Gray
Write-Host "   Rebuild:      docker-compose up --build`n" -ForegroundColor Gray
