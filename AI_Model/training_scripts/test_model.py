"""
Test the trained model on test images or webcam
"""
import cv2
from ultralytics import YOLO
import argparse
from pathlib import Path

def test_on_images(model_path, image_dir, conf_threshold=0.25):
    """Test model on directory of images"""
    model = YOLO(model_path)
    image_dir = Path(image_dir)
    
    # Get all images
    images = list(image_dir.glob("*.jpg")) + list(image_dir.glob("*.jpeg")) + list(image_dir.glob("*.png")) + list(image_dir.glob("*.webp"))
    
    print(f"Testing on {len(images)} images with confidence threshold: {conf_threshold}")
    print("Press any key to see next image, 'q' to quit")
    
    # Create resizable window
    cv2.namedWindow('Test Results', cv2.WINDOW_NORMAL)
    cv2.resizeWindow('Test Results', 1200, 800)
    
    for img_path in images:
        # Run inference with custom confidence threshold
        results = model(str(img_path), conf=conf_threshold, iou=0.45)
        
        # Get the annotated image
        annotated = results[0].plot()
        
        # Resize to fit window while maintaining aspect ratio
        h, w = annotated.shape[:2]
        max_width = 1200
        max_height = 800
        
        scale = min(max_width / w, max_height / h, 1.0)
        new_w = int(w * scale)
        new_h = int(h * scale)
        
        if scale < 1.0:
            resized = cv2.resize(annotated, (new_w, new_h), interpolation=cv2.INTER_AREA)
        else:
            resized = annotated
        
        # Display
        cv2.imshow('Test Results', resized)
        key = cv2.waitKey(0) & 0xFF
        
        if key == ord('q'):
            break
    
    cv2.destroyAllWindows()
    print("Testing complete!")

def test_on_webcam(model_path, camera_id=0):
    """Test model on webcam"""
    model = YOLO(model_path)
    cap = cv2.VideoCapture(camera_id)
    
    if not cap.isOpened():
        print(f"Error: Could not open camera {camera_id}")
        return
    
    print("Press 'q' to quit")
    
    # Create resizable window
    cv2.namedWindow('Webcam Test', cv2.WINDOW_NORMAL)
    cv2.resizeWindow('Webcam Test', 1200, 800)
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # Run inference with lower confidence to detect more objects
        results = model(frame, conf=0.25, iou=0.45)
        
        # Get annotated frame
        annotated = results[0].plot()
        
        # Display
        cv2.imshow('Webcam Test', annotated)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()
    print("Webcam test complete!")

def test_on_video(model_path, video_path):
    """Test model on video file"""
    model = YOLO(model_path)
    cap = cv2.VideoCapture(video_path)
    
    if not cap.isOpened():
        print(f"Error: Could not open video {video_path}")
        return
    
    print("Press 'q' to quit")
    
    # Create resizable window
    cv2.namedWindow('Video Test', cv2.WINDOW_NORMAL)
    cv2.resizeWindow('Video Test', 1200, 800)
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # Run inference
        results = model(frame)
        
        # Get annotated frame
        annotated = results[0].plot()
        
        # Display
        cv2.imshow('Video Test', annotated)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()
    print("Video test complete!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Test trained model')
    parser.add_argument('--model', type=str, 
                       default='C:/Users/ngtszch/Documents/FYP/runs/train/exp/weights/best.pt',
                       help='Path to trained model')
    parser.add_argument('--source', type=str, default='webcam',
                       help='Test source: "webcam", "images", or path to video/image directory')
    parser.add_argument('--camera-id', type=int, default=0,
                       help='Camera ID for webcam (default: 0)')
    parser.add_argument('--conf', type=float, default=0.25,
                       help='Confidence threshold for detection (default: 0.25)')
    
    args = parser.parse_args()
    
    print("=" * 50)
    print("Model Testing")
    print("=" * 50)
    print(f"Model: {args.model}")
    print(f"Source: {args.source}")
    print(f"Confidence: {args.conf}")
    print("=" * 50)
    
    if args.source == 'webcam':
        test_on_webcam(args.model, args.camera_id)
    elif args.source == 'images':
        image_dir = Path('data/yolo_dataset/images/test')
        test_on_images(args.model, image_dir, args.conf)
    elif Path(args.source).is_dir():
        test_on_images(args.model, args.source, args.conf)
    elif Path(args.source).is_file():
        test_on_video(args.model, args.source)
    else:
        print(f"Error: Invalid source '{args.source}'")
        print("Use: 'webcam', 'images', or path to video/directory")
