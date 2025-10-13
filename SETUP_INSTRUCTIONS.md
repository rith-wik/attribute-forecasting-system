# AFS Setup Instructions - Step by Step

## Current Situation

Your WSL environment needs these packages installed:
- `python3-venv` (for virtual environments)
- `python3-pip` (for package management)

Since I cannot run `sudo` commands without a password, you'll need to run these steps manually.

## Quick Setup (5 minutes)

### Step 1: Install Required Packages in WSL

Open your WSL terminal and run:

```bash
sudo apt update
sudo apt install -y python3-venv python3-pip build-essential
```

This will prompt for your password. Enter it and wait for installation to complete.

### Step 2: Verify Installation

```bash
python3 --version      # Should show: Python 3.12.3
pip3 --version         # Should show: pip X.X.X
```

### Step 3: Set Up Backend

```bash
cd /mnt/c/Dev/AttributeForecastingSystem/backend

# Create virtual environment
python3 -m venv .venv

# Activate it
source .venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install fastapi uvicorn[standard] pydantic pydantic-settings \
    pandas numpy scikit-learn xgboost python-multipart pytest
```

### Step 4: Run Backend

```bash
cd /mnt/c/Dev/AttributeForecastingSystem/backend
source .venv/bin/activate
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**Expected output**:
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

### Step 5: Test Backend (New Terminal)

Open a new WSL terminal:

```bash
# Health check
curl http://localhost:8000/health
# Expected: {"status":"ok"}

# API docs
curl http://localhost:8000/docs
# Should return HTML

# Get trends
curl http://localhost:8000/api/v1/trends
# Should return JSON array
```

### Step 6: Set Up Frontend (Optional)

Open another WSL terminal:

```bash
cd /mnt/c/Dev/AttributeForecastingSystem/frontend

# Install Node.js if not installed
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs

# Verify installation
node --version   # Should be v20.x
npm --version    # Should be 10.x

# Install dependencies
npm install

# Run frontend
npm run dev
```

**Expected output**:
```
  VITE v5.x.x  ready in XXX ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
```

### Step 7: Access the Application

Open your browser:
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## Alternative: Docker Setup (Recommended)

If the above seems complex, install Docker Desktop instead:

### Docker Desktop Installation

1. **Download Docker Desktop for Windows**:
   - URL: https://docs.docker.com/desktop/install/windows-install/
   - Version: Latest stable release

2. **Install**:
   - Double-click the installer
   - Enable "Use WSL 2 instead of Hyper-V" option
   - Restart computer when prompted

3. **Configure WSL Integration**:
   - Open Docker Desktop
   - Go to Settings → Resources → WSL Integration
   - Enable integration with your WSL distribution
   - Click "Apply & Restart"

4. **Verify Docker Installation**:
   ```bash
   # In WSL terminal
   docker --version
   docker compose version
   ```

5. **Run the Application**:
   ```bash
   cd /mnt/c/Dev/AttributeForecastingSystem

   # Build images (first time only, takes 3-5 minutes)
   docker compose build

   # Start services
   docker compose up -d

   # Check status
   docker compose ps

   # View logs
   docker compose logs -f
   ```

6. **Access Application**:
   - Frontend: http://localhost:5173
   - Backend: http://localhost:8000
   - API Docs: http://localhost:8000/docs

7. **Useful Docker Commands**:
   ```bash
   # Stop services
   docker compose down

   # Restart services
   docker compose restart

   # View API logs
   docker compose logs -f api

   # View frontend logs
   docker compose logs -f web

   # Run tests
   docker compose exec api pytest tests/ -v

   # Train model
   curl -X POST http://localhost:8000/api/v1/train \
     -H "Content-Type: application/json" \
     -d '{"force_retrain": true}'
   ```

## Quick Test Script

After setting up (either method), save this as `test_system.sh`:

```bash
#!/bin/bash

echo "Testing AFS System..."
echo ""

# Test 1: Health check
echo "1. Health Check:"
curl -s http://localhost:8000/health
echo ""
echo ""

# Test 2: Get trends
echo "2. Get Trends:"
curl -s http://localhost:8000/api/v1/trends | head -c 200
echo "..."
echo ""
echo ""

# Test 3: Simple prediction
echo "3. Run Prediction:"
curl -s -X POST http://localhost:8000/api/v1/predict \
  -H "Content-Type: application/json" \
  -d '{
    "horizon_days": 7,
    "level": "attribute",
    "store_ids": ["DXB01"]
  }' | head -c 300
echo "..."
echo ""
echo ""

# Test 4: Train model
echo "4. Train Model:"
curl -s -X POST http://localhost:8000/api/v1/train \
  -H "Content-Type: application/json" \
  -d '{"force_retrain": true}' | head -c 200
echo "..."
echo ""
echo ""

echo "✅ All tests completed!"
```

Run it:
```bash
chmod +x test_system.sh
./test_system.sh
```

## Troubleshooting

### "python3-venv: command not found"
→ You need to run: `sudo apt install python3-venv`

### "pip3: command not found"
→ You need to run: `sudo apt install python3-pip`

### "Port 8000 already in use"
```bash
# Find process using port
lsof -i :8000

# Kill it
kill -9 <PID>
```

### "Module not found" errors
```bash
# Ensure virtual environment is activated
source /mnt/c/Dev/AttributeForecastingSystem/backend/.venv/bin/activate

# Reinstall packages
pip install fastapi uvicorn[standard] pydantic pydantic-settings \
    pandas numpy scikit-learn xgboost python-multipart pytest
```

### Docker installation issues
- Ensure WSL 2 is installed: `wsl --update`
- Ensure virtualization is enabled in BIOS
- Restart Docker Desktop after installation

## What I Recommend

**For quick testing**: Install packages in WSL (Steps 1-5)

**For production-like setup**: Install Docker Desktop

**Time investment**:
- WSL setup: 10 minutes
- Docker setup: 15 minutes (but easier to maintain)

## Next Steps After Setup

Once the system is running:

1. **Open the dashboard**: http://localhost:5173
2. **Explore the API**: http://localhost:8000/docs
3. **Run tests**:
   ```bash
   # WSL
   cd backend && pytest tests/ -v

   # Docker
   docker compose exec api pytest tests/ -v
   ```
4. **Train the model**:
   ```bash
   curl -X POST http://localhost:8000/api/v1/train \
     -H "Content-Type: application/json" \
     -d '{"force_retrain": true}'
   ```
5. **Try what-if scenarios**: Use the dashboard or API

## Need Help?

If you encounter issues:
1. Check the error message carefully
2. Refer to RUN_LOCAL.md for detailed troubleshooting
3. Check logs: `docker compose logs -f` or check terminal output
4. Verify all prerequisites are installed

---

**Start here**: Run `sudo apt install python3-venv python3-pip` in your WSL terminal, then follow Steps 2-5 above.
