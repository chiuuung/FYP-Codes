# Project Architecture Flow

## System Overview

**Human-Cat Interaction Detector with BLE Positioning & Remote Motor Control**

A comprehensive system that combines AI-based detection, real-time video streaming, indoor positioning using BLE beacons, and remote motor control through an iOS application.

---

## Main System Components

### 1. **Hardware Layer** (3 Main Parts)

#### A. ESP32-S3 + OV5640 Camera (Vision & Positioning Module)
- **Purpose**: Video capture and BLE distance monitoring
- **Components**:
  - ESP32-S3 microcontroller
  - OV5640 camera module
  - BLE scanner functionality
- **Functions**:
  1. Captures real-time video stream
  2. Sends camera frames to Mac backend server
  3. Scans BLE beacon signals (RSSI)
  4. Calculates distance to BLE beacon(s)
  5. Sends distance data to Mac backend server

#### B. ESP32-CAM (Motor Control Module)
- **Purpose**: Remote servo motor control
- **Components**:
  - ESP32-CAM board
  - Servo motor (connected via GPIO)
- **Functions**:
  1. Receives motor control commands from Mac backend
  2. Executes servo movements based on instructions
  3. Responds to button presses from iOS app

#### C. BLE Beacon(s)
- **Purpose**: Indoor positioning and proximity detection
- **Components**:
  - BLE beacon transmitter(s)
  - Currently: 1 beacon for testing
  - Future: 2+ beacons for multi-point positioning
- **Functions**:
  1. Broadcasts BLE signal continuously
  2. Provides RSSI (signal strength) for distance calculation
  3. Enables proximity alerts

---

### 2. **Backend Server** (Mac/Jetson Computer)

- **Technology**: Python Flask Server (Port 5001)
- **Location**: `backend/streaming_backend_server.py`
- **AI Model**: YOLOv8s (trained for human & cat detection)
- **Functions**:
  1. **Video Processing**:
     - Receives real-time video frames from ESP32-S3
     - Runs YOLOv8 detection (human + cat)
     - Auto-records when both detected
     - Streams processed video to iOS app
  
  2. **BLE Distance Monitoring**:
     - Receives distance data from ESP32-S3
     - Compares distance with iOS app threshold settings
     - Triggers proximity alerts when threshold exceeded
     - Example: If distance < 1m (set in iOS), send "Too close!" alert
  
  3. **Motor Control Relay**:
     - Receives motor commands from iOS app
     - Forwards instructions to ESP32-CAM motor module
     - Manages command queue and execution
  
  4. **Video Storage**:
     - Stores recorded videos (max 10 files)
     - Auto-cleanup of old recordings
     - Serves videos to iOS app

---

### 3. **iOS App** (iPhone/iPad)

- **Technology**: Swift/SwiftUI
- **App Name**: PetGuard
- **Location**: `iOS_App/PetGuard/`
- **Functions**:
  1. **Live Video Stream**:
     - Displays real-time camera feed with AI detections
     - Shows bounding boxes and confidence scores
  
  2. **Video Playback**:
     - Browse recorded interaction videos
     - Download/play recorded clips
  
  3. **Motor Control**:
     - Button interface for servo movements
     - Sends commands to backend → ESP32-CAM motor
  
  4. **BLE Distance Settings**:
     - Configure distance thresholds per beacon
     - Example: Set alert at 1m, 2m, etc.
     - Receive proximity alerts ("Too close!")
  
  5. **Server Configuration**:
     - Set backend server URL
     - Monitor connection status

---

## Complete System Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          SYSTEM ARCHITECTURE                            │
└─────────────────────────────────────────────────────────────────────────┘

┌──────────────────────┐
│   BLE BEACON(s)      │
│  (Hardware Part 2)   │
│                      │
│  • Broadcasts BLE    │
│  • RSSI Signal       │
│  • 1 beacon          │
└──────────┬───────────┘
           │ BLE Signal
           │ (RSSI)
           ↓
┌──────────────────────┐             ┌────────────────────────────────┐
│  ESP32-S3 + OV5640   │             │      Mac Computer              │
│  (Hardware Part 1)   │───Video───▶│     (Backend Server)           │
│                      │  Frames     │                                │
│  • OV5640 Camera     │  (10FPS)    │  • Flask Server (Port 5001)    │
│  • BLE Scanner       │             │  • YOLOv8s AI Model            │
│  • Distance Calc     │──Distance─▶│  • Video Processing            │
│  • RSSI Monitoring   │    Data     │  • Distance Monitoring         │
│                      │   (1Hz)     │  • Alert Trigger Logic         │
└──────────────────────┘             │  • Video Storage (Max 10)      │
                                     └─────────────┬──────────────────┘
                                                   │            
                                                   │ HTTP/      
                                                   │ Stream     
                                                   │            
                                                   ↓            
                                            ┌─────────────┐
                                            │  iOS App    │  
                                            │ (iPhone)    │  
                                            │             │  
                                            │ • Live View │  
                                            │ • Videos    │  
                                            │ • Alerts    │  
                                            └─────────────┘
```

```
SYSTEM ARCHITECTURE

┌─────────────────────────────────────────────────────────┐
│                    PETGUARD SYSTEM                      │
└─────────────────────────────────────────────────────────┘

HARDWARE LAYER
┌──────────────────────┐         ┌────────────────────┐
│   ESP32-S3           │         │   BLE BEACONS      │
│   Microcontroller    │◄────────┤   (NRF52810)       │
│                      │  RSSI   │                    │
│   + OV5640 Camera    │ Signal  │   Proximity        │
│   • 5MP Resolution   │         │   Detection        │
│   • 10 FPS Capture   │         │   1m Threshold     │
│   • JPEG Encoding    │         └────────────────────┘
│   • Wi-Fi Streaming  │
└──────────┬───────────┘
           │ 
           │ HTTP POST
           │ • Video frames (10 FPS)
           │ • Distance data (1 Hz)
           │ • Wi-Fi (2.4 GHz)
           ▼
SOFTWARE LAYER - BACKEND                                        SOFTWARE LAYER - FRONTEND
┌──────────────────────────────────────────────┐               ┌──────────────────────────────────────────────┐
│   MacBook Air (M2) - Backend Server          │               │   iOS APPLICATION:  "PetGuard"               │
│   ┌────────────────────────────────────┐     │               │                                              │
│   │    YOLOv8s AI MODEL                │     │               │     Live Stream Page                         │
│   │    • 72 layers                     │     │  HTTP GET/POST│      • Real-time video display               │
│   │    • 28. 4 GFLOPs                  │     │  ───────────► │      • Detection labels overlay              │
│   │    • 77% mAP50 Accuracy            │     │  • Annotated  │      • Connection status                     │
│   │    • Real-time inference (<100ms)  │     │    frames     │                                              │
│   └────────────────────────────────────┘     │  • Video      │     Recordings Page                          │
│                                              │    recordings │      • Video list with metadata              │
│   Processing Pipeline:                       │  • Alert      │      • Playback (2x speed)                   │
│   1.  Receive frames → 2. AI detection →     │    signals    │      • Timestamp & file size                 │
│   3. Check conditions → 4. Record video      │               │                                              │
│   5. Send to iOS → 6. Store recordings       │               │     Settings Page                            │
│                                              │               │      • IP configuration                      │
│   Flask HTTP Server:  Port 5001              │               │      • Connection testing                    │
│   Endpoints: /esp32/frame, /esp32/distance   │               │                                              │
│             /stream/live, /videos            │               │     Alert System                             │
└──────────────────────────────────────────────┘               │      • Proximity warnings                    │
                                                               │      • Recording notifications               │
                                                               └──────────────────────────────────────────────┘

DATA FLOW:  ESP32-S3 → Backend → iOS App
PROCESSING: Edge capture + Server AI + Mobile display
NETWORK: Private Wi-Fi (all devices same SSID)
```

---

## Detailed Data Flow

### Flow 1: Video Stream & AI Detection
```
1. ESP32-S3 OV5640 captures video frame
        ↓
2. ESP32-S3 sends frame to Mac backend (WiFi)
        ↓
3. Mac runs YOLOv8 detection
        ↓
4. Detects human/cat with confidence scores
        ↓
5. If both detected → Auto-record video
        ↓
6. Mac streams annotated video to iOS app
        ↓
7. iOS app displays live feed with detections
```

### Flow 2: BLE Distance Monitoring & Alerts
```
1. BLE Beacon continuously broadcasts signal
        ↓
2. ESP32-S3 scans BLE signal (RSSI)
        ↓
3. ESP32-S3 calculates distance from RSSI
        ↓
4. ESP32-S3 sends distance data to Mac backend
        ↓
5. Mac backend compares with iOS threshold settings
        ↓
6. If distance < threshold (e.g., <1m):
        ↓
7. Mac sends alert to iOS app
        ↓
8. iOS app displays: "Too close!" notification
```

### Flow 3: Remote Motor Control
```
1. User presses button on iOS app
        ↓
2. iOS sends motor command to Mac backend
        ↓
3. Mac backend relays command to ESP32-CAM motor
        ↓
4. ESP32-CAM receives command via WiFi
        ↓
5. ESP32-CAM controls servo motor (GPIO)
        ↓
6. Servo executes movement (rotate, move, etc.)
        ↓
7. Completion status sent back to iOS app
```

---

## Communication Protocols

### ESP32-S3 ↔ Mac Backend
- **Protocol**: HTTP/WebSocket (WiFi)
- **Data Sent**:
  - Video frames (JPEG/MJPEG)
  - BLE distance data (JSON)
  - Status updates

### BLE Beacon ↔ ESP32-S3
- **Protocol**: Bluetooth Low Energy (BLE)
- **Data**: RSSI signal strength
- **Range**: Typically 1-10 meters

### ESP32-CAM Motor ↔ Mac Backend
- **Protocol**: HTTP/WebSocket (WiFi)
- **Data Received**: Motor commands (JSON)
- **Data Sent**: Execution status

### iOS App ↔ Mac Backend
- **Protocol**: HTTP REST API + MJPEG Stream
- **Endpoints**:
  - `/stream/live` - Live video feed
  - `/status` - System status
  - `/motor/control` - Motor commands
  - `/ble/distance` - Distance data
  - `/ble/settings` - Threshold configuration
  - `/videos` - Recorded videos

---

## Key Features

### AI Detection
- Real-time human & cat detection
- Auto-recording when both present
- Confidence scoring
- Bounding box visualization

### BLE Proximity Monitoring
- Distance calculation from RSSI
- Configurable thresholds (iOS app)
- Real-time alerts ("Too close!")
- Multi-beacon support (future)

### Remote Motor Control
- Button-triggered commands
- WiFi-based control
- Real-time execution
- Status feedback

### Video Management
- Auto-recording interactions
- Storage limit (10 videos)
- Auto-cleanup old files
- Playback on iOS

---

## Current Implementation Status

| Component | Status | Notes |
|-----------|--------|-------|
| ESP32-S3 + OV5640 | Complete | Camera streaming + BLE scanning working |
| ESP32-CAM Motor | Not Implemented | Motor control moved to separate project |
| BLE Beacon | Complete | Single beacon proximity detection active |
| Mac Backend Server | Complete | Flask server operational with dual camera support |
| YOLOv8 AI Model | Complete | 77% mAP50 accuracy, ESP32 + webcam modes |
| iOS App (PetGuard) | Complete | Live view, videos, proximity alerts working |

---

## Technical Specifications

### Hardware Requirements
- **ESP32-S3**: WiFi + BLE capable
- **OV5640 Camera**: 5MP sensor
- **ESP32-CAM**: Motor control board
- **Servo Motor**: 180° rotation
- **BLE Beacon**: iBeacon compatible
- **Mac/Jetson**: Python 3.8+, 8GB RAM

### Software Stack
- **Backend**: Python 3.8+, Flask, OpenCV, Ultralytics
- **AI Model**: YOLOv8s (PyTorch)
- **iOS App**: Swift 5+, SwiftUI, iOS 15+
- **ESP32**: Arduino IDE, ESP-IDF

### Network Configuration
- **Backend Server**: Port 5001
- **WiFi**: Local network (2.4/5GHz)
- **BLE**: Bluetooth 4.0+

---

## Future Enhancements

1. **Multi-Beacon Positioning**
   - Add 2+ beacons for triangulation
   - More accurate indoor positioning
   - Room-level tracking

2. **Advanced Motor Control**
   - Multiple servo support
   - Preset movement patterns
   - Automated patrol mode

3. **Enhanced AI Detection**
   - Activity recognition
   - Behavior analysis
   - Pet identification

4. **Cloud Integration**
   - Remote access via cloud
   - Video backup to cloud storage
   - Multi-device synchronization

---

## System Integration Points

### Critical Integration Tasks Remaining

1. **ESP32-S3 Integration**
   - [ ] Implement BLE scanning code
   - [ ] Calculate distance from RSSI
   - [ ] Send distance data to backend
   - [ ] Optimize video streaming

2. **Backend Enhancements**
   - [ ] Add BLE distance endpoint
   - [ ] Implement alert trigger logic
   - [ ] Add motor control relay endpoint
   - [ ] Distance threshold management

3. **iOS App Updates**
   - [ ] Add BLE settings UI
   - [ ] Implement proximity alerts
   - [ ] Add motor control buttons
   - [ ] Display distance data

4. **ESP32-CAM Motor**
   - [ ] WiFi communication with backend
   - [ ] Command parsing logic
   - [ ] Motor control execution
   - [ ] Status reporting

---

## Backend Camera Source Switching & ESP32 Streaming

The backend server now supports two camera sources:
- **ESP32-S3 Camera**: Streams JPEG frames via HTTP POST to `/esp32/frame` endpoint.
- **Mac/Jetson Webcam**: Uses local webcam (OpenCV) for video capture.

You can switch between sources at runtime using the `/esp32/enable` endpoint:
- `POST /esp32/enable` with `{ "enable": true }` to use ESP32-S3 camera
- `POST /esp32/enable` with `{ "enable": false }` to use Mac webcam

**ESP32 Frame Upload:**
- ESP32-S3 sends JPEG frames to the backend:
  - Endpoint: `POST /esp32/frame`
  - Content-Type: `image/jpeg`
  - Body: JPEG binary data

The backend will run YOLOv8 detection on each received frame and update the live stream and recording logic accordingly.

---

**Document Version**: 1.0  
**Last Updated**: December 8, 2025  
**Project**: Human-Cat Interaction Detector  
**Repository**: chiuuung/new-FYP
