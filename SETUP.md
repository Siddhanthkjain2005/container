# MiniContainer - Setup Guide

## 📋 System Requirements

| Requirement | Details |
|-------------|---------|
| **OS** | Linux (Ubuntu 20.04+) |
| **Kernel** | 5.4+ with cgroup v2 |
| **Root Access** | Required for containers |
| **Software** | GCC, Python 3.11+, Node.js 18+, ngrok |

---

## 🚀 Installation

```bash
# 1. Clone repository
git clone https://github.com/Siddhanthkjain2005/container.git
cd container

# 2. Build C runtime
cd runtime && make && cd ..

# 3. Setup Python backend
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cd ..

# 4. Install dashboard dependencies
cd dashboard && npm install && cd ..
```

---

## 🖥️ Running the CLI

```bash
# List containers
sudo ./runtime/build/minicontainer-runtime list

# Create container
sudo ./runtime/build/minicontainer-runtime create --name mycontainer

# Start container
sudo ./runtime/build/minicontainer-runtime start <container_id>

# Stop container
sudo ./runtime/build/minicontainer-runtime stop <container_id>

# Delete container
sudo ./runtime/build/minicontainer-runtime delete <container_id>

# Execute command in container
sudo ./runtime/build/minicontainer-runtime exec <container_id> --cmd "echo hello"
```

---

## ☁️ Vercel Deployment

### Step 1: Start Backend with ngrok

```bash
# Terminal 1 - Start backend
sudo PYTHONPATH=./backend ./backend/venv/bin/python3 -m minicontainer.cli dashboard

# Terminal 2 - Start ngrok tunnel
ngrok http 8000
```

Copy the ngrok URL (e.g., `https://abc123.ngrok-free.dev`)

### Step 2: Configure ngrok Token

```bash
# Get token from https://dashboard.ngrok.com/get-started/your-authtoken
ngrok config add-authtoken YOUR_TOKEN
```

Token is saved to: `~/.config/ngrok/ngrok.yml`

### Step 3: Update Frontend URL

Edit `dashboard/src/App.jsx` (lines 4-5):
```javascript
const API_URL = 'https://YOUR-NGROK-URL.ngrok-free.dev'
const WS_URL = 'wss://YOUR-NGROK-URL.ngrok-free.dev/ws'
```

### Step 4: Deploy to Vercel

1. Push code to your GitHub
2. Go to [vercel.com](https://vercel.com) → **New Project**
3. Import your repository
4. Configure:
   - **Root Directory**: `dashboard`
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
5. Click **Deploy**

Your dashboard will be live at: `https://your-project.vercel.app`

---

## ✅ Quick Reference

| Command | Description |
|---------|-------------|
| `sudo ./runtime/build/minicontainer-runtime list` | List all containers |
| `sudo ./runtime/build/minicontainer-runtime create --name NAME` | Create container |
| `sudo ./runtime/build/minicontainer-runtime start ID` | Start container |
| `sudo ./runtime/build/minicontainer-runtime stop ID` | Stop container |
| `sudo ./runtime/build/minicontainer-runtime delete ID` | Delete container |
| `sudo PYTHONPATH=./backend ./backend/venv/bin/python3 -m minicontainer.cli dashboard` | Start backend |
| `ngrok http 8000` | Start tunnel |
