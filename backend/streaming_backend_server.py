"""
Streaming Backend Server for Hand-Pet Interaction Detection
- Captures video from Mac/Jetson camera
- Runs YOLOv8 detection
- Records when cat+human detected
- Streams live feed to iOS app
"""

from flask import Flask, request, jsonify, send_file, Response
from flask_cors import CORS
from ultralytics import YOLO
import cv2
import numpy as np
import base64
from pathlib import Path
from datetime import datetime
import threading
import queue
import time
import json
# ESP32 MOTOR CONTROL - Commented out (see hardware_part/esp32_motor_control folder)
# import serial
# import serial.tools.list_ports

app = Flask(__name__)
CORS(app)

# Configuration
SCRIPT_DIR = Path(__file__).parent.absolute()  # iOS_App/backend/
PROJECT_ROOT = SCRIPT_DIR.parent.parent.absolute()  # new-FYP/
MODEL_PATH = PROJECT_ROOT / "AI_Model" / "weights" / "best.pt"
VIDEOS_DIR = PROJECT_ROOT / "recorded_videos"

# Video write queue (for async writing)
video_write_queue = queue.Queue(maxsize=3)  # Small queue to prevent memory buildup
VIDEOS_DIR.mkdir(exist_ok=True)

# Global variables
model = None
camera_capture = None
esp32_frame_queue = queue.Queue(maxsize=1)  # Keep only latest frame (prevents lag)
use_esp32_camera = True  # Changed to True: Use ESP32-S3 instead of Mac webcam

recording_state = {
    "is_recording": False,
    "video_writer": None,
    "current_filename": None,
    "last_detection_time": time.time(),
    "both_detected": False,
    "latest_frame": None,
    "latest_annotated_frame": None,
    "detections": []
}

# BLE Beacon proximity state
proximity_state = {
    "distance": 999.0,
    "rssi": -100,
    "is_close": False,
    "last_update": time.time(),
    "beacon_mac": None,
    "proximity_recording": False,
    "proximity_alert_active": False
}

# Detection parameters
CONFIDENCE_THRESHOLD = 0.25
COOLDOWN_SECONDS = 2
CAMERA_ID = 0  # Default camera (0 for Mac webcam, adjust for Jetson)
MAX_VIDEOS = 10  # Keep only the 10 newest videos, delete older ones

# ESP32 MOTOR CONTROL - Commented out (see hardware_part/esp32_motor_control folder)
# esp32_connection = None
# ESP32_ENABLED = False  # Set to True when ESP32 is connected


class CameraThread(threading.Thread):
    """Handles camera capture and detection in separate thread"""
    
    def __init__(self):
        super().__init__(daemon=True)
        self.running = False
        self.camera = None
    
    def run(self):
        """Main camera loop"""
        global use_esp32_camera
        
        print("📹 Starting camera thread...")
        
        if use_esp32_camera:
            print("📡 Using ESP32-S3 camera stream")
            self.running = True
            self.run_esp32_mode()
        else:
            print("📷 Using Mac webcam")
            self.run_webcam_mode()
    
    def run_webcam_mode(self):
        """Use Mac's built-in webcam"""
        # Open camera
        self.camera = cv2.VideoCapture(CAMERA_ID)
        if not self.camera.isOpened():
            print(f"❌ Failed to open camera {CAMERA_ID}")
            return
        
        # Set camera properties
        self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        self.camera.set(cv2.CAP_PROP_FPS, 30)
        
        print(f"✅ Camera opened: {self.camera.get(cv2.CAP_PROP_FRAME_WIDTH)}x{self.camera.get(cv2.CAP_PROP_FRAME_HEIGHT)}")
        
        self.running = True
        frame_count = 0
        
        while self.running:
            ret, frame = self.camera.read()
            
            if not ret:
                print("❌ Failed to read frame")
                time.sleep(0.1)
                continue
            
            frame_count += 1
            
            # Run detection
            results = model.predict(
                source=frame,
                conf=CONFIDENCE_THRESHOLD,
                iou=0.45,
                verbose=False
            )
            
            result = results[0]
            boxes = result.boxes
            
            # Process detections
            self.process_detections(frame, result)
            
            # Small delay
            time.sleep(0.01)
        
        if self.camera:
            self.camera.release()
            print("📹 Webcam released")
    
    def run_esp32_mode(self):
        """Use ESP32-S3 camera frames"""
        print("🔄 Waiting for ESP32-S3 frames...")
        frame_count = 0
        
        while self.running:
            try:
                # Get frame from ESP32 queue (with timeout)
                frame = esp32_frame_queue.get(timeout=1.0)
                frame_count += 1
                
                # Run detection directly (no enhancement for max speed)
                results = model.predict(
                    source=frame,
                    conf=CONFIDENCE_THRESHOLD,
                    iou=0.45,
                    imgsz=640,
                    half=False,  # FP16 disabled for CPU (use half=True on GPU)
                    verbose=False
                )
                
                result = results[0]
                
                # Process detections
                self.process_detections(frame, result)
                
            except queue.Empty:
                # No frame received from ESP32
                if frame_count == 0:
                    print("⏳ Still waiting for ESP32-S3 frames...")
                continue
            except Exception as e:
                print(f"❌ Error processing ESP32 frame: {e}")
                time.sleep(0.1)
        
        print("📹 ESP32 camera thread stopped")
    
    def process_detections(self, frame, result):
        """Process YOLOv8 detection results"""
        boxes = result.boxes
        
        # Parse detections
        detections = []
        has_human = False
        has_cat = False
        
        for box in boxes:
            cls = int(box.cls[0])
            conf = float(box.conf[0])
            class_name = "human" if cls == 0 else "cat"
            
            detections.append({
                "class": class_name,
                "confidence": conf,
                "bbox": box.xyxy[0].tolist()
            })
            
            if class_name == "human":
                has_human = True
            elif class_name == "cat":
                has_cat = True
        
        # Create annotated frame for display (ALWAYS show stream)
        annotated_frame = result.plot()
        
        # Store latest frames (direct assignment, no extra copy)
        recording_state["latest_frame"] = frame
        recording_state["latest_annotated_frame"] = annotated_frame
        recording_state["detections"] = detections
        
        # Update recording state for AI detection
        both_present = has_human and has_cat
        
        if both_present:
            recording_state["last_detection_time"] = time.time()
            recording_state["both_detected"] = True
            
            # Only start AI detection recording if proximity recording is not active
            if not recording_state["is_recording"] and not proximity_state["proximity_recording"]:
                recording_state["is_recording"] = True
                start_recording(frame.shape)
                print("🔴 AI Recording STARTED - Cat and Human detected!")
        
        # Queue frame for recording (works for both AI and proximity recording)
        if recording_state["is_recording"]:
            try:
                # Use put_nowait to avoid blocking if queue is full
                video_write_queue.put_nowait(frame.copy())
            except queue.Full:
                pass  # Skip frame if queue full (prevents lag)
        
        # Check for timeout (only for AI detection recording)
        if recording_state["is_recording"] and not proximity_state["proximity_recording"]:
            check_recording_timeout()
    
    def enhance_frame(self, frame):
        """Enhance ESP32 frame quality for better AI detection (ultra-fast version)"""
        # Quick brightness/contrast adjustment
        alpha = 1.15  # Contrast control
        beta = 10     # Brightness control
        enhanced = cv2.convertScaleAbs(frame, alpha=alpha, beta=beta)
        
        # Ultra-fast bilateral filter (d=3 is 4x faster than d=5)
        enhanced = cv2.bilateralFilter(enhanced, 3, 50, 50)
        
        return enhanced
    
    def stop(self):
        """Stop the camera thread"""
        self.running = False


def video_writer_thread():
    """Background thread for writing video frames (non-blocking)"""
    print("📹 Video writer thread started")
    frames_written = 0
    while True:
        try:
            # Wait for frames to write
            frame = video_write_queue.get(timeout=1)
            
            # Write frame if recorder is active
            if recording_state["video_writer"]:
                recording_state["video_writer"].write(frame)
                frames_written += 1
                if frames_written % 30 == 0:  # Log every 30 frames (~1 second)
                    print(f"📹 Writing frames... ({frames_written} frames written)")
            
        except queue.Empty:
            if frames_written > 0:
                frames_written = 0  # Reset counter when idle
            continue  # No frames to write, keep waiting
        except Exception as e:
            print(f"⚠️  Video write error: {e}")


def cleanup_old_videos():
    """Delete old videos, keep only the MAX_VIDEOS newest"""
    try:
        videos = sorted(VIDEOS_DIR.glob("*.mp4"), key=lambda p: p.stat().st_ctime, reverse=True)
        
        if len(videos) > MAX_VIDEOS:
            videos_to_delete = videos[MAX_VIDEOS:]
            for video in videos_to_delete:
                video.unlink()
                print(f"🗑️  Deleted old video: {video.name}")
            
            print(f"✅ Kept {min(len(videos), MAX_VIDEOS)} newest videos, deleted {len(videos_to_delete)} old ones")
    except Exception as e:
        print(f"⚠️  Error cleaning up videos: {e}")


def start_recording(frame_shape):
    """Start a new video recording"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"interaction_{timestamp}.mp4"
    filepath = VIDEOS_DIR / filename
    
    height, width = frame_shape[:2]
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    fps = 30.0
    
    recording_state["video_writer"] = cv2.VideoWriter(
        str(filepath), fourcc, fps, (width, height)
    )
    recording_state["current_filename"] = filename
    
    print(f"📹 Started recording: {filename}")


def stop_recording():
    """Stop and save the current video"""
    if recording_state["video_writer"]:
        # Wait for remaining frames to be written
        time.sleep(0.2)
        
        recording_state["video_writer"].release()
        print(f"💾 Saved video: {recording_state['current_filename']}")
        recording_state["video_writer"] = None
        recording_state["current_filename"] = None
        
        # Clear any remaining queued frames
        while not video_write_queue.empty():
            try:
                video_write_queue.get_nowait()
            except queue.Empty:
                break
        
        # Clean up old videos after saving
        cleanup_old_videos()


def check_recording_timeout():
    """Check if we should stop recording due to timeout"""
    if recording_state["is_recording"]:
        time_since_detection = time.time() - recording_state["last_detection_time"]
        if time_since_detection > COOLDOWN_SECONDS:
            recording_state["is_recording"] = False
            recording_state["both_detected"] = False
            stop_recording()
            print(f"⏱️  Recording stopped - {COOLDOWN_SECONDS}s timeout")


def load_model():
    """Load YOLOv8 model with optimizations"""
    global model
    print(f"⏳ Loading model: {MODEL_PATH}")
    model = YOLO(MODEL_PATH)
    
    # Warmup model for faster first inference
    print("🔥 Warming up model...")
    dummy_frame = np.zeros((640, 640, 3), dtype=np.uint8)
    model.predict(dummy_frame, verbose=False)
    
    print("✅ Model loaded and warmed up!")


def frame_to_base64(frame):
    """Convert frame to base64 JPEG (fast encoding)"""
    _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 75])
    return base64.b64encode(buffer).decode('utf-8')


@app.route('/esp32/frame', methods=['POST'])
def receive_esp32_frame():
    """Receive camera frame from ESP32-S3"""
    global use_esp32_camera
    
    try:
        # Get JPEG data from ESP32
        jpeg_data = request.data
        
        if len(jpeg_data) == 0:
            return jsonify({"error": "No image data received"}), 400
        
        # Decode JPEG to OpenCV format
        nparr = np.frombuffer(jpeg_data, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if frame is None:
            return jsonify({"error": "Failed to decode image"}), 400
        
        # Add frame to queue (non-blocking)
        try:
            esp32_frame_queue.put_nowait(frame)
        except queue.Full:
            # Queue full, skip this frame
            pass
        
        return jsonify({
            "success": True,
            "message": "Frame received",
            "frame_size": frame.shape,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        print(f"❌ Error receiving ESP32 frame: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/esp32/distance', methods=['POST'])
def receive_distance_data():
    """Receive BLE beacon distance from ESP32-S3"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No data received"}), 400
        
        distance = float(data.get('distance', 999.0))
        rssi = int(data.get('rssi', -100))
        beacon_mac = data.get('beacon_mac', 'unknown')
        
        # Update proximity state
        proximity_state['distance'] = distance
        proximity_state['rssi'] = rssi
        proximity_state['beacon_mac'] = beacon_mac
        proximity_state['last_update'] = time.time()
        
        # Check if beacon is close (<=1m) - using RSSI threshold is more reliable
        was_close = proximity_state['is_close']
        is_now_close = (distance <= 1.0) or (rssi >= -70)  # Use RSSI threshold or distance
        proximity_state['is_close'] = is_now_close
        
        print(f"📏 RSSI: {rssi} dBm, Distance: {distance:.2f}m, Close: {is_now_close}, Alert: {proximity_state['proximity_alert_active']}, Recording: {proximity_state['proximity_recording']}")
        
        # Handle proximity detection
        if is_now_close:
            # Beacon is close - activate alert
            proximity_state['proximity_alert_active'] = True
            
            # Start recording if not already recording
            if not proximity_state['proximity_recording']:
                if recording_state['latest_frame'] is not None:
                    proximity_state['proximity_recording'] = True
                    recording_state['is_recording'] = True
                    start_recording(recording_state['latest_frame'].shape)
                    print(f"🚨 PROXIMITY ALERT! Recording started - RSSI: {rssi} dBm, Distance: {distance:.2f}m")
                else:
                    print("⚠️  No frame available to start recording")
        else:
            # Beacon is far - deactivate alert and stop recording
            if proximity_state['proximity_alert_active']:
                print(f"📴 Beacon moved away - RSSI: {rssi} dBm, Distance: {distance:.2f}m")
                proximity_state['proximity_alert_active'] = False
            
            if proximity_state['proximity_recording']:
                proximity_state['proximity_recording'] = False
                recording_state['is_recording'] = False
                stop_recording()
                print(f"⏹️  Recording stopped - beacon beyond 1m")
        
        return jsonify({
            "success": True,
            "distance": distance,
            "rssi": rssi,
            "is_close": is_now_close,
            "alert_active": proximity_state['proximity_alert_active'],
            "recording": proximity_state['proximity_recording'],
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        print(f"❌ Error receiving distance data: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/esp32/enable', methods=['POST'])
def enable_esp32_camera():
    """Switch to ESP32-S3 camera mode"""
    global use_esp32_camera
    
    data = request.get_json() or {}
    enable = data.get('enable', True)
    
    use_esp32_camera = enable
    
    return jsonify({
        "success": True,
        "esp32_camera_enabled": use_esp32_camera,
        "message": "ESP32-S3 camera enabled" if enable else "Mac webcam enabled",
        "timestamp": datetime.now().isoformat()
    })


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "model_loaded": model is not None,
        "recording": recording_state["is_recording"],
        "camera_active": camera_thread.running if camera_thread else False,
        "camera_source": "ESP32-S3" if use_esp32_camera else "Mac Webcam",
        "timestamp": datetime.now().isoformat()
    })


@app.route('/stream/live', methods=['GET'])
def stream_live():
    """Get current frame with annotations (for live view) - optimized"""
    if recording_state["latest_annotated_frame"] is None:
        return jsonify({"error": "No frame available"}), 404
    
    # Fast JPEG encoding with lower quality for faster transmission
    frame_base64 = frame_to_base64(recording_state["latest_annotated_frame"])
    
    # Minimal response (remove unnecessary fields for speed)
    return jsonify({
        "frame": frame_base64,
        "detections": recording_state["detections"],
        "is_recording": recording_state["is_recording"],
        "current_video": recording_state["current_filename"],
        "proximity_alert": proximity_state["proximity_alert_active"],
        "beacon_distance": proximity_state["distance"],
        "timestamp": datetime.now().isoformat()
    })


@app.route('/proximity/status', methods=['GET'])
def get_proximity_status():
    """Get current proximity status"""
    time_since_update = time.time() - proximity_state["last_update"]
    return jsonify({
        "distance": proximity_state["distance"],
        "rssi": proximity_state["rssi"],
        "is_close": proximity_state["is_close"],
        "alert_active": proximity_state["proximity_alert_active"],
        "recording": proximity_state["proximity_recording"],
        "beacon_mac": proximity_state["beacon_mac"],
        "last_update": proximity_state["last_update"],
        "time_since_update": time_since_update,
        "has_frame": recording_state["latest_frame"] is not None,
        "timestamp": datetime.now().isoformat()
    })


@app.route('/stream/mjpeg', methods=['GET'])
def stream_mjpeg():
    """MJPEG video stream (alternative for continuous streaming)"""
    def generate():
        while True:
            if recording_state["latest_annotated_frame"] is not None:
                _, buffer = cv2.imencode('.jpg', recording_state["latest_annotated_frame"])
                frame_bytes = buffer.tobytes()
                
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            
            time.sleep(0.033)  # ~30 FPS
    
    return Response(generate(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/status', methods=['GET'])
def get_status():
    """Get current detection and recording status"""
    return jsonify({
        "is_recording": recording_state["is_recording"],
        "both_detected": recording_state["both_detected"],
        "current_video": recording_state["current_filename"],
        "detections": recording_state["detections"],
        "timestamp": datetime.now().isoformat()
    })


@app.route('/videos', methods=['GET'])
def get_videos():
    """Get list of all recorded videos"""
    videos = []
    for video_file in sorted(VIDEOS_DIR.glob('*.mp4'), key=lambda x: x.stat().st_ctime, reverse=True):
        videos.append({
            'filename': video_file.name,
            'size': video_file.stat().st_size,
            'created': datetime.fromtimestamp(video_file.stat().st_ctime).isoformat(),
            'url': f'/videos/{video_file.name}'
        })
    
    return jsonify({
        'videos': videos,
        'count': len(videos)
    })


# ESP32 MOTOR CONTROL ENDPOINTS - Commented out (see hardware_part/esp32_motor_control folder)
# Uncomment these and install pyserial to enable motor control via serial
# OR use HTTP requests to ESP32 web server (recommended)

# @app.route('/motor/control', methods=['POST'])
# def control_motor():
#     """Control ESP32 motor via commands from iOS app"""
#     global esp32_connection, ESP32_ENABLED
#     
#     try:
#         data = request.get_json()
#         command = data.get('command', '')  # 'ON' or 'OFF'
#         duration = data.get('duration', 0)  # Duration in seconds (optional)
#         
#         if not ESP32_ENABLED or esp32_connection is None:
#             return jsonify({
#                 'success': False,
#                 'message': 'ESP32 not connected',
#                 'esp32_enabled': ESP32_ENABLED
#             }), 503
#         
#         # Send command to ESP32
#         if command == 'ON':
#             esp32_connection.write(b'MOTOR_ON\n')
#             message = f'Motor turned ON'
#             if duration > 0:
#                 message += f' for {duration} seconds'
#         elif command == 'OFF':
#             esp32_connection.write(b'MOTOR_OFF\n')
#             message = 'Motor turned OFF'
#         elif command == 'TOGGLE':
#             esp32_connection.write(b'MOTOR_TOGGLE\n')
#             message = 'Motor toggled'
#         else:
#             return jsonify({
#                 'success': False,
#                 'message': f'Invalid command: {command}'
#             }), 400
#         
#         # Wait for ESP32 response (optional)
#         time.sleep(0.1)
#         response = ''
#         if esp32_connection.in_waiting > 0:
#             response = esp32_connection.readline().decode('utf-8').strip()
#         
#         print(f"🤖 Motor control: {command} - Response: {response}")
#         
#         return jsonify({
#             'success': True,
#             'message': message,
#             'command': command,
#             'esp32_response': response,
#             'timestamp': datetime.now().isoformat()
#         })
#         
#     except Exception as e:
#         print(f"❌ Motor control error: {e}")
#         return jsonify({
#             'success': False,
#             'message': str(e)
#         }), 500


# @app.route('/motor/status', methods=['GET'])
# def motor_status():
#     """Get ESP32 connection status"""
#     global esp32_connection, ESP32_ENABLED
#     
#     return jsonify({
#         'esp32_connected': ESP32_ENABLED,
#         'port': esp32_connection.port if esp32_connection else None,
#         'timestamp': datetime.now().isoformat()
#     })


@app.route('/videos/<filename>', methods=['GET'])
def get_video(filename):
    """Download a specific video file"""
    try:
        video_path = VIDEOS_DIR / filename
        
        if not video_path.exists():
            return jsonify({"error": "Video not found"}), 404
        
        return send_file(
            video_path,
            mimetype='video/mp4',
            as_attachment=False,
            download_name=filename
        )
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/videos/<filename>', methods=['DELETE'])
def delete_video(filename):
    """Delete a specific video file"""
    try:
        video_path = VIDEOS_DIR / filename
        
        if not video_path.exists():
            return jsonify({"error": "Video not found"}), 404
        
        video_path.unlink()
        return jsonify({"message": "Video deleted successfully"})
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/config', methods=['GET', 'POST'])
def config():
    """Get or update configuration"""
    global CONFIDENCE_THRESHOLD, COOLDOWN_SECONDS
    
    if request.method == 'POST':
        data = request.get_json()
        
        if 'confidence' in data:
            CONFIDENCE_THRESHOLD = float(data['confidence'])
        
        if 'cooldown' in data:
            COOLDOWN_SECONDS = float(data['cooldown'])
        
        return jsonify({
            "message": "Configuration updated",
            "confidence": CONFIDENCE_THRESHOLD,
            "cooldown": COOLDOWN_SECONDS
        })
    
    else:
        return jsonify({
            "confidence": CONFIDENCE_THRESHOLD,
            "cooldown": COOLDOWN_SECONDS
        })


# Global camera thread
camera_thread = None


def main():
    """Main entry point"""
    global camera_thread  # , arduino_connection, ARDUINO_ENABLED
    
    print("\n" + "="*70)
    print("  Streaming Backend Server - Hand-Pet Interaction Detector")
    print("="*70)
    
    # Load model
    load_model()
    
    # ARDUINO MOTOR CONTROL - Commented out (see arduino_motor_control folder)
    # Uncomment this section and install pyserial to enable Arduino motor control
    # try:
    #     print("🔌 Searching for Arduino...")
    #     ports = list(serial.tools.list_ports.comports())
    #     arduino_port = None
    #     
    #     for port in ports:
    #         if 'usbmodem' in port.device or 'usbserial' in port.device or 'Arduino' in port.description:
    #             arduino_port = port.device
    #             break
    #     
    #     if arduino_port:
    #         arduino_connection = serial.Serial(arduino_port, 9600, timeout=1)
    #         time.sleep(2)  # Wait for Arduino to reset
    #         ARDUINO_ENABLED = True
    #         print(f"✅ Arduino connected: {arduino_port}")
    #     else:
    #         print("⚠️  Arduino not found. Motor control disabled.")
    #         print("   Available ports:", [p.device for p in ports])
    # except Exception as e:
    #     print(f"⚠️  Arduino connection failed: {e}")
    #     print("   Motor control will be disabled")
    
    # Start video writer thread (daemon so it exits with main program)
    writer_thread = threading.Thread(target=video_writer_thread, daemon=True)
    writer_thread.start()
    
    # Start camera thread
    camera_thread = CameraThread()
    camera_thread.start()
    
    # Give camera time to initialize
    time.sleep(2)
    
    # Get local IP
    import socket
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    
    print("\n📱 iOS App Configuration:")
    print(f"   Server URL: http://{local_ip}:5001")
    print(f"   Live Stream: http://{local_ip}:5001/stream/live")
    print(f"   MJPEG Stream: http://{local_ip}:5001/stream/mjpeg")
    print(f"\n📂 PATHS:")
    print(f"   Model: {MODEL_PATH}")
    print(f"   Model exists: {MODEL_PATH.exists()}")
    print(f"   Videos dir: {VIDEOS_DIR.absolute()}")
    print(f"   Videos dir exists: {VIDEOS_DIR.exists()}")
    print(f"\n🎯 Settings:")
    print(f"   Confidence threshold: {CONFIDENCE_THRESHOLD}")
    print(f"   Recording cooldown: {COOLDOWN_SECONDS} seconds")
    print(f"   Camera: {'ESP32-S3' if use_esp32_camera else f'Webcam {CAMERA_ID}'}")
    print("\n🚀 Starting server...")
    print("="*70 + "\n")
    
    try:
        # Run Flask server
        app.run(
            host='0.0.0.0',
            port=5001,
            debug=False,
            threaded=True
        )
    finally:
        # Cleanup
        if camera_thread:
            camera_thread.stop()
        stop_recording()
        print("\n👋 Server stopped")


if __name__ == "__main__":
    main()
