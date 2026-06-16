#!/usr/bin/env bash
set -euo pipefail

echo "==> Building frontend..."
cd frontend
npm ci
npm run build
cd ..

echo "==> Copying static files to backend/static..."
rm -rf backend/static
mkdir -p backend/static
cp -r frontend/dist/* backend/static/

echo "==> Installing Python dependencies..."
pip install -r backend/requirements.txt

echo "==> Build complete."
