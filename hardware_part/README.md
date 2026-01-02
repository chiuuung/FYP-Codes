# Hardware Part - Complete System Overview

## Two Independent ESP32 Systems

This project uses **TWO separate ESP32 devices** for different purposes:

```
┌─────────────────────────────────────────────────────────────────┐
│                      YOUR COMPLETE SYSTEM                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌────────────────────────────┐  ┌────────────────────────────┐│
│  │  ESP32 #1 (Monitoring)     │  │  ESP32 #2 (Motor Control)  ││
│  │  /esp32_control/           │  │  /esp32_motor_control/     ││
│  ├────────────────────────────┤  ├────────────────────────────┤│
│  │                            │  │                            ││
│  │  • Camera (OV2640)         │  │  • WiFi Web Server         ││
│  │  • BLE Scanner             │  │  • Motor Driver Control    ││
│  │  • WiFi → Mac Backend      │  │  • iOS App Commands        ││
│  │                            │  │                            ││
│  │  Monitors pet location     │  │  Controls motor remotely   ││
│  │  and sends camera images   │  │  via iOS app buttons       ││
│  │                            │  │                            ││
│  └────────────────────────────┘  └────────────────────────────┘│
│              │                                  │                │
│              ▼                                  ▼                │
│    ┌──────────────────┐              ┌──────────────────┐      │
│    │  3x BLE Beacons  │              │   L298N Driver   │      │
│    │  (passive tags)  │              │   + DC Motor     │      │
│    └──────────────────┘              └──────────────────┘      │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## System #1: Pet Monitoring (ESP32-CAM + BLE Scanner)

**Location:** `/hardware_part/esp32_control/`

**Purpose:** Monitor pet location and stream camera feed to Mac for AI detection

**Hardware:**
- 1x ESP32-CAM module ($12) - has built-in camera
- 3x Passive BLE beacon tags ($5-10 each) - Tile, Chipolo, or generic

**What it does:**
1. **Captures images** (10 FPS) from built-in camera
2. **Scans BLE beacons** every 2 seconds to detect room location
3. **Sends data to Mac** via WiFi:
   - Camera frames → YOLOv8 detection
   - Beacon RSSI data → Room identification
4. **Receives commands** from Mac (motor activation, alerts)

**Data Flow:**
```
BLE Beacons → ESP32-CAM → WiFi → Mac Backend → YOLOv8 Detection
                  ↓                      ↓
              Camera                 Auto-record
                                     iOS App Alerts
```

**Files:**
- `esp32_cam_ble_allinone.ino` - Main code (camera + BLE scanning)
- `ESP32_CAM_SETUP_GUIDE.md` - Complete setup instructions
- `BLUETOOTH_INDOOR_POSITIONING.md` - Technical details
- `README.md` - Overview and quick start

**Cost:** ~$30 (1 ESP32-CAM + 3 beacons)

---

## System #2: Remote Motor Control (ESP32 + Motor)

**Location:** `/hardware_part/esp32_motor_control/`

**Purpose:** Control a motor remotely via iOS app button presses

**Hardware:**
- 1x ESP32 DevKit ($12) - any model with WiFi
- 1x L298N Motor Driver ($8)
- 1x DC Motor ($5)
- Power supply (USB + battery/adapter)

**What it does:**
1. **Runs WiFi web server** on port 8080
2. **Receives commands** from iOS app:
   - `MOTOR_ON` - Turn motor on
   - `MOTOR_OFF` - Turn motor off
   - `MOTOR_TOGGLE` - Toggle motor state
3. **Controls motor** through L298N driver
4. **Sends status** back to iOS app

**Data Flow:**
```
iOS App → WiFi → ESP32 Web Server → L298N Driver → DC Motor
              ↑                          ↓
         Port 8080                  Motor Control
```

**Files:**
- `esp32_motor_control.ino` - Main code (WiFi server + motor control)
- `README.md` - Complete setup guide, wiring, API docs

**Cost:** ~$25 (1 ESP32 + motor + driver)

---

## Why Two Separate ESP32s?

### Design Decision

**Alternative (Not Used):** Single ESP32 doing everything
- ❌ Too complex - hard to debug
- ❌ Camera + WiFi + BLE + motor = overloaded
- ❌ If camera fails, motor fails too
- ❌ Limited GPIO pins for expansion

**Current Design (Recommended):** Two independent ESP32s
- ✅ Each system testable separately
- ✅ Clear separation of concerns
- ✅ Easy to debug and maintain
- ✅ Can develop/test motor control without camera
- ✅ If one fails, other keeps working
- ✅ More GPIO pins available on each

### Cost Comparison

| Component | Quantity | Unit Price | Total |
|-----------|----------|------------|-------|
| **System #1** | | | |
| ESP32-CAM | 1 | $12 | $12 |
| BLE Beacons | 3 | $7 | $21 |
| **System #2** | | | |
| ESP32 DevKit | 1 | $12 | $12 |
| L298N Driver | 1 | $8 | $8 |
| DC Motor | 1 | $5 | $5 |
| **Total** | | | **$58** |

Still cheaper than Arduino + WiFi shield ($45) + ESP32-CAM ($12) + motor ($13) = $70!

---

## Complete Wiring Diagrams

### System #1: ESP32-CAM + BLE Beacons

```
┌─────────────────────────────────────────────────────────┐
│  ESP32-CAM Module                                       │
│  ┌────────────────────────┐                            │
│  │                        │                            │
│  │   [OV2640 Camera]      │                            │
│  │                        │                            │
│  │   WiFi: 172.20.10.3    │◄─── USB Power (5V)       │
│  │   Port: 5001           │                            │
│  │                        │                            │
│  └────────────────────────┘                            │
│            │                                            │
│            │ Scans for BLE signals                     │
│            ▼                                            │
│  ┌─────────────────────────────────────────┐          │
│  │  3 Passive BLE Beacon Tags              │          │
│  │                                          │          │
│  │  📍 Living Room Beacon                  │          │
│  │     MAC: AA:BB:CC:DD:EE:01              │          │
│  │     (Allowed zone)                      │          │
│  │                                          │          │
│  │  📍 Bedroom Beacon                      │          │
│  │     MAC: AA:BB:CC:DD:EE:02              │          │
│  │     (Forbidden zone)                    │          │
│  │                                          │          │
│  │  📍 Kitchen Beacon                      │          │
│  │     MAC: AA:BB:CC:DD:EE:03              │          │
│  │     (Allowed zone)                      │          │
│  └─────────────────────────────────────────┘          │
└─────────────────────────────────────────────────────────┘

No physical connections between ESP32-CAM and beacons!
Beacons just broadcast, ESP32-CAM scans wirelessly.
```

### System #2: ESP32 + Motor Control

```
┌──────────────────────────────────────────────────────────────┐
│  ESP32 Motor Control System                                  │
│                                                               │
│  ┌──────────────┐          ┌────────────────┐              │
│  │   ESP32      │          │  L298N Driver  │              │
│  │   DevKit     │          │                │              │
│  │              │          │                │              │
│  │  GPIO 25 ────┼─────────►│ IN1            │              │
│  │  GPIO 26 ────┼─────────►│ IN2            │              │
│  │              │          │                │              │
│  │  GND     ────┼─────────►│ GND            │              │
│  │              │          │                │              │
│  │  5V (USB)    │          │ +12V ◄─────────┼──── Battery  │
│  │              │          │                │     or       │
│  │  WiFi Server │          │ OUT1 ──────────┼──┐  Adapter  │
│  │  Port: 8080  │          │ OUT2 ──────────┼──┤          │
│  │              │          │                │  │          │
│  └──────────────┘          └────────────────┘  │          │
│         ▲                                       │          │
│         │                                       ▼          │
│         │                            ┌──────────────────┐ │
│    iOS App Commands                  │   DC Motor ⚡    │ │
│    (WiFi Network)                    │   6-12V          │ │
│                                      └──────────────────┘ │
└──────────────────────────────────────────────────────────────┘

Important:
- ESP32 and L298N MUST share common ground (GND)
- Motor power separate from ESP32 power
- GPIO 25/26 control motor direction
```

---

## Network Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Network Topology                          │
│               (All on same WiFi/Hotspot)                    │
│                                                              │
│  ┌──────────────┐           ┌──────────────┐              │
│  │  iPhone      │           │  Mac Backend │              │
│  │              │           │              │              │
│  │  iOS App     │◄─────────►│  Python      │              │
│  │  Port: -     │   WiFi    │  Port: 5001  │              │
│  │              │           │              │              │
│  │              │           │  • YOLOv8    │              │
│  │              │           │  • Detection │              │
│  │              │           │  • Recording │              │
│  └──────┬───────┘           └──────┬───────┘              │
│         │                          │                       │
│         │                          │                       │
│         │    ┌─────────────────────┴────────┐             │
│         │    │                              │             │
│         ▼    ▼                              ▼             │
│  ┌─────────────────┐              ┌──────────────────┐   │
│  │  ESP32 #2       │              │  ESP32-CAM #1    │   │
│  │  Motor Control  │              │  Monitoring      │   │
│  │                 │              │                  │   │
│  │  172.20.10.4    │              │  172.20.10.3     │   │
│  │  Port: 8080     │              │  Sends to 5001   │   │
│  └─────────────────┘              └──────────────────┘   │
│                                                           │
└─────────────────────────────────────────────────────────────┘

Communication Paths:
1. iOS App ←→ Mac Backend (stream, videos, alerts)
2. iOS App → ESP32 #2 (motor control commands)
3. ESP32-CAM #1 → Mac Backend (camera frames, beacon data)
4. Mac Backend → iOS App (detection results, alerts)
```

---

## Setup Order (Recommended)

### Phase 1: Test Motor Control First (Easier)
1. Build ESP32 #2 motor control system
2. Upload `esp32_motor_control.ino`
3. Test with Serial Monitor
4. Test with curl/browser
5. Integrate with iOS app
6. ✅ Motor working independently

### Phase 2: Add Camera Monitoring
1. Build ESP32-CAM #1 system
2. Place BLE beacons in rooms
3. Find beacon MAC addresses
4. Upload `esp32_cam_ble_allinone.ino`
5. Test camera streaming to Mac
6. Test BLE room detection
7. ✅ Full monitoring system working

### Phase 3: Integration
1. Both systems running
2. iOS app controls motor (ESP32 #2)
3. iOS app monitors pet (ESP32-CAM #1 → Mac)
4. Automation: forbidden zone → auto-activate motor
5. ✅ Complete integrated system!

---

## File Structure

```
hardware_part/
├── README.md (this file)
│
├── esp32_control/              # System #1: Camera + BLE Monitoring
│   ├── esp32_cam_ble_allinone.ino
│   ├── ble_beacon.ino          # (optional, if you make your own beacons)
│   ├── ble_scanner_motor.ino   # (alternative design)
│   ├── ESP32_CAM_SETUP_GUIDE.md
│   ├── BLUETOOTH_INDOOR_POSITIONING.md
│   └── README.md
│
└── esp32_motor_control/        # System #2: Remote Motor Control
    ├── esp32_motor_control.ino
    └── README.md
```

---

## Quick Start Commands

### System #1 (ESP32-CAM)
```bash
# Navigate to esp32_control folder
cd hardware_part/esp32_control

# Open code in Arduino IDE
open esp32_cam_ble_allinone.ino

# After upload, check Serial Monitor (115200 baud)
# Note the IP address (e.g., 172.20.10.3)
```

### System #2 (Motor Control)
```bash
# Navigate to esp32_motor_control folder
cd hardware_part/esp32_motor_control

# Open code in Arduino IDE
open esp32_motor_control.ino

# After upload, test with curl
curl -X POST http://172.20.10.4:8080/motor/control \
  -H "Content-Type: application/json" \
  -d '{"command":"ON"}'
```

---

## Troubleshooting Guide

### Both Systems Won't Connect to WiFi
**Solution:** Check iPhone hotspot is on, verify SSID/password in both .ino files

### Can't Find BLE Beacons
**Solution:** Use nRF Connect app on phone to scan, verify beacons are powered on

### Motor Doesn't Spin
**Solution:** Check wiring (GPIO 25/26), verify motor power supply, test with battery

### Camera Images Not Received
**Solution:** Check WiFi connection, verify Mac backend running, check firewall

### iOS App Can't Connect
**Solution:** Verify all devices on same network, check IP addresses match

---

## Shopping List

### Essential (Required)
- [ ] 1x ESP32-CAM ($12) - for camera + BLE scanning
- [ ] 3x BLE beacon tags ($21) - Tile/Chipolo/generic
- [ ] 1x ESP32 DevKit ($12) - for motor control
- [ ] 1x L298N motor driver ($8)
- [ ] 1x DC motor 6-12V ($5)
- [ ] 1x USB cables ($5)
- **Total: $63**

### Optional (Nice to Have)
- [ ] Breadboard + jumper wires ($8)
- [ ] Power bank for portable ESP32 ($15)
- [ ] 9V or 12V battery pack for motor ($10)
- [ ] 3D printed case for ESP32-CAM ($5)
- [ ] Extra ESP32s for backup ($12 each)

---

## Success Criteria

### System #1 Checklist
- [ ] ESP32-CAM connects to WiFi
- [ ] Camera images visible in Mac backend logs
- [ ] All 3 BLE beacons detected
- [ ] Correct room identified based on signal strength
- [ ] RSSI values reasonable (-40 to -80 dBm)
- [ ] Data sent to Mac every 2 seconds

### System #2 Checklist
- [ ] ESP32 motor controller connects to WiFi
- [ ] Web server responds on port 8080
- [ ] Motor turns ON with curl command
- [ ] Motor turns OFF with curl command
- [ ] iOS app can send commands
- [ ] Motor responds to iOS app buttons

### Integration Checklist
- [ ] Both ESP32s on same network
- [ ] iOS app shows live stream
- [ ] iOS app control tab works
- [ ] Motor activates when entering forbidden zone
- [ ] Auto-recording triggers correctly
- [ ] All systems stable for 30+ minutes

---

## Support Resources

- **ESP32-CAM Pinout:** https://randomnerdtutorials.com/esp32-cam-ai-thinker-pinout/
- **L298N Driver Guide:** https://lastminuteengineers.com/l298n-dc-stepper-driver-arduino-tutorial/
- **BLE Beacon Scanning:** https://randomnerdtutorials.com/esp32-ble-server-client/
- **Arduino ESP32 Docs:** https://docs.espressif.com/projects/arduino-esp32/

---

## Future Enhancements

### Phase 1 (Basic) - Current Implementation ✅
- 2 ESP32 systems working independently
- Camera monitoring + motor control
- BLE room detection
- iOS app integration

### Phase 2 (Advanced)
- [ ] Add battery level monitoring
- [ ] Implement deep sleep for power saving
- [ ] Add more BLE beacons (4-6 rooms)
- [ ] Motor speed control (PWM)
- [ ] Schedule motor activation times

### Phase 3 (Professional)
- [ ] Web dashboard for monitoring
- [ ] Historical movement data visualization
- [ ] Machine learning for behavior prediction
- [ ] Multi-pet support (multiple ESP32-CAMs)
- [ ] Cloud storage integration

---

## Credits

**Project:** Hand-Pet Interaction Detector with Indoor Positioning
**Course:** Final Year Project (FYP)
**Hardware:** ESP32-based IoT system
**Software:** Python (YOLOv8) + Swift (iOS) + C++ (ESP32)

Built with ❤️ using ESP32, BLE beacons, and open-source tools!
