# NEW Architecture - Streaming Setup

## How It Works Now

**Mac/Jetson Side:**
- Webcam captures video
- Python server runs YOLOv8 detection
- Records when cat + human detected
- Streams live feed to network

**iPhone Side:**
- Just a viewer/monitor
- NO camera needed!
- Shows live stream from Mac/Jetson
- Browse and play recorded videos

---

## Quick Start

### Step 1: Start Streaming Server on Mac

```bash
cd /Users/tszchiung/Desktop/FYP-Codes/backend

# Stop old server if running
lsof -ti:5001 | xargs kill -9

# Start streaming server (ESP32 + webcam support)
python3 streaming_backend_server.py

# OR start webcam-only version
python3 streaming_backend_server_webcam.py
```

**You should see:**
```
✅ Model loaded successfully!
📹 Starting camera thread...
✅ Camera opened: 1280x720

Server URL: http://10.17.94.27:5001
Live Stream: http://10.17.94.27:5001/stream/live
```

### Step 2: Update iOS App in Xcode

**Files location in your Xcode project:**

1. **NetworkManager.swift** - Backend communication
   - Location: `iOS_App/PetGuard/PetGuard/NetworkManager.swift`
   - Update: `baseURL` on line 19

2. **ContentView.swift** - Main UI
   - Location: `iOS_App/PetGuard/PetGuard/ContentView.swift`
   - Uses StreamView for live feed

3. **StreamView.swift** - Live camera view
   - Location: `iOS_App/PetGuard/PetGuard/StreamView.swift`
   - Displays video stream from Mac/ESP32

4. **VideosView.swift** - Saved videos view
   - Location: `iOS_App/PetGuard/PetGuard/VideosView.swift`
   - No changes needed

5. **PetGuardApp.swift** - App entry point
   - Location: `iOS_App/PetGuard/PetGuard/PetGuardApp.swift`

### Step 3: Update Info.plist

**REMOVE camera permission** (not needed anymore!):
- Delete: `Privacy - Camera Usage Description`

**Keep only network permission:**
```xml
<key>NSAppTransportSecurity</key>
<dict>
    <key>NSAllowsArbitraryLoads</key>
    <true/>
</dict>
```

### Step 4: Run iOS App

1. Clean Build: **Shift+Cmd+K**
2. Build and Run: **Cmd+R**
3. In Settings, enter: `http://10.17.94.27:5001`
4. Test connection
5. Go to "Live Stream" tab
6. You should see your Mac's webcam feed!

---

## Testing

### Test 1: Server Webcam
On Mac, check if webcam is working:
```bash
# Test camera access
python3 -c "import cv2; cap = cv2.VideoCapture(0); print('Camera OK' if cap.isOpened() else 'Failed'); cap.release()"
```

### Test 2: Stream API
```bash
curl http://localhost:5001/stream/live | jq '.detections'
```

### Test 3: Live Detection
1. Position yourself in front of Mac webcam
2. Open iOS app → Live Stream tab
3. You should see yourself with "human" detection
4. Show a cat picture/video on another screen
5. When both visible → "RECORDING" appears!
6. Check "Recordings" tab for videos

---

## File Structure

```
ios_app/
├── streaming_backend_server.py  ⭐ ACTIVE - Mac/Jetson server with webcam
├── cleanup_videos.py            🧹 NEW - Manual video cleanup utility
├── STREAMING_SETUP.md           📖 This file
├── StreamView.swift             ⭐ NEW - iOS stream viewer
├── ContentView.swift            ✏️  UPDATED - Uses StreamView
├── NetworkManager.swift         ✏️  UPDATED - Added streaming
├── VideosView.swift             ✅ Video playback view
└── HandPetDetectorApp.swift     ✅ Main iOS app
```

---

## Demo Flow

1. **Start Server**: Mac/Jetson runs with webcam
2. **Open iOS App**: Connect to server
3. **View Stream**: See live feed with detections
4. **Trigger Recording**: Show cat + human to camera
5. **View Recordings**: Browse saved videos in app

---

## Configuration

### Change Camera (for Jetson)
In `backend/streaming_backend_server.py`, line 49:
```python
use_esp32_camera = False  # Set to False for Mac webcam
CAMERA_ID = 0  # Change to 1 or 2 for external camera
```

### Adjust Detection & Recording
```python
CONFIDENCE_THRESHOLD = 0.25  # Lower = more detections
COOLDOWN_SECONDS = 2         # Recording timeout
MAX_VIDEOS = 10              # Maximum stored videos (auto-cleanup)
```

### Storage Management

**Auto-Cleanup (Built-in):**
- Automatically keeps only 10 newest videos
- Runs after each recording stops
- Deletes oldest videos first
- No manual intervention needed

**Manual Cleanup (if needed):**
```bash
python3 ios_app/cleanup_videos.py
```

**Recorded videos location:**
```
recorded_videos/interaction_YYYYMMDD_HHMMSS.mp4
```

---

## Advantages of New Architecture

- No iPhone camera needed
- Better for Jetson Nano deployment
- iPhone is just a remote viewer
- Can add multiple viewer devices
- All processing on Mac/Jetson
- Auto-storage management (max 10 videos)
- Cleaner separation of concerns
- Easier to deploy and scale
- Network-based streaming architecture

---

## Ready to Test!

1. Start server: `python3 ios_app/streaming_backend_server.py`
2. Update Xcode project files
3. Run iOS app
4. See your Mac webcam feed on iPhone!

---

## ESP32-S3 Camera Streaming Setup

1. **Flash your ESP32-S3 with the provided `esp32s3_camera_stream.ino`**
   - Configure your WiFi SSID/password and backend server IP/port in the sketch.
   - The ESP32 will send JPEG frames to the backend at `/esp32/frame` (default 10 FPS).
   - You can preview the stream locally at `http://<esp32-ip>/stream` in a browser.

2. **Start the backend server on your Mac/Jetson**
   - By default, the backend uses the Mac webcam.
   - To switch to ESP32-S3 camera, send:
     ```bash
     curl -X POST http://<backend-ip>:5001/esp32/enable -H "Content-Type: application/json" -d '{"enable": true}'
     ```
   - To switch back to Mac webcam:
     ```bash
     curl -X POST http://<backend-ip>:5001/esp32/enable -H "Content-Type: application/json" -d '{"enable": false}'
     ```

3. **iOS App**
   - No changes needed; it will display whichever source the backend is using.

**Tip:**
- The backend will auto-detect and process whichever camera source is active.
- You can run both ESP32 and Mac webcam, and switch sources as needed for testing or deployment.

---
