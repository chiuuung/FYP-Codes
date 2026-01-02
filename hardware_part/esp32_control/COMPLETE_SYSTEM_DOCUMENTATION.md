# Hand-Pet Interaction Detection System - Complete Documentation

## System Overview

This system uses **ESP32-S3 camera** → **Mac backend (YOLOv8)** → **iOS app** architecture to detect and record interactions between humans and cats.

```
┌─────────────┐      HTTP POST        ┌──────────────┐      HTTP GET      ┌─────────────┐
│  ESP32-S3   │ ──────────────────► │ Mac Backend  │ ◄────────────────── │   iOS App   │
│  + OV5640   │   JPEG frames       │   + YOLOv8   │    JSON/MJPEG      │   (iPhone)  │
│   Camera    │   @15 FPS           │   Detection  │    Live Stream     │             │
└─────────────┘                      └──────────────┘                     └─────────────┘
```

**Flow:**
1. ESP32-S3 captures camera frames (640x480, 15 FPS)
2. Sends JPEG frames to Mac via HTTP POST
3. Mac runs YOLOv8 detection on each frame
4. iOS app fetches annotated frames with detection results
5. Auto-records video when both cat + human detected

---

## Component 1: ESP32-S3 Camera Module

### Hardware Specifications
- **Board**: ESP32-S3-N16R8
  - 16MB Flash
  - 8MB PSRAM (OPI PSRAM)
- **Camera**: OV5640 5MP
  - Connected via WROVER CAM port
  - Resolution: 640x480 (VGA)
  - Frame rate: 15 FPS
  - JPEG quality: 20 (optimized for speed)

### Pin Configuration (WROVER CAM Port)
```cpp
XCLK:  GPIO15    |  D7:   GPIO16
SIOD:  GPIO4     |  D6:   GPIO17
SIOC:  GPIO5     |  D5:   GPIO18
PCLK:  GPIO13    |  D4:   GPIO12
VSYNC: GPIO6     |  D3:   GPIO10
HREF:  GPIO7     |  D2:   GPIO8
                 |  D1:   GPIO9
                 |  D0:   GPIO11
```

### Network Configuration
- **WiFi**: Connects to iPhone hotspot
- **IP Address**: `172.20.10.2` (assigned by DHCP)
- **Sends to**: `http://172.20.10.3:5001/esp32/frame`
- **Local stream**: `http://172.20.10.2/stream` (MJPEG)

### Code Location
```
FYP/hardware_part/esp32_control/esp32s3_camera_stream/
└── esp32s3_camera_stream.ino
```

### Key Configuration Parameters
```cpp
const char* ssid = "Chiu😺";           // iPhone hotspot name
const char* password = "james5123";    // Hotspot password
const char* serverIP = "172.20.10.3";  // Mac backend IP
const int serverPort = 5001;

#define FRAME_SIZE FRAMESIZE_VGA       // 640x480
#define STREAM_FPS 15                  // 15 frames per second
```

### Arduino IDE Setup

**Step 1: Install ESP32 Board Support**
1. Open Arduino IDE
2. Go to: **Arduino IDE → Preferences** (or **File → Preferences** on Windows/Linux)
3. In "Additional Board Manager URLs", add:
   ```
   https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json
   ```
4. Click OK
5. Go to: **Tools → Board → Boards Manager**
6. Search for "esp32"
7. Install **"esp32 by Espressif Systems"** (version 2.0.11 or later)
8. Wait for installation to complete

**Step 2: Install Required Libraries**
1. Go to: **Tools → Manage Libraries**
2. Search and install:
   - **"ESP32" by Espressif** (if not auto-installed)
   - Libraries should be included with ESP32 board package

**Step 3: Board Configuration**
```
Tools Settings:
├── Board:              "ESP32S3 Dev Module"
├── Port:               /dev/cu.usbmodem11201 (Mac) or COM port (Windows)
├── USB CDC On Boot:    "Enabled" ⚠️ CRITICAL!
├── CPU Frequency:      "240MHz (WiFi)"
├── Core Debug Level:   "None"
├── USB DFU On Boot:    "Disabled"
├── Erase All Flash:    "Disabled"
├── Events Run On:      "Core 1"
├── Flash Mode:         "QIO 80MHz"
├── Flash Size:         "16MB (128Mb)" ⚠️ CRITICAL!
├── JTAG Adapter:       "Disabled"
├── Arduino Runs On:    "Core 1"
├── USB Firmware MSC:   "Disabled"
├── Partition Scheme:   "Huge APP (3MB No OTA/1MB SPIFFS)" ⚠️ CRITICAL!
├── PSRAM:              "OPI PSRAM" ⚠️ CRITICAL! (NOT "QSPI" or "Disabled")
├── Upload Mode:        "UART0 / Hardware CDC"
└── Upload Speed:       "921600"
```

### Upload Steps
1. Open `esp32s3_camera_stream.ino` in Arduino IDE
2. Update WiFi credentials (lines 19-20)
3. Update Mac IP address (line 24)
4. Select **all** board settings above (especially PSRAM, Flash Size, Partition Scheme)
5. Connect ESP32-S3 via USB-C cable
6. Select correct Port in Tools menu
7. Press and hold **BOOT** button on ESP32
8. Click **Upload** button in Arduino IDE
9. Release BOOT button when "Connecting..." appears
10. Wait for upload to complete (~15 seconds)
11. Open **Serial Monitor** (button in top-right corner)
12. Set baud rate to **115200**
13. Press **RESET** button on ESP32
14. Verify camera initialization and WiFi connection

### Expected Serial Output
```
✅ PSRAM: 8388608 bytes
✅ Camera initialized successfully!
📐 Resolution: 640x480
📡 Connecting to WiFi: Chiu😺
✅ WiFi Connected!
📍 ESP32-S3 IP: 172.20.10.2
🖥️  Mac Backend: http://172.20.10.3:5001
✅ Streaming server started!
📺 Local Stream: http://172.20.10.2/stream
🔄 Sending frames to Mac backend every 67ms
✅ HTTP POST success (200)
```

### Troubleshooting
| Issue | Solution |
|-------|----------|
| PSRAM not found | Set Tools → PSRAM → **OPI PSRAM** (not OSPI!) |
| Camera not detected | Check camera cable connection, try pressing RESET |
| WiFi connection failed | Verify SSID/password, ensure 2.4GHz network |
| HTTP POST failed | Check Mac IP address, ensure backend is running |
| Upload failed | Press BOOT button while clicking Upload |

---

## Component 2: Mac Backend Server (YOLOv8)

### System Requirements
- **OS**: macOS (tested on macOS Ventura+)
- **Python**: 3.9+
- **RAM**: 8GB minimum, 16GB recommended
- **Network**: Connected to same iPhone hotspot as ESP32

### Network Configuration
- **IP Address**: `172.20.10.3` (on iPhone hotspot)
- **Port**: 5001
- **Receives from**: ESP32 at `http://172.20.10.3:5001/esp32/frame`
- **Serves to**: iOS app on `172.20.10.1`

### Code Location
```
FYP/hand-pet-interaction-detector/ios_app/
└── streaming_backend_server.py
```

### Dependencies
```bash
Flask==3.0.0
flask-cors==4.0.0
opencv-python==4.8.1
numpy==1.24.3
ultralytics==8.0.196
```

### Installation Steps
```bash
# Navigate to directory
cd /Users/tszchiung/Desktop/FYP.ZIP/FYP/hand-pet-interaction-detector/ios_app

# Install dependencies
pip3 install flask flask-cors opencv-python numpy ultralytics

# Or use requirements.txt if available
pip3 install -r requirements.txt
```

### Configuration
Key settings in `streaming_backend_server.py`:

```python
# Line 33: Enable ESP32 camera mode
use_esp32_camera = True  # Set to True for ESP32, False for Mac webcam

# Line 46-49: Detection parameters
CONFIDENCE_THRESHOLD = 0.25  # Detection confidence (0.0-1.0)
COOLDOWN_SECONDS = 2         # Recording timeout
CAMERA_ID = 0                # Webcam ID (unused in ESP32 mode)
MAX_VIDEOS = 10              # Keep 10 newest recordings
```

### Model Configuration
```python
MODEL_PATH = SCRIPT_DIR / "runs/best_accuracy/yolov8s_massive/weights/best.pt"
```

**Model Details:**
- Architecture: YOLOv8s
- Classes: 2 (human, cat)
- mAP50: 77% (cat: 90.4%, human: 63.7%)
- Training: 150 epochs, 75 hours on CPU
- Input: 640x640 images
- Inference: ~50-100ms per frame on Mac

### Starting the Server
```bash
cd /Users/tszchiung/Desktop/FYP.ZIP/FYP/hand-pet-interaction-detector/ios_app
python3 streaming_backend_server.py
```

### Expected Output
```
======================================================================
  Streaming Backend Server - Hand-Pet Interaction Detector
======================================================================
⏳ Loading model: .../best.pt
✅ Model loaded successfully!
📹 Starting camera thread...
📡 Using ESP32-S3 camera stream
🔄 Waiting for ESP32-S3 frames...

📱 iOS App Configuration:
   Server URL: http://172.20.10.3:5001
   Live Stream: http://172.20.10.3:5001/stream/live
   MJPEG Stream: http://172.20.10.3:5001/stream/mjpeg

📂 Videos saved to: .../recorded_videos
🎯 Confidence threshold: 0.25
⏱️  Recording cooldown: 2 seconds

🚀 Starting server...
======================================================================

 * Running on http://172.20.10.3:5001

📷 ESP32 frame added to queue: (480, 640, 3), queue size: 1
172.20.10.2 - - [Date] "POST /esp32/frame HTTP/1.1" 200 -
```

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Server health check |
| `/esp32/frame` | POST | Receive JPEG frame from ESP32 |
| `/esp32/enable` | POST | Enable/disable ESP32 mode |
| `/stream/live` | GET | Get single annotated frame (JSON) |
| `/stream/mjpeg` | GET | Continuous MJPEG video stream |
| `/status` | GET | Detection and recording status |
| `/videos` | GET | List recorded videos |
| `/videos/<filename>` | GET | Download specific video |
| `/videos/<filename>` | DELETE | Delete specific video |

### Response Formats

**`/stream/live` Response:**
```json
{
  "frame": "base64_encoded_jpeg",
  "detections": [
    {
      "class": "human",
      "confidence": 0.87,
      "bbox": [x1, y1, x2, y2]
    }
  ],
  "is_recording": true,
  "current_video": "interaction_20251211_230145.mp4",
  "timestamp": "2025-12-11T23:01:45.123456"
}
```

**`/videos` Response:**
```json
{
  "videos": [
    {
      "filename": "interaction_20251211_230145.mp4",
      "size": 12345678,
      "created": "2025-12-11T23:01:45",
      "url": "/videos/interaction_20251211_230145.mp4"
    }
  ],
  "count": 1
}
```

### Auto-Recording Logic
1. Detects when **both** cat and human present
2. Starts recording with 30 FPS MP4
3. Continues recording while both detected
4. Stops after 2 seconds of no dual detection
5. Saves to `recorded_videos/` directory
6. Keeps only 10 newest videos (auto-deletes old)

### Performance Metrics
- **Frame reception**: ~15 FPS from ESP32
- **YOLOv8 inference**: 50-100ms per frame
- **Total latency**: ~200-500ms (ESP32 → Mac → iOS)
- **Recording format**: MP4 (H.264), 30 FPS, original resolution

### Troubleshooting
| Issue | Solution |
|-------|----------|
| Model not found | Check MODEL_PATH, ensure best.pt exists |
| No frames from ESP32 | Verify ESP32 IP is correct, check firewall |
| Port 5001 in use | Kill existing process: `lsof -ti:5001 \| xargs kill` |
| Webcam instead of ESP32 | Set `use_esp32_camera = True` on line 33 |
| High CPU usage | YOLOv8s is CPU-intensive, consider GPU acceleration |

---

## Component 3: iOS App

### System Requirements
- **iOS**: 15.0+
- **Device**: iPhone (tested on iPhone with hotspot capability)
- **Network**: Must be the device providing the hotspot

### Network Configuration
- **IP Address**: `172.20.10.1` (iPhone hotspot gateway)
- **Backend URL**: `http://172.20.10.3:5001`
- **Streams from**: Mac at `172.20.10.3:5001/stream/live`

### Code Location
```
FYP.ZIP/HandPetDetector/
├── HandPetDetector/
│   ├── NetworkManager.swift       # Backend communication
│   ├── ContentView.swift          # Main UI
│   ├── LiveStreamView.swift       # Live camera view
│   └── RecordingsView.swift       # Saved videos view
```

### Configuration
In `NetworkManager.swift` (line 19):
```swift
private(set) var baseURL = "http://172.20.10.3:5001"
```

**Update this to your Mac's IP address!**

### Key Features

**1. Live Stream View**
- Fetches annotated frames from backend
- Shows bounding boxes around detected objects
- Displays confidence scores
- Updates at ~5-10 FPS (polling-based)
- Shows recording indicator

**2. Recordings View**
- Lists all saved videos
- Shows file size, date created
- Tap to play video in-app
- Swipe to delete videos
- Auto-refreshes list

**3. Connection Status**
- Health check every 5 seconds
- Shows green indicator when connected
- Shows error message if backend unreachable

### NetworkManager Methods

```swift
// Check backend health
func checkHealth(completion: @escaping (Bool) -> Void)

// Fetch single annotated frame
func fetchLiveFrame(completion: @escaping (UIImage?) -> Void)

// Get list of recorded videos
func fetchVideos(completion: @escaping (Bool) -> Void)

// Download video file
func downloadVideo(filename: String, completion: @escaping (URL?) -> Void)

// Delete video
func deleteVideo(filename: String, completion: @escaping (Bool) -> Void)

// Get video URL
func getVideoURL(filename: String) -> URL?
```

### Building & Running

**Xcode Setup:**
1. Open `HandPetDetector.xcodeproj` in Xcode
2. Select your iPhone as target device
3. Update Team in Signing & Capabilities
4. Update baseURL in NetworkManager.swift
5. Build and Run (⌘R)

**Deployment:**
1. Connect iPhone via cable
2. Trust computer on iPhone
3. Enable Developer Mode (Settings → Privacy & Security)
4. Run from Xcode

### UI Flow
```
┌──────────────────┐
│   ContentView    │ (Tab view)
└────────┬─────────┘
         │
    ┌────┴────┐
    │         │
┌───▼──┐  ┌──▼────────┐
│ Live │  │ Recordings│
│Stream│  │   View    │
└──────┘  └───────────┘
```

### Live Stream Implementation
```swift
// Polling-based frame fetching
Timer.publish(every: 0.2, on: .main, in: .common)
    .autoconnect()
    .sink { _ in
        networkManager.fetchLiveFrame { image in
            self.currentFrame = image
        }
    }
```

**Why 0.2s (5 FPS)?**
- Reduces network overhead
- Sufficient for monitoring
- iPhone battery friendly
- Backend processes at 15 FPS

### Performance Optimization
- **Image caching**: Reuse previous frame if fetch fails
- **Timeout**: 2-second request timeout
- **Background fetch**: Disabled when app backgrounded
- **Compression**: JPEG 0.7 quality for uploads

### Troubleshooting
| Issue | Solution |
|-------|----------|
| Connection failed | Verify baseURL matches Mac IP, check hotspot |
| No stream available | Ensure backend running, ESP32 sending frames |
| Laggy stream | Normal over WiFi, expect 200-500ms latency |
| Videos won't play | Check video format (MP4/H.264), try re-downloading |
| Build failed | Update Team in signing, check iOS deployment target |

---

## Network Architecture

### Complete Network Map
```
┌─────────────────────────────────────────────────────┐
│          iPhone Hotspot: "Chiu😺"                   │
│               Gateway: 172.20.10.1                   │
└──────┬────────────────────┬────────────────────┬────┘
       │                    │                    │
       │                    │                    │
┌──────▼──────┐      ┌──────▼──────┐      ┌─────▼─────┐
│   iOS App   │      │ Mac Backend │      │  ESP32-S3 │
│ 172.20.10.1 │◄─────┤172.20.10.3  │◄─────┤172.20.10.2│
│ (Gateway)   │ GET  │  Port 5001  │ POST │   Camera  │
└─────────────┘      └─────────────┘      └───────────┘
```

### Data Flow
```
1. ESP32 captures frame
   ↓ (JPEG, ~20KB per frame)
2. POST /esp32/frame → Mac
   ↓ (OpenCV decode)
3. Mac runs YOLOv8
   ↓ (50-100ms inference)
4. Mac annotates frame
   ↓ (stores in memory)
5. iOS app polls GET /stream/live
   ↓ (JSON with base64 image)
6. iOS displays frame
   ↓ (every 0.2s)
```

### Bandwidth Requirements
- **ESP32 → Mac**: ~2.4 Mbps (15 FPS × 20KB)
- **Mac → iOS**: ~0.4 Mbps (5 FPS × 10KB base64)
- **Total**: ~3 Mbps

---

## Complete Setup Guide

### Step 1: Prepare Hardware
1. ✅ ESP32-S3-N16R8 board
2. ✅ OV5640 camera module connected via WROVER port
3. ✅ USB-C cable for programming
4. ✅ iPhone with hotspot capability
5. ✅ Mac computer

### Step 2: Network Setup
1. Enable iPhone Personal Hotspot
2. Note hotspot name and password
3. Connect Mac to iPhone hotspot
4. Get Mac IP: `ifconfig | grep "inet " | grep -v 127.0.0.1`
5. Note IP (should be `172.20.10.X`)

### Step 3: ESP32 Configuration
1. Open `esp32s3_camera_stream.ino` in Arduino IDE
2. Update WiFi credentials (lines 19-20)
3. Update Mac IP (line 24)
4. Set Arduino settings (see Component 1)
5. Upload code
6. Open Serial Monitor, verify connection

### Step 4: Mac Backend Setup
1. Install Python dependencies
2. Verify model path is correct
3. Set `use_esp32_camera = True` (line 33)
4. Start server: `python3 streaming_backend_server.py`
5. Verify "Waiting for ESP32-S3 frames..."
6. Check for "ESP32 frame added to queue" messages

### Step 5: iOS App Setup
1. Open project in Xcode
2. Update baseURL in NetworkManager.swift
3. Build and run on iPhone
4. Allow network permissions
5. Check connection status (green = connected)
6. Open Live Stream tab

### Step 6: Verification
✅ ESP32 Serial Monitor shows "HTTP POST success (200)"
✅ Mac backend shows "ESP32 frame added to queue"
✅ iOS app shows live camera feed
✅ Detections appear with bounding boxes
✅ Recording starts when cat + human detected
✅ Videos appear in Recordings tab

---

## Common Issues & Solutions

### Issue: Laggy/Frozen Stream

**Causes:**
1. Network congestion on iPhone hotspot
2. YOLOv8 inference too slow
3. iOS polling too fast
4. Frame queue backup

**Solutions:**
1. **Reduce ESP32 frame rate:**
   ```cpp
   #define STREAM_FPS 10  // Reduce from 15 to 10
   ```

2. **Increase JPEG compression:**
   ```cpp
   config.jpeg_quality = 25;  // Increase from 20 to 25
   ```

3. **Lower YOLOv8 resolution** (in backend):
   ```python
   # Before running detection, resize frame
   frame = cv2.resize(frame, (416, 416))  # Smaller input
   ```

4. **Reduce iOS polling rate:**
   ```swift
   Timer.publish(every: 0.3, on: .main, in: .common)  // 0.3 instead of 0.2
   ```

5. **Enable frame skipping** (in backend):
   ```python
   frame_skip = 2  # Process every 2nd frame
   if frame_count % frame_skip == 0:
       # Run detection
   ```

### Issue: Videos Not Recording

**Check:**
1. Backend shows "🔴 Recording STARTED"?
2. Both cat AND human detected simultaneously?
3. Confidence threshold too high?
4. Recordings directory writable?

**Solutions:**
- Lower confidence: `CONFIDENCE_THRESHOLD = 0.15`
- Check directory: `ls -la recorded_videos/`
- Verify both classes detected: Check backend logs

### Issue: High CPU Usage

**Solutions:**
1. Use YOLOv8n (nano) instead of YOLOv8s:
   ```python
   MODEL_PATH = "yolov8n.pt"  # Smaller model
   ```

2. Reduce frame rate (ESP32 and iOS)
3. Skip frames (process every Nth frame)
4. Close other applications

---

## Performance Benchmarks

### Tested Configuration
- **ESP32**: 15 FPS, 640x480, JPEG quality 20
- **Mac**: M1 MacBook Air, 8GB RAM
- **Network**: iPhone 13 Hotspot, 2.4GHz

### Measured Metrics
| Metric | Value |
|--------|-------|
| ESP32 frame capture | 67ms per frame |
| Network latency (ESP32→Mac) | 20-50ms |
| YOLOv8s inference | 80-120ms |
| Mac processing total | 100-150ms |
| Network latency (Mac→iOS) | 50-100ms |
| **Total end-to-end** | **250-400ms** |
| iOS display rate | 5 FPS (0.2s polling) |
| Actual perceived latency | ~0.5-1 second |

### Bottlenecks
1. **YOLOv8 inference**: 80-120ms (largest)
2. **Network latency**: 70-150ms total
3. **iOS polling**: 200ms interval

---

## Advanced Optimizations

### 1. Reduce Latency

**Option A: Use YOLOv8n (nano)**
```python
# Faster but less accurate
MODEL_PATH = "yolov8n.pt"
# Inference: ~30-50ms (vs 80-120ms)
```

**Option B: Reduce Input Resolution**
```python
# In run_esp32_mode(), before detection:
frame = cv2.resize(frame, (416, 416))  # vs 640x480
```

**Option C: Skip Frame Processing**
```python
frame_skip_counter = 0
if frame_skip_counter % 2 == 0:  # Process every 2nd frame
    results = model.predict(...)
frame_skip_counter += 1
```

### 2. Improve Stream Smoothness

**Option A: Increase ESP32 Frame Rate**
```cpp
#define STREAM_FPS 20  // vs 15 FPS
config.jpeg_quality = 25;  // Compensate with lower quality
```

**Option B: Use Adaptive Polling** (iOS)
```swift
// Poll faster when active, slower when idle
let pollInterval = isRecording ? 0.1 : 0.3
```

### 3. Reduce Bandwidth

**Option A: Lower Resolution**
```cpp
#define FRAME_SIZE FRAMESIZE_CIF  // 400x296 vs 640x480
```

**Option B: Dynamic Quality**
```cpp
// Adjust quality based on detection
int quality = both_detected ? 15 : 25;
```

---

## Additional Resources

### YOLOv8 Training Documentation
- `chiu/TRAINING_METHODOLOGY.md` - Training techniques explained
- `chiu/TRAINING_COMMANDS.md` - Complete training script

### Hardware Guides
- `hardware_part/esp32_control/COMPLETE_SETUP_GUIDE.md`
- `hardware_part/esp32_control/esp32s3_camera_test/` - Camera testing

### Model Information
- Location: `runs/best_accuracy/yolov8s_massive/weights/best.pt`
- Config: `runs/best_accuracy/yolov8s_massive/args.yaml`
- Results: `runs/best_accuracy/yolov8s_massive/results.csv`

---

## Future Improvements

### Short-term
1. Fix stream freezing issues (DONE)
2. Add BLE beacon distance monitoring
3. Implement video playback controls in iOS
4. Add detection confidence filtering in app

### Medium-term
1. ⬜ Use websockets for real-time streaming
2. ⬜ Add GPU acceleration for YOLOv8
3. ⬜ Implement local recording on iOS
4. ⬜ Add cloud storage for videos

### Long-term
1. ⬜ Deploy to Jetson Nano for better performance
2. ⬜ Add multi-camera support
3. ⬜ Implement behavior analysis
4. ⬜ Add push notifications

---

## 📝 Changelog

### 2025-12-11
- ✅ Fixed camera thread stopping after each frame
- ✅ Stream now always shows frames (not just when recording)
- ✅ Updated ESP32 to send to correct Mac IP
- ✅ Optimized JPEG quality and frame rate
- ✅ Created complete system documentation

### 2025-12-10
- ✅ Configured ESP32-S3 with PSRAM support
- ✅ Tested 4 camera pin configurations
- ✅ Found working WROVER CAM port pinout
- ✅ Set up Mac backend for ESP32 frames
- ✅ Connected iOS app to backend

---

## 👥 Credits

**Developer**: Tsz Chiung
**Project**: Final Year Project (FYP)
**Institution**: [Your University]
**Year**: 2025

**Technologies Used:**
- ESP32-S3 (Espressif)
- YOLOv8 (Ultralytics)
- OpenCV
- Flask
- Swift/SwiftUI

---

## 📄 License

[Add your license information here]

---

**Last Updated**: December 12, 2025
**Version**: 1.0.0
