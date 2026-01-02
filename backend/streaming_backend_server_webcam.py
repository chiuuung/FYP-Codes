"""
Streaming Backend Server for Hand-Pet Interaction Detection
- Captures video from Mac/Jetson WEBCAM (not ESP32)
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
import time

app = Flask(__name__)
CORS(app)

# Configuration
SCRIPT_DIR = Path(__file__).parent.parent.parent.absolute()  # Go up 3 levels to project root
MODEL_PATH = SCRIPT_DIR / "AI_Model/weights/best.pt"
VIDEOS_DIR = SCRIPT_DIR / "recorded_videos"
VIDEOS_DIR.mkdir(exist_ok=True)

# Global variables
model = None
camera_capture = None

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

# Detection parameters
CONFIDENCE_THRESHOLD = 0.25
COOLDOWN_SECONDS = 2
CAMERA_ID = 0  # 0 for Mac webcam, 1 for external USB camera
MAX_VIDEOS = 10  # Keep only the 10 newest videos


class CameraThread(threading.Thread):
    """Handles camera capture and detection in separate thread"""
    
    def __init__(self):
        super().__init__(daemon=True)
        self.running = False
        self.camera = None
    
    def run(self):
        """Main camera loop - uses Mac webcam"""
        print("📹 Starting camera thread...")
        
        # Open Mac webcam
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
            
            # Update recording state
            both_present = has_human and has_cat
            
            if both_present:
                recording_state["last_detection_time"] = time.time()
                recording_state["both_detected"] = True
                
                if not recording_state["is_recording"]:
                    recording_state["is_recording"] = True
                    start_recording(frame.shape)
                    print("🔴 Recording STARTED - Cat and Human detected!")
            
            # Check for timeout
            check_recording_timeout()
            
            # Save clean frame for recording
            if recording_state["is_recording"] and recording_state["video_writer"]:
                recording_state["video_writer"].write(frame)
            
            # Create annotated frame for display
            annotated_frame = result.plot()
            
            # Store latest frames
            recording_state["latest_frame"] = frame.copy()
            recording_state["latest_annotated_frame"] = annotated_frame.copy()
            recording_state["detections"] = detections
            
            # Small delay to control frame rate
            time.sleep(0.033)  # ~30 FPS
        
        # Cleanup
        if self.camera:
            self.camera.release()
        print("📹 Camera thread stopped")
    
    def stop(self):
        """Stop the camera thread"""
        self.running = False


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
        recording_state["video_writer"].release()
        print(f"💾 Saved video: {recording_state['current_filename']}")
        recording_state["video_writer"] = None
        recording_state["current_filename"] = None
        
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
    """Load YOLOv8 model"""
    global model
    print(f"⏳ Loading model: {MODEL_PATH}")
    model = YOLO(MODEL_PATH)
    print("✅ Model loaded successfully!")


def frame_to_base64(frame):
    """Convert frame to base64 JPEG"""
    _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
    return base64.b64encode(buffer).decode('utf-8')


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "model_loaded": model is not None,
        "recording": recording_state["is_recording"],
        "camera_active": camera_thread.running if camera_thread else False,
        "camera_source": "Mac Webcam",
        "timestamp": datetime.now().isoformat()
    })


@app.route('/stream/live', methods=['GET'])
def stream_live():
    """Get current frame with annotations (for live view)"""
    if recording_state["latest_annotated_frame"] is None:
        return jsonify({"error": "No frame available"}), 404
    
    frame_base64 = frame_to_base64(recording_state["latest_annotated_frame"])
    
    return jsonify({
        "frame": frame_base64,
        "detections": recording_state["detections"],
        "is_recording": recording_state["is_recording"],
        "current_video": recording_state["current_filename"],
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
def list_videos():
    """List all recorded videos"""
    try:
        videos = []
        for video_file in sorted(VIDEOS_DIR.glob("*.mp4"), reverse=True):
            stat = video_file.stat()
            videos.append({
                "filename": video_file.name,
                "size": stat.st_size,
                "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "url": f"/videos/{video_file.name}"
            })
        
        return jsonify({
            "videos": videos,
            "count": len(videos)
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


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
    global camera_thread
    
    print("\n" + "="*70)
    print("  Streaming Backend Server - Mac Webcam Version")
    print("="*70)
    
    # Load model
    load_model()
    
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
    print(f"\n📂 Videos will be saved to: {VIDEOS_DIR.absolute()}")
    print(f"🎯 Confidence threshold: {CONFIDENCE_THRESHOLD}")
    print(f"⏱️  Recording cooldown: {COOLDOWN_SECONDS} seconds")
    print(f"📹 Camera: Mac Webcam (ID: {CAMERA_ID})")
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
