# FYP - Human-Cat Interaction Detector

This is the **organized and ready-to-run** version of the project with all essential components clearly labeled.

---

## Project Structure

```
FYP-Codes/
├── README.md                    # You are here
├── AI_Model/                    # AI Model & Training
│   ├── weights/
│   │   └── best.pt             # Trained YOLOv8s model (77% mAP50)
│   ├── training_scripts/
│   │   ├── train_model.py      # Script to train new models
│   │   └── test_model.py       # Script to test model accuracy
│   ├── requirements.txt         # Python dependencies for AI
│   └── train result document/   # Training metrics and results
│
├── backend/                     # Backend Server
│   ├── streaming_backend_server.py         # Main server (ESP32 + webcam)
│   └── start_ios_server.sh                 # Quick start script
│
├── iOS_App/                     # iOS Application
│   └── PetGuard/                # Xcode project folder
│       ├── PetGuard/            # App source files
│       │   ├── StreamView.swift      # Live stream viewer
│       │   ├── ContentView.swift     # Main app view
│       │   ├── NetworkManager.swift  # API communication
│       │   ├── VideosView.swift      # Video playback
│       │   └── PetGuardApp.swift     # App entry point
│       └── PetGuard.xcodeproj/  # Xcode project
│
├── hardware_part/               # ESP32 Hardware
│   └── esp32_control/          # ESP32-S3 camera + BLE
│       ├── esp32s3_camera_stream.ino
│       ├── COMPLETE_SYSTEM_DOCUMENTATION.md
│       └── STREAM_OPTIMIZATION_GUIDE.md
│
├── Dataset/                     # Dataset Configuration
│   ├── dataset.yaml            # Original dataset config
│   └── expanded_data.yaml      # Expanded dataset config (2500+ images)
│
├── recorded_videos/             # Auto-recorded videos
│   └── interaction_*.mp4       # Saved interactions (max 10)
│
└── Documentation/               # Project Documentation
    ├── README.md               # Main project overview
    ├── PROJECT_ARCHITECTURE.md # System architecture
    ├── STREAMING_SETUP.md      # iOS app setup guide
    ├── TRAINING_DOCUMENTATION.md    # Complete training guide
    └── THEORETICAL_PRINCIPLES_AND_METHODS.md  # Academic documentation
```

---

## Quick Start Guide

### 1. Start the Backend Server (Mac/Jetson)

```bash
cd "/Users/tszchiung/Desktop/FYP-Codes/backend"

# Option A: Use the start script
./start_ios_server.sh

# Option B: Run directly (ESP32 + Mac webcam)
python3 streaming_backend_server.py

# Option C: Run webcam-only version
python3 streaming_backend_server_webcam.py
```

**What you should see:**
```
✅ Model loaded successfully!
📹 Starting camera thread...
✅ Camera opened: 1280x720

Server URL: http://YOUR_IP:5001
Live Stream: http://YOUR_IP:5001/stream/live
```

### 2. Stop the Server

```bash
# Press Ctrl+C in the terminal

# OR force kill:
lsof -ti:5001 | xargs kill -9
```

### 3. Run iOS App

1. Open Xcode
2. Create new iOS project (or use existing)
3. Copy all files from `iOS_App/xcode_project/` to your Xcode project
4. Update `Info.plist`:
   ```xml
   <key>NSAppTransportSecurity</key>
   <dict>
       <key>NSAllowsArbitraryLoads</key>
       <true/>
   </dict>
   ```
5. In app Settings, set server URL: `http://YOUR_MAC_IP:5001`
6. Run on iPhone/iPad

---

## Key Features

### Auto-Recording
- Automatically records when **cat AND human** detected together
- 2-second cooldown between recordings
- Videos saved as: `interaction_YYYYMMDD_HHMMSS.mp4`

### Auto-Storage Management
- Keeps only **10 newest videos** automatically
- Older videos deleted after each recording
- Manual cleanup: `python3 cleanup_videos.py`

### Live Streaming
- Real-time webcam feed to iOS devices
- Shows detection confidence levels
- Recording indicator when active

### iOS Viewer App
- **Live Stream** tab: Watch real-time feed
- **Recordings** tab: Browse and play saved videos
- No iPhone camera needed (viewer only)

---

## Model Performance

- **Model**: YOLOv8s
- **Dataset**: 2500+ annotated images
- **Overall mAP50**: 77.0%
- **Cat Detection**: 90.4% mAP50
- **Human Detection**: 63.7% mAP50
- **Model Size**: ~22 MB
- **Location**: `AI_Model/weights/best.pt`

---

## Configuration

### **Backend Server Settings**
Edit `backend/streaming_backend_server.py`:

```python
# Line 28-51 (Configuration section)
MODEL_PATH = PROJECT_ROOT / "AI_Model" / "weights" / "best.pt"
VIDEOS_DIR = PROJECT_ROOT / "recorded_videos"
use_esp32_camera = True                      # True for ESP32, False for Mac webcam
CONFIDENCE_THRESHOLD = 0.25                  # Detection sensitivity
COOLDOWN_SECONDS = 2                         # Recording timeout
CAMERA_ID = 0                                # Webcam ID (if not using ESP32)
MAX_VIDEOS = 10                              # Max stored videos
```

### **iOS App Settings**
In the app's Settings tab:
- **Server URL**: `http://YOUR_MAC_IP:5001`
- Test connection before viewing stream

---

## Documentation Files

| File | Purpose |
|------|---------|
| **Documentation/README.md** | Complete project overview |
| **Documentation/STREAMING_SETUP.md** | Detailed iOS app setup |
| **Documentation/TRAINING_DOCUMENTATION.md** | Model training guide |

---

## Requirements

### **For Backend (Mac/Jetson)**
```bash
cd AI_Model
pip3 install -r requirements.txt
```

**Key packages:**
- `ultralytics` (YOLOv8)
- `opencv-python` (Camera & video)
- `flask` (Web server)
- `torch` (Deep learning)

### **For iOS App**
- Xcode 14+
- iOS 15+ device/simulator
- Network connectivity to Mac/Jetson

---

## Workflow

```
1. Start Backend Server
   ↓
2. Mac/Jetson webcam captures video
   ↓
3. YOLOv8 detects humans & cats
   ↓
4. Auto-records when both detected
   ↓
5. Streams to iOS app
   ↓
6. View live feed & recordings on iPhone
```

---

## Troubleshooting

### **Server won't start**
```bash
# Check if port 5001 is in use
lsof -i :5001

# Kill existing process
lsof -ti:5001 | xargs kill -9
```

### **Model not found**
```bash
# Verify model exists
ls -lh AI_Model/weights/best.pt

# Update MODEL_PATH in streaming_backend_server.py
```

### **iOS app can't connect**
```bash
# Get your Mac's IP address
ipconfig getifaddr en0

# Update server URL in iOS app settings
# Example: http://10.17.94.27:5001
```

### **Camera not working**
```bash
# Test camera access
python3 -c "import cv2; cap = cv2.VideoCapture(0); print('OK' if cap.isOpened() else 'FAILED')"

# Try different camera ID (0, 1, or 2)
```

---

## Training New Models

See `Documentation/TRAINING_DOCUMENTATION.md` for details.

**Quick training:**
```bash
cd AI_Model/training_scripts

python3 train_model.py \
  --data "../../Dataset/expanded_data.yaml" \
  --epochs 50 \
  --batch-size 8 \
  --model yolov8s
```

---

## Project Status

- AI Model: Trained and tested (77% mAP50)
- Backend Server: Streaming + Auto-recording working
- iOS App: Live viewer + Video playback complete
- Storage: Auto-cleanup implemented
- Jetson Nano: Deployment pending

---

## Support

For detailed setup instructions, refer to:
- `Documentation/STREAMING_SETUP.md` - iOS app setup
- `Documentation/TRAINING_DOCUMENTATION.md` - Model training
- `Documentation/README.md` - Full project details

---

## Project Info

**Title**: Human-Cat Interaction Detector with iOS Monitoring  
**Technology**: YOLOv8, Python, Swift, Flask, OpenCV  
**Platform**: Mac/Jetson Nano (Backend) + iOS (Frontend)  
**Architecture**: Client-Server Streaming Model

---

**Ready to run! 🚀**
