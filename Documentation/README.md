# Human-Cat Interaction Detector with iOS App

An AI-powered system to detect humans and cats using computer vision, with iOS app for remote monitoring. Designed for deployment on **Mac** and **NVIDIA Jetson Nano**.

## 🎯 Project Overview

This system uses deep learning (YOLOv8) to:
- Detect **humans** and **cats** in real-time via webcam
- Auto-record interactions when both cat and human detected
- Stream live video to iOS devices for remote monitoring
- Automatically manage storage (keeps 10 newest recordings)
- Achieve **77.0% mAP50** on expanded dataset (2500+ images)

### Current Status: ✅ Phase 2 Complete
- ✅ 2-class object detection (human: 63.7%, cat: 90.4% mAP50)
- ✅ Trained model: YOLOv8s on 2500+ images
- ✅ **iOS App**: Remote viewer with video playback
- ✅ **Auto-recording**: Detects cat+human interactions
- ✅ **Storage management**: Auto-cleanup (max 10 videos)
- ✅ **Streaming server**: Mac/Jetson webcam → iOS viewer
- ⏳ Jetson Nano deployment (next phase)

## 🛠️ Hardware Requirements

- **NVIDIA Jetson Nano** (2GB or 4GB model)
- **USB Camera** or CSI Camera module
- **Power supply** (5V 4A recommended)
- **MicroSD card** (64GB+ recommended)
- Optional: External cooling fan

## 📋 Software Requirements

### Current Development Environment
- **Python:** 3.14.0
- **PyTorch:** 2.9.0+cpu (CPU-only validated)
- **YOLOv8:** Ultralytics 8.3.222
- **OpenCV:** 4.12.0.88
- **Platform:** Windows 11

### For Deployment (Jetson Nano) - Future
- JetPack 4.6+ (includes Ubuntu 18.04, CUDA, cuDNN)
- Python 3.6+
- TensorRT optimization recommended

## 🚀 Quick Start

### ✅ Current Status: Streaming System Ready

**Trained Model Location:**  
`runs/best_accuracy/yolov8s_massive/weights/best.pt`

**Performance:**
- Overall mAP50: 77.0% (on 2500+ images)
- Cat Detection: 90.4% mAP50
- Human Detection: 63.7% mAP50
- Model: YOLOv8s

### 🎥 Run the Streaming System

**1. Start Backend Server (Mac/Jetson):**
```bash
cd /path/to/hand-pet-interaction-detector
python3 ios_app/streaming_backend_server.py
```

**2. Stop Server:**
```bash
# Press Ctrl+C or run:
lsof -ti:5001 | xargs kill -9
```

**3. Run iOS App:**
- Open `ios_app/HandPetInteraction.xcodeproj` in Xcode
- Update server URL in Settings: `http://YOUR_MAC_IP:5001`
- Run on iPhone/iPad
- View live stream and recorded videos

### 📖 Documentation Quick Links

| Document | Purpose |
|----------|---------|  
| **[ios_app/STREAMING_SETUP.md](ios_app/STREAMING_SETUP.md)** | ⭐ iOS App Setup & Streaming Guide |
| **[TRAINING_DOCUMENTATION.md](TRAINING_DOCUMENTATION.md)** | Complete training methodology & results |
| **[QUICK_TEST_GUIDE.md](QUICK_TEST_GUIDE.md)** | Test with webcam, images, or video |
| **[TERMINAL_RECORD.md](TERMINAL_RECORD.md)** | All commands used (reproducibility) |
| **[DATA_COLLECTION_GUIDE.md](DATA_COLLECTION_GUIDE.md)** | How data was collected & labeled |
| **[JETSON_SETUP.md](JETSON_SETUP.md)** | Deploy to Jetson Nano (future) |### 🧪 Test the Model Now

**1. Test with Webcam:**
```powershell
& "C:\Users\ngtszch\AppData\Local\Programs\Python\Python314\python.exe" "test_model.py" --source webcam
```

**2. Test with Images:**
```powershell
& "C:\Users\ngtszch\AppData\Local\Programs\Python\Python314\python.exe" "test_model.py" --source "data\yolo_dataset\images\test"
```

**3. Test with Your Own Image:**
```powershell
& "C:\Users\ngtszch\AppData\Local\Programs\Python\Python314\python.exe" "test_model.py" --source "path\to\your\image.jpg"
```

See **[QUICK_TEST_GUIDE.md](QUICK_TEST_GUIDE.md)** for more testing options.

### 🎓 Want to Train Your Own Model?

See **[DATA_COLLECTION_GUIDE.md](DATA_COLLECTION_GUIDE.md)** for:
- How to collect cat images
- How to label them
- How to train the model

**Quick training command:**
```powershell
& "C:\Users\ngtszch\AppData\Local\Programs\Python\Python314\python.exe" "train_model.py" --data-dir "data\yolo_dataset" --epochs 50 --batch-size 4 --device cpu
```

## 📁 Project Structure

```
hand-pet-interaction-detector/
├── train_model.py          # Model training script
├── test_model.py           # Model testing script
├── requirements.txt        # Python dependencies
├── ios_app/               # ⭐ iOS App & Backend
│   ├── streaming_backend_server.py  # Mac/Jetson streaming server
│   ├── cleanup_videos.py            # Video storage management
│   ├── STREAMING_SETUP.md           # Setup guide
│   ├── StreamView.swift             # iOS stream viewer
│   ├── ContentView.swift            # iOS main view
│   ├── NetworkManager.swift         # iOS networking
│   └── VideosView.swift             # iOS video player
├── recorded_videos/       # Auto-recorded interactions (max 10)
├── runs/
│   └── best_accuracy/
│       └── yolov8s_massive/
│           └── weights/
│               └── best.pt        # Trained model (77% mAP50)
└── data/
    └── expanded_dataset/          # 2500+ annotated images
```

## ⚙️ Configuration

Edit `config/config.json` to customize:

```json
{
  "model_path": "models/best.pt",
  "confidence_threshold": 0.5,
  "touching_threshold": 50,
  "hitting_threshold": 15,
  "velocity_hitting_threshold": 100,
  "enable_sound_alert": true,
  "enable_logging": true,
  "camera_width": 640,
  "camera_height": 480,
  "camera_fps": 30
}
```

### Key Parameters:
- **touching_threshold**: Distance in pixels to detect touching (default: 50)
- **hitting_threshold**: Distance in pixels for hitting detection (default: 15)
- **velocity_hitting_threshold**: Human velocity threshold in px/s (default: 100)
- **confidence_threshold**: Minimum detection confidence (default: 0.5)

## 🎥 Camera Setup

### USB Camera
```bash
# List available cameras
ls /dev/video*

# Test camera
python3 -c "import cv2; cap = cv2.VideoCapture(0); print(cap.isOpened())"
```

### CSI Camera (Raspberry Pi Camera)
```bash
# Use GStreamer pipeline in main.py
# Modify camera initialization to use CSI camera
```

## 🔧 Optimization for Jetson Nano

### 1. Use FP16 Precision
The training script includes automatic FP16 optimization:
```bash
python train_model.py --optimize
```

### 2. Adjust Performance Mode
```bash
# Maximum performance
sudo nvpmodel -m 0
sudo jetson_clocks
```

### 3. Reduce Image Size
In `config/config.json`:
```json
{
  "camera_width": 416,
  "camera_height": 416
}
```

### 4. Use TensorRT (Advanced)
```bash
# Convert model to TensorRT
# See Jetson optimization guides
```

## 📊 Performance Metrics

Expected performance on Jetson Nano:
- **YOLOv5n**: ~15-20 FPS (416x416)
- **YOLOv8n**: ~12-18 FPS (416x416)
- **YOLOv5s**: ~8-12 FPS (640x640)

## 📱 iOS App Features

### Live Streaming
- **Real-time view**: See Mac/Jetson webcam feed on iPhone/iPad
- **Detection overlay**: View human and cat detections in real-time
- **Recording indicator**: Shows when interaction is being recorded
- **Confidence scores**: Displays detection confidence levels

### Auto-Recording
- **Smart trigger**: Automatically records when cat AND human detected
- **Cooldown period**: 2-second timeout between recordings
- **Storage management**: Auto-cleanup keeps only 10 newest videos
- **Timestamp naming**: `interaction_YYYYMMDD_HHMMSS.mp4`

### Video Playback
- **Browse recordings**: List of all saved interaction videos
- **Thumbnail preview**: Visual preview of each recording
- **Built-in player**: Play videos directly in the app
- **Auto-refresh**: List updates automatically

### Configuration
- **Server URL**: Set Mac/Jetson IP address
- **Connection test**: Verify server connectivity
- **Port**: 5001 (configurable in server)

## 📝 Training Tips

1. **Collect diverse data**: Different lighting, angles, pets, people
2. **Balance classes**: Equal samples of touching, hitting, no-interaction
3. **Augmentation**: YOLOv8 includes built-in augmentation
4. **Start small**: Begin with YOLOv8n, upgrade if needed
5. **Monitor training**: Use TensorBoard

```bash
tensorboard --logdir runs/train
```

## 🐛 Troubleshooting

### Camera not detected
```bash
# Check camera connections
v4l2-ctl --list-devices

# Try different camera IDs
python3 main.py --camera 1
```

### Low FPS on Jetson
- Reduce image resolution
- Use smaller model (YOLOv8n)
- Enable maximum performance mode
- Close other applications

### Model not loading
- Check model path in `config/config.json`
- Ensure model is in `models/` directory
- Verify PyTorch version compatibility

### Out of memory on Jetson
- Reduce batch size during training
- Use swap space
- Close other applications

## 📚 Additional Resources

- [YOLOv5 Documentation](https://github.com/ultralytics/yolov5)
- [YOLOv8 Documentation](https://docs.ultralytics.com/)
- [Jetson Nano Guide](https://developer.nvidia.com/embedded/learn/get-started-jetson-nano-devkit)
- [NVIDIA JetPack](https://developer.nvidia.com/embedded/jetpack)

## 🤝 Contributing

This is a FYP project. Suggestions and improvements are welcome!

## 📄 License

This project is for educational purposes.

## 👤 Author

FYP Project - Human-Pet Interaction Detection System

## 🙏 Acknowledgments

- Ultralytics for YOLOv5/YOLOv8
- NVIDIA for Jetson platform
- OpenCV community

---

## 📞 Support

For issues or questions about this project, please create an issue in the repository or contact the project maintainer.

**Good luck with your FYP! 🚀**
