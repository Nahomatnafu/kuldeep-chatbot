# Docker Setup Guide for Kuldeep Chatbot

## Prerequisites

✅ You've already:
- Created a Docker account (`nahomdocker`)
- Installed Docker Desktop for Windows

## Step 1: Start Docker Desktop

1. **Open Docker Desktop** from your Start menu or taskbar
2. Wait for the Docker icon to show it's running (you'll see it in the system tray)
   - Look for a Docker whale icon in the bottom-right corner
   - When it's ready, it will show a checkmark or "Docker Desktop is running"
3. You may see a login prompt — use your credentials:
   - **Username**: `nahomdocker`
   - **Password**: your Docker Hub password

**This may take 30-60 seconds on first start.**

## Step 2: Verify Docker is running

Open PowerShell and run:

```powershell
docker ps
```

You should see an empty list of containers (no error). If you see `ERROR`, Docker isn't running yet — wait a moment and try again.

## Step 3: Build and run your project

Once Docker is running, you can build and start the containers:

```powershell
cd c:\Users\15073\Documents\GitHub\kuldeep-chatbot

# Build images (first time: ~3-5 min depending on internet speed)
docker-compose build

# Start containers in the background
docker-compose up -d

# View logs
docker-compose logs -f

# Stop everything when done
docker-compose down
```

## Step 4: Access your application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:5000
- **Health check**: http://localhost:5000/api/health

## Useful Docker commands

```powershell
# View running containers
docker-compose ps

# View logs for a service
docker-compose logs backend
docker-compose logs frontend

# View logs in real-time
docker-compose logs -f

# Stop all containers (don't delete them)
docker-compose stop

# Start stopped containers
docker-compose start

# Delete everything (images, containers, volumes)
docker-compose down -v

# Rebuild after code changes
docker-compose up --build

# Run a command inside a container
docker-compose exec backend python ingest.py
```

## Troubleshooting

### Docker Desktop won't start
- Check that **Windows Hyper-V** is enabled (Settings > Apps > Programs and Features > Turn Windows features on or off > ☑ Hyper-V)
- Restart your computer
- Reinstall Docker Desktop if all else fails

### Port 3000 or 5000 already in use
```powershell
# Find process using port 5000
Get-NetTCPConnection -LocalPort 5000 | Select OwningProcess

# Kill it (replace PID with the actual process ID)
Stop-Process -Id <PID> -Force
```

Or use the script:
```powershell
.\stop-dev.ps1 -PortsOnly
```

### Containers exit immediately
Check logs:
```powershell
docker-compose logs
```

Common causes:
- Missing `OPENAI_API_KEY` in `.env` or `backend/.env`
- Port already in use
- Insufficient disk space

### Still having issues?
1. Run `docker-compose logs` to see what's failing
2. Verify your `.env` has `OPENAI_API_KEY=sk-...`
3. Try rebuilding: `docker-compose build --no-cache`

## Next steps

Once Docker is running, you can:
1. Push images to Docker Hub: `docker push nahomdocker/kuldeep-chatbot-backend:latest`
2. Deploy to cloud (AWS, GCP, Azure, DigitalOcean, etc.)
3. Run multiple instances with orchestration (Kubernetes, Docker Swarm)

