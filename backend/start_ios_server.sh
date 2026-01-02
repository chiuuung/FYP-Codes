#!/bin/bash
# Quick Start Script for iOS Streaming Backend Server

echo "=========================================="
echo "  iOS Streaming Backend - Quick Start"
echo "=========================================="
echo ""

# Change to parent directory (hand-pet-interaction-detector)
cd "$(dirname "$0")/.."

# Check if in correct directory
if [ ! -f "ios_app/streaming_backend_server.py" ]; then
    echo "❌ Error: streaming_backend_server.py not found"
    echo "Please run this script from the ios_app directory"
    exit 1
fi

# Check if model exists
if [ ! -f "runs/best_accuracy/yolov8s_massive/weights/best.pt" ]; then
    echo "❌ Error: Trained model not found"
    echo "Expected: runs/best_accuracy/yolov8s_massive/weights/best.pt"
    exit 1
fi

# Install requirements
echo "📦 Installing Python packages..."
pip3 install -r ios_app/requirements-ios.txt

if [ $? -ne 0 ]; then
    echo "❌ Failed to install requirements"
    exit 1
fi

echo "✅ Packages installed"
echo ""

# Get IP address
echo "🌐 Your Mac's IP address:"
ipconfig getifaddr en0
echo ""
echo "Use this IP in your iOS app settings!"
echo "Example: http://$(ipconfig getifaddr en0):5001"
echo ""
echo "⚠️  NOTE: Server runs on PORT 5001 (not 5000)"
echo ""

# Start server
echo "🚀 Starting streaming server..."
echo "Press Ctrl+C to stop"
echo ""
echo "📹 Features:"
echo "  - Auto-recording when cat+human detected"
echo "  - Storage management (max 10 videos)"
echo "  - Live streaming to iOS devices"
echo ""

python3 ios_app/streaming_backend_server.py
