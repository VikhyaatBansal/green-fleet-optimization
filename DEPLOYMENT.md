# Complete Deployment Guide — GreenFleet Quanta (SIH 26138)

This guide provides exact, step-by-step deployment instructions for the Green Fleet Optimization prototype across different environments:
1. **Docker & Docker Compose** (Recommended for local, Cloud VM, or Hackathon staging)
2. **Free Cloud PaaS** (Vercel for Frontend + Render / Railway for FastAPI)
3. **Linux VPS / Virtual Machine** (Ubuntu with Systemd + Nginx + PM2)
4. **Local Windows / macOS / Linux Development Setup**

---

## Architecture & Ports
- **Backend**: FastAPI (Python 3.11) on port `8000`
- **Frontend**: Next.js 14 (TypeScript + Tailwind) on port `3000`
- **Communication**: Frontend calls `NEXT_PUBLIC_API_URL` (defaults to `http://localhost:8000` or custom domain).

---

## Method 1: Containerized Deployment via Docker & Docker Compose (Recommended)

### Prerequisites
- [Docker Engine & Docker Compose](https://docs.docker.com/get-docker/) installed.

### Step-by-Step
1. **Clone or Navigate to the project root**:
   ```bash
   cd green-fleet-optimization
   ```

2. **Build and start both containers in detached mode**:
   ```bash
   docker compose up --build -d
   ```

3. **Verify running containers**:
   ```bash
   docker compose ps
   ```

4. **Access the application**:
   - Web Dashboard: `http://localhost:3000`
   - FastAPI Interactive Swagger Docs: `http://localhost:8000/docs`

5. **Stopping the containers**:
   ```bash
   docker compose down
   ```

---

## Method 2: Free Cloud PaaS (Vercel + Render / Railway)

Ideal for presenting a live public URL to judges without managing a server.

### Part A: Deploy FastAPI Backend on Render.com or Railway.app
1. Push your repository to GitHub.
2. In **Render.com** (or **Railway.app**):
   - Click **New Web Service** -> Select your GitHub repository.
   - **Root Directory**: `.` (or project root).
   - **Runtime**: Python 3.
   - **Build Command**:
     ```bash
     pip install -r requirements.txt && python backend/prediction.py
     ```
   - **Start Command**:
     ```bash
     uvicorn backend.main:app --host 0.0.0.0 --port $PORT
     ```
   - Click **Create Web Service**.
   - Copy your public backend URL (e.g., `https://greenfleet-api.onrender.com`).

### Part B: Deploy Next.js Frontend on Vercel
1. Go to [Vercel](https://vercel.com) and click **Add New Project**.
2. Select your repository and set the **Root Directory** to `frontend`.
3. Under **Environment Variables**, add:
   - `NEXT_PUBLIC_API_URL` = `https://greenfleet-api.onrender.com` (your backend URL from Part A).
4. Click **Deploy**.
5. Your public dashboard will be live at `https://your-project.vercel.app`.

---

## Method 3: Ubuntu / Linux VPS Deployment (Production Standard)

For deploying on an AWS EC2, DigitalOcean Droplet, GCP Compute Engine, or Azure VM.

### 1. System Packages & Environment
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3-pip python3-venv nodejs npm nginx git

# Install Node LTS if needed
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs
```

### 2. Setup Backend Systemd Service
Create a virtual environment and install dependencies:
```bash
cd /opt/green-fleet-optimization
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
python backend/prediction.py
```

Create `/etc/systemd/system/greenfleet-backend.service`:
```ini
[Unit]
Description=GreenFleet Quanta FastAPI Backend
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/opt/green-fleet-optimization
Environment="PATH=/opt/green-fleet-optimization/venv/bin"
ExecStart=/opt/green-fleet-optimization/venv/bin/uvicorn backend.main:app --host 127.0.0.1 --port 8000 --workers 2
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable greenfleet-backend
sudo systemctl start greenfleet-backend
sudo systemctl status greenfleet-backend
```

### 3. Setup Next.js Frontend with PM2
```bash
cd /opt/green-fleet-optimization/frontend
npm install
NEXT_PUBLIC_API_URL=http://your-server-ip:8000 npm run build

# Install PM2 process manager
sudo npm install -g pm2
pm2 start npm --name "greenfleet-frontend" -- start -- -p 3000
pm2 save
pm2 startup
```

### 4. Configure Nginx Reverse Proxy
Edit `/etc/nginx/sites-available/default`:
```nginx
server {
    listen 80;
    server_name your-domain-or-ip;

    # Frontend
    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    # Backend API endpoints
    location ~ ^/(predict|optimize|scenario|benchmark|vessels|fuels|routes|metrics|docs|openapi.json) {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```
Test and reload Nginx:
```bash
sudo nginx -t
sudo systemctl restart nginx
```

---

## Method 4: Local Development & Pitch Mode

### Terminal 1 — Backend:
```bash
cd green-fleet-optimization
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```

### Terminal 2 — Frontend:
```bash
cd green-fleet-optimization/frontend
npm run dev
```
Open `http://localhost:3000`.
