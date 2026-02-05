# MiniContainer - Setup Guide

## 📋 System Requirements

| Requirement | Details |
|-------------|---------|
| **OS** | Linux (Ubuntu 20.04+) |
| **Kernel** | 5.4+ with cgroup v2 |
| **Root Access** | Required for containers |
| **Software** | GCC, Python 3.11+, Node.js 18+, busybox-static, ngrok |

---

## 🚀 Installation

```bash
# 1. Clone repository
git clone https://github.com/Siddhanthkjain2005/container.git
cd container

# 2. Install dependencies
sudo apt-get update && sudo apt-get install -y gcc make busybox-static

# 3. Build C runtime
cd runtime && make && cd ..

# 4. Setup the root filesystem (CRITICAL)
# This creates a minimal isolated environment for your containers
sudo bash scripts/restore.sh
sudo bash scripts/setup_rootfs.sh

# 5. Setup Python backend
cd backend
python3 -m venv venv
# Note: Use sudo with the direct path to the venv python for container operations
sudo ./venv/bin/python3 -m pip install -r requirements.txt
cd ..

# 6. Install dashboard dependencies
cd dashboard && npm install && cd ..
```

---

## 🖥️ Running the Backend
```bash
cd backend
sudo PYTHONPATH=. ./venv/bin/python3 -m kernelsight.api
```

## 📊 Running the Dashboard
```bash
cd dashboard
npm run dev
```

## ⌨️ Running the CLI
```bash
python3 controller.py
in root
```

## ☁️ Vercel Deployment

### Step 1: Configure ngrok Token

```bash
# Get token from https://dashboard.ngrok.com/get-started/your-authtoken
ngrok config add-authtoken YOUR_TOKEN
```

Token is saved to: `~/.config/ngrok/ngrok.yml`

### Step 2: Start Backend with ngrok

```bash
# Terminal 1 - Start backend
sudo PYTHONPATH=./backend ./backend/venv/bin/python3 -m minicontainer.cli dashboard

# Terminal 2 - Start ngrok tunnel
ngrok http 8000
```

Copy the ngrok URL (e.g., `https://abc123.ngrok-free.dev`)

### Step 3: Access the Dashboard
Access the dashboard via your browser. The frontend automatically detects the API and WebSocket URLs.

### Step 4: Deploy to Vercel

1. Push code to your GitHub
2. Go to [vercel.com](https://vercel.com) → **New Project**
3. Import your repository
4. Configure:
   - **Root Directory**: `dashboard`
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
   - **Environment Variables**:
     - `VITE_API_URL`: Your ngrok URL (e.g., `https://abc123.ngrok-free.dev`)
     - `VITE_WS_URL`: Your ngrok WebSocket URL (e.g., `wss://abc123.ngrok-free.dev/ws`)
5. Click **Deploy**

Your dashboard will be live at: `https://your-project.vercel.app`

---


