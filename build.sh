#!/usr/bin/env bash
# build.sh — runs during Render's build phase
# Make executable: chmod +x build.sh

set -o errexit   # exit immediately if any command fails

echo "==> Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "==> Build complete!"
