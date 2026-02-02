#!/bin/bash
# MiniContainer - Automated Setup Script
set -e

echo "🐳 Starting MiniContainer Setup..."

# 1. Install System Dependencies
echo "📦 Installing system dependencies..."
sudo apt-get update
sudo apt-get install -y gcc make busybox-static python3-venv nodejs npm curl

# 2. Build C Runtime
echo "🔨 Building C runtime..."
cd runtime
make clean && make
cd ..

# 3. Setup RootFS
echo "📂 Setting up root filesystem..."
sudo bash scripts/setup_rootfs.sh

# 4. Setup Python Backend
echo "🐍 Setting up Python backend..."
cd backend
python3 -m venv venv
sudo ./venv/bin/python3 -m pip install -r requirements.txt
cd ..

# 5. Setup Dashboard
echo "🎨 Setting up dashboard..."
cd dashboard
npm install
cd ..

echo ""
echo "✨ Setup Complete!"
echo "--------------------------------------------------"
echo "To start the project:"
echo "1. Start Backend: cd backend && sudo PYTHONPATH=. ./venv/bin/python3 -m minicontainer.api"
echo "2. Start Dashboard: cd dashboard && npm run dev"
echo "3. Open browser: http://localhost:5173"
echo "--------------------------------------------------"
