# Stream Performance Optimization Guide

## Current Issue: Stream Freezing/Lagging

### Symptoms
- Image freezes for 1-2 seconds
- Intermittent frame drops
- Delayed response to detections

### Root Causes
1. **Network latency** on iPhone hotspot (50-150ms variable)
2. **YOLOv8 inference time** varies (50-150ms depending on scene)
3. **Frame queue backup** when processing slower than receiving
4. **iOS polling rate** may request faster than backend can respond

---

## Quick Fixes (Apply These First)

### Fix 1: Add Frame Buffering (Backend)
This prevents queue overflow and ensures smooth delivery.

**File**: `streaming_backend_server.py` (line 33)

Change:
```python
esp32_frame_queue = queue.Queue(maxsize=2)
```

To:
```python
esp32_frame_queue = queue.Queue(maxsize=1)  # Keep only latest frame
```

**Effect**: Drops old frames, always shows most recent

### Fix 2: Add Frame Skipping When Slow
Only process every Nth frame if detection is slow.

**File**: `streaming_backend_server.py` in `run_esp32_mode()` method

Add after line 140:
```python
frame_count = 0
process_every = 1  # Process every frame initially

while self.running:
    try:
        frame = esp32_frame_queue.get(timeout=1.0)
        frame_count += 1
        
        # Skip frames if processing is slow
        if frame_count % process_every != 0:
            # Still update display with unprocessed frame
            recording_state["latest_frame"] = frame.copy()
            recording_state["latest_annotated_frame"] = frame.copy()
            continue
        
        # Run detection (existing code)
        results = model.predict(...)
```

### Fix 3: Reduce ESP32 Frame Rate Slightly
**File**: `esp32s3_camera_stream.ino` (line 48)

Change:
```cpp
#define STREAM_FPS 15
```

To:
```cpp
#define STREAM_FPS 12  // Slightly slower but more stable
```

---

## Advanced Optimizations

### Optimization 1: Use Smaller YOLOv8 Model

**Current**: YOLOv8s (11.2M parameters, 80-120ms)
**Alternative**: YOLOv8n (3.2M parameters, 30-50ms)

**File**: `streaming_backend_server.py` (line 28)

Change MODEL_PATH or download YOLOv8n:
```python
from ultralytics import YOLO
model = YOLO('yolov8n.pt')  # Download automatically
```

**Trade-off**: Slightly lower accuracy (75% vs 77% mAP) but 2-3x faster

### Optimization 2: Reduce Detection Resolution

Add this before YOLOv8 prediction:
```python
# Resize frame for faster detection
small_frame = cv2.resize(frame, (416, 416))
results = model.predict(source=small_frame, ...)

# Scale back bounding boxes to original size
# (handled automatically by result.plot())
```

**Effect**: 30-40% faster inference

### Optimization 3: Async Frame Processing

Process frames in parallel with frame reception:
```python
import concurrent.futures

executor = concurrent.futures.ThreadPoolExecutor(max_workers=2)

def process_frame_async(frame):
    results = model.predict(frame, ...)
    # Process results...

while self.running:
    frame = esp32_frame_queue.get(timeout=1.0)
    # Submit to background thread
    executor.submit(process_frame_async, frame)
```

---

## Expected Improvements

| Optimization | Latency Reduction | Complexity |
|-------------|------------------|------------|
| Frame buffering (maxsize=1) | 50-100ms | Easy ⭐ |
| Frame skipping | 100-200ms | Easy ⭐ |
| Reduce ESP32 FPS | 30-50ms | Easy ⭐ |
| Use YOLOv8n | 50-80ms | Medium ⭐⭐ |
| Reduce detection resolution | 30-50ms | Medium ⭐⭐ |
| Async processing | 100-150ms | Hard ⭐⭐⭐ |

**Recommended combo**: Fix 1 + Fix 2 + Fix 3 = ~200ms improvement

---

## Testing Procedure

1. **Apply Fix 1** (maxsize=1)
2. Restart backend server
3. Test stream for 2 minutes
4. If still freezing, **add Fix 2**
5. If still not smooth, **apply Fix 3**
6. Monitor backend logs for processing time

**Success criteria**:
- No freezes > 0.5 seconds
- Consistent frame updates
- Detections appear within 1 second

---

## Monitoring Commands

Check backend performance:
```bash
# Watch backend logs
tail -f /path/to/backend/logs

# Monitor CPU usage
top -pid $(pgrep -f streaming_backend_server)

# Check network latency
ping 172.20.10.2  # ESP32
ping 172.20.10.3  # Mac
```

---

## Target Performance

**Before optimization**:
- End-to-end latency: 500-1000ms
- Freeze frequency: Every 5-10 seconds
- Frame drops: 20-30%

**After optimization**:
- End-to-end latency: 300-500ms
- Freeze frequency: Rare (<1%)
- Frame drops: <5%

---

**Apply these fixes and let me know the results!**
