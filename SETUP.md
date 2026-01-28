# MiniContainer - Setup Guide

> Complete guide for setting up and running MiniContainer from scratch.

---

## 📋 System Requirements

### Required Architecture
| Requirement | Details |
|-------------|---------|
| **OS** | Linux (Ubuntu 20.04+ recommended) |
| **Kernel** | 5.4+ with cgroup v2 support |
| **Architecture** | x86_64 or aarch64 |
| **Privileges** | Root/sudo access required |
| **Memory** | Minimum 2GB RAM |
| **Disk** | 1GB free space |

### Required Software
| Software | Version | Purpose |
|----------|---------|---------|
| GCC | 9+ | Compile C runtime |
| Python | 3.11+ | Backend server |
| Node.js | 18+ | Dashboard build |
| npm | 9+ | Package management |
| Git | 2.0+ | Clone repository |
| ngrok | Latest | External tunnel |

### Verify Cgroup v2
```bash
# Check if cgroup v2 is mounted
mount | grep cgroup2
# Should show: cgroup2 on /sys/fs/cgroup type cgroup2
```

---

## 🚀 Quick Start

### 1. Clone the Repository
```bash
git clone https://github.com/Siddhanthkjain2005/container.git
cd container
```

### 2. Build C Runtime
```bash
cd runtime
make clean && make
cd ..
```

### 3. Setup Python Backend
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cd ..
```

### 4. Install Dashboard Dependencies
```bash
cd dashboard
npm install
cd ..
```

### 5. Run Backend Server
```bash
sudo PYTHONPATH=./backend ./backend/venv/bin/python3 -m minicontainer.cli dashboard
```

### 6. Run Dashboard (separate terminal)
```bash
cd dashboard
npm run dev
```

Open http://localhost:5173 in your browser!

---

## 🌐 ngrok Setup (For External Access)

### Step 1: Install ngrok
```bash
# Download from https://ngrok.com/download or:
curl -s https://ngrok-agent.s3.amazonaws.com/ngrok.asc | sudo tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null
echo "deb https://ngrok-agent.s3.amazonaws.com buster main" | sudo tee /etc/apt/sources.list.d/ngrok.list
sudo apt update && sudo apt install ngrok
```

### Step 2: Get Your Auth Token
1. Create account at https://ngrok.com
2. Go to https://dashboard.ngrok.com/get-started/your-authtoken
3. Copy your authtoken

### Step 3: Configure ngrok
```bash
# Replace YOUR_TOKEN with your actual token
ngrok config add-authtoken YOUR_TOKEN
```

**Configuration file location**: `~/.config/ngrok/ngrok.yml`

### Step 4: Start ngrok Tunnel
```bash
# In a separate terminal, after starting the backend:
ngrok http 8000
```

### Step 5: Update Frontend URL
Edit `dashboard/src/App.jsx`:
```javascript
// Replace with your ngrok URL (line 4-5)
const API_URL = 'https://YOUR-NGROK-URL.ngrok-free.dev'
const WS_URL = 'wss://YOUR-NGROK-URL.ngrok-free.dev/ws'
```

---

## ☁️ Vercel Deployment (Frontend)

### Step 1: Push to Your GitHub
```bash
# Fork or push to your own GitHub repository
git remote set-url origin https://github.com/YOUR_USERNAME/container.git
git push -u origin main
```

### Step 2: Deploy to Vercel
1. Go to https://vercel.com and sign in with GitHub
2. Click **"New Project"**
3. Import your `container` repository
4. Configure build settings:
   - **Framework Preset**: Vite
   - **Root Directory**: `dashboard`
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
5. Click **"Deploy"**

### Step 3: Configure Environment
After deployment, your frontend will be at:
```
https://your-project-name.vercel.app
```

### Step 4: Connect to Backend
Before deploying, update `dashboard/src/App.jsx` with your ngrok URL:
```javascript
const API_URL = 'https://your-ngrok-url.ngrok-free.dev'
const WS_URL = 'wss://your-ngrok-url.ngrok-free.dev/ws'
```

Commit and push - Vercel will auto-redeploy!

---

## 🔧 Running Commands

### Start Backend Only
```bash
sudo PYTHONPATH=./backend ./backend/venv/bin/python3 -m minicontainer.cli dashboard
```

### Start with ngrok (Full External Access)
```bash
# Terminal 1: Backend
sudo PYTHONPATH=./backend ./backend/venv/bin/python3 -m minicontainer.cli dashboard

# Terminal 2: ngrok
ngrok http 8000

# Terminal 3: Frontend (optional for local dev)
cd dashboard && npm run dev
```

### CLI Commands
```bash
# List containers
sudo ./runtime/build/minicontainer-runtime list

# Create container
sudo ./runtime/build/minicontainer-runtime create --name mycontainer

# Start container
sudo ./runtime/build/minicontainer-runtime start <container_id>

# Execute command in container
sudo ./runtime/build/minicontainer-runtime exec <container_id> --cmd "echo hello"

# Stop container
sudo ./runtime/build/minicontainer-runtime stop <container_id>

# Delete container
sudo ./runtime/build/minicontainer-runtime delete <container_id>
```

---

## 🛠️ Troubleshooting

### Port 8000 Already in Use
```bash
sudo fuser -k 8000/tcp
```

### Permission Denied
Always run backend with `sudo`:
```bash
sudo PYTHONPATH=./backend ./backend/venv/bin/python3 -m minicontainer.cli dashboard
```

### ngrok Connection Refused
1. Verify backend is running: `curl http://localhost:8000/api/containers`
2. Check ngrok is tunneling port 8000

### Cgroup Not Found
```bash
# Create cgroup directory
sudo mkdir -p /sys/fs/cgroup/minicontainer
sudo chown -R $USER:$USER /var/lib/minicontainer
```

### Missing Python Modules
```bash
cd backend
source venv/bin/activate
pip install -r requirements.txt
```

---

## 📁 Important Files Reference

| File | Purpose |
|------|---------|
| `dashboard/src/App.jsx` (lines 4-5) | API and WebSocket URLs |
| `~/.config/ngrok/ngrok.yml` | ngrok auth token |
| `backend/requirements.txt` | Python dependencies |
| `dashboard/package.json` | Node.js dependencies |
| `runtime/Makefile` | C build configuration |

---

## ✅ Verification Checklist

- [ ] C runtime builds without errors
- [ ] Python venv created and packages installed
- [ ] Backend starts on port 8000
- [ ] Dashboard accessible at localhost:5173
- [ ] ngrok tunnel created (if needed)
- [ ] Vercel deployment successful (if needed)
- [ ] Can create/start/stop containers from dashboard

---

## 📞 Support

If you encounter issues:
1. Check the [Troubleshooting](#️-troubleshooting) section
2. Verify all system requirements are met
3. Ensure you're running commands with `sudo`
4. Check backend logs: `tail -f backend.log`
