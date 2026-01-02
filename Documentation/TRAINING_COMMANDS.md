# YOLOv8s Training Commands and Code

## Table of Contents
1. [Environment Setup](#environment-setup)
2. [Training Commands](#training-commands)
3. [Training Script](#training-script)
4. [Resume Training](#resume-training)
5. [Validation and Testing](#validation-and-testing)

---

## Environment Setup

### 1. Install Required Dependencies

```bash
# Install Ultralytics YOLOv8
pip install ultralytics

# Install additional dependencies
pip install opencv-python numpy matplotlib pillow pyyaml torch torchvision
```

### 2. Verify Installation

```bash
# Check YOLOv8 installation
python -c "from ultralytics import YOLO; print('YOLOv8 installed successfully')"

# Check CUDA availability (for GPU training)
python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}')"
```

---

## Training Commands

### Method 1: Direct Command Line (Quick Start)

**Basic Training:**
```bash
# Navigate to project directory
cd /Users/tszchiung/Desktop/FYP-Codes

# Start training with YOLOv8s
python -c "from ultralytics import YOLO; model = YOLO('yolov8s.pt'); model.train(data='Dataset/expanded_data.yaml', epochs=150, batch=8, imgsz=640, device='cpu', project='AI_Model/runs/best_accuracy', name='yolov8s_massive')"
```

**Training with All Hyperparameters (Exact Configuration Used):**
```bash
python -c "from ultralytics import YOLO; \
model = YOLO('yolov8s.pt'); \
model.train(\
    data='data/expanded_dataset/data.yaml', \
    epochs=150, \
    batch=8, \
    imgsz=640, \
    device='cpu', \
    project='runs/best_accuracy', \
    name='yolov8s_massive', \
    optimizer='Adam', \
    lr0=0.001, \
    lrf=0.01, \
    momentum=0.937, \
    weight_decay=0.0005, \
    warmup_epochs=3.0, \
    patience=30, \
    save=True, \
    pretrained=True, \
    verbose=True, \
    plots=True, \
    val=True\
)"
```

### Method 2: Using Training Script

**Run the existing training script:**
```bash
# Navigate to project directory
cd /Users/tszchiung/Desktop/FYP-Codes/AI_Model/training_scripts

# Run training script with arguments
python train_model.py \
    --data-dir ../../Dataset \
    --epochs 150 \
    --batch-size 8 \
    --img-size 640 \
    --model yolov8s \
    --device cpu \
    --project ../runs/best_accuracy \
    --name yolov8s_massive
```

---

## Training Script

### Complete Training Script (`train_yolov8s.py`)

Create this file in your project directory:

```python
"""
YOLOv8s Training Script for Hand-Pet Interaction Detection
Exact configuration used to train the 77% mAP50 model
"""

from ultralytics import YOLO
import torch
from pathlib import Path

def train_yolov8s():
    """
    Train YOLOv8s model with exact hyperparameters from args.yaml
    """
    
    print("="*70)
    print("YOLOv8s Training - Hand-Pet Interaction Detection")
    print("="*70)
    
    # Check device
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    print(f"\n🖥️  Training Device: {device}")
    if device == 'cpu':
        print("⚠️  Warning: Training on CPU will be slow. GPU recommended.")
    
    # Dataset configuration
    data_yaml = 'data/expanded_dataset/data.yaml'
    
    # Verify dataset exists
    if not Path(data_yaml).exists():
        print(f"\n❌ Error: Dataset configuration not found at {data_yaml}")
        print("Please ensure your dataset is properly set up.")
        return
    
    print(f"📊 Dataset: {data_yaml}")
    
    # Load pretrained YOLOv8s model
    print("\n📥 Loading YOLOv8s pretrained model...")
    model = YOLO('yolov8s.pt')
    print("✅ Model loaded successfully")
    
    # Training configuration (exact settings from args.yaml)
    print("\n🎯 Training Configuration:")
    training_args = {
        'data': data_yaml,
        'epochs': 150,
        'batch': 8,
        'imgsz': 640,
        'device': device,
        'project': 'runs/best_accuracy',
        'name': 'yolov8s_massive',
        
        # Optimizer settings
        'optimizer': 'Adam',
        'lr0': 0.001,              # Initial learning rate
        'lrf': 0.01,               # Final learning rate factor
        'momentum': 0.937,
        'weight_decay': 0.0005,
        'warmup_epochs': 3.0,
        'warmup_momentum': 0.8,
        'warmup_bias_lr': 0.1,
        
        # Loss weights
        'box': 1.5,                # Box loss weight
        'cls': 2.5,                # Classification loss weight
        'dfl': 1.5,                # DFL loss weight
        
        # Data augmentation
        'hsv_h': 0.01,             # HSV-Hue augmentation
        'hsv_s': 0.4,              # HSV-Saturation augmentation
        'hsv_v': 0.3,              # HSV-Value augmentation
        'degrees': 10.0,           # Rotation
        'translate': 0.1,          # Translation
        'scale': 0.3,              # Scaling
        'shear': 2.0,              # Shear
        'perspective': 0.0002,     # Perspective
        'flipud': 0.0,             # Vertical flip
        'fliplr': 0.5,             # Horizontal flip
        'mosaic': 0.5,             # Mosaic augmentation
        'mixup': 0.0,              # MixUp
        'copy_paste': 0.0,         # Copy-paste
        'auto_augment': 'randaugment',
        'erasing': 0.4,            # Random erasing
        
        # Training settings
        'patience': 30,            # Early stopping patience
        'save': True,
        'save_period': -1,
        'cache': False,
        'pretrained': True,
        'verbose': True,
        'seed': 0,
        'deterministic': True,
        'single_cls': False,
        'rect': False,
        'cos_lr': False,
        'close_mosaic': 10,        # Close mosaic in final epochs
        'amp': True,               # Mixed precision training
        'fraction': 1.0,
        'profile': False,
        'freeze': None,
        'multi_scale': False,
        
        # Validation settings
        'val': True,
        'split': 'val',
        'save_json': False,
        'iou': 0.7,
        'max_det': 300,
        'plots': True,
        'show_labels': True,
        'show_conf': True,
        'show_boxes': True,
        'visualize': False,
        'augment': True,
    }
    
    # Print key parameters
    print(f"  Epochs: {training_args['epochs']}")
    print(f"  Batch Size: {training_args['batch']}")
    print(f"  Image Size: {training_args['imgsz']}x{training_args['imgsz']}")
    print(f"  Optimizer: {training_args['optimizer']}")
    print(f"  Learning Rate: {training_args['lr0']} → {training_args['lr0'] * training_args['lrf']}")
    print(f"  Early Stopping Patience: {training_args['patience']} epochs")
    
    # Start training
    print("\n🚀 Starting training...")
    print("="*70)
    
    try:
        results = model.train(**training_args)
        
        print("\n" + "="*70)
        print("✅ Training completed successfully!")
        print("="*70)
        print(f"\n📁 Results saved to: runs/best_accuracy/yolov8s_massive")
        print(f"📊 Best model: runs/best_accuracy/yolov8s_massive/weights/best.pt")
        print(f"📊 Last checkpoint: runs/best_accuracy/yolov8s_massive/weights/last.pt")
        print(f"📈 Training curves: runs/best_accuracy/yolov8s_massive/results.csv")
        
        return results
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Training interrupted by user")
        print("💾 Progress saved. You can resume training using the command in TRAINING_COMMANDS.md")
        
    except Exception as e:
        print(f"\n\n❌ Training failed with error:")
        print(f"   {str(e)}")
        print("\n🔍 Troubleshooting tips:")
        print("   1. Check if dataset path is correct")
        print("   2. Ensure enough disk space available")
        print("   3. Verify all dependencies are installed")
        print("   4. Try reducing batch size if out of memory")


if __name__ == '__main__':
    train_yolov8s()
```

**Save this script as `train_yolov8s.py` and run:**
```bash
python train_yolov8s.py
```

---

## Resume Training

### Resume from Last Checkpoint

**If training was interrupted, resume from where it stopped:**

```bash
# Resume using last.pt checkpoint
python -c "from ultralytics import YOLO; \
model = YOLO('runs/best_accuracy/yolov8s_massive/weights/last.pt'); \
model.train(resume=True)"
```

**This is the exact command you used to resume training (from your screenshot):**
```bash
cd C:\Users\ngtszch\Documents\FYP\hand-pet-interaction-detector
python.exe -c "from ultralytics import YOLO; model = YOLO('runs/best_accuracy/yolov8s_massive/weights/last.pt'); model.train(resume=True)"
```

### Resume with Modified Settings

```bash
# Resume but change device to GPU
python -c "from ultralytics import YOLO; \
model = YOLO('runs/best_accuracy/yolov8s_massive/weights/last.pt'); \
model.train(resume=True, device='cuda')"
```

---

## Validation and Testing

### Validate Trained Model

**Run validation on validation set:**
```bash
python -c "from ultralytics import YOLO; \
model = YOLO('runs/best_accuracy/yolov8s_massive/weights/best.pt'); \
results = model.val(data='data/expanded_dataset/data.yaml')"
```

### Test on Custom Images

**Test model on test images:**
```bash
python -c "from ultralytics import YOLO; \
model = YOLO('runs/best_accuracy/yolov8s_massive/weights/best.pt'); \
results = model.predict(source='data/expanded_dataset/test/images', save=True)"
```

### View Training Results

**Generate and view training plots:**
```python
from ultralytics import YOLO
import matplotlib.pyplot as plt

# Load trained model
model = YOLO('runs/best_accuracy/yolov8s_massive/weights/best.pt')

# Print model info
model.info()

# Results are automatically saved to:
# runs/best_accuracy/yolov8s_massive/results.csv
# runs/best_accuracy/yolov8s_massive/results.png
```

---

## Quick Reference Commands

### Start Fresh Training
```bash
python train_yolov8s.py
```

### Resume Training
```bash
python -c "from ultralytics import YOLO; model = YOLO('runs/best_accuracy/yolov8s_massive/weights/last.pt'); model.train(resume=True)"
```

### Validate Model
```bash
python -c "from ultralytics import YOLO; model = YOLO('runs/best_accuracy/yolov8s_massive/weights/best.pt'); model.val()"
```

### Test Model
```bash
python -c "from ultralytics import YOLO; model = YOLO('runs/best_accuracy/yolov8s_massive/weights/best.pt'); model.predict(source='test_image.jpg', save=True)"
```

---

## Training Output Files

After training, you'll find these files in `runs/best_accuracy/yolov8s_massive/`:

```
runs/best_accuracy/yolov8s_massive/
├── weights/
│   ├── best.pt              # Best model (highest mAP)
│   └── last.pt              # Last checkpoint
├── args.yaml                # Training configuration
├── results.csv              # Training metrics (epoch-by-epoch)
├── results.png              # Training curves visualization
├── confusion_matrix.png     # Confusion matrix
├── F1_curve.png            # F1 score curve
├── P_curve.png             # Precision curve
├── R_curve.png             # Recall curve
├── PR_curve.png            # Precision-Recall curve
└── val_batch*.jpg          # Validation batch predictions
```

---

## Troubleshooting

### Out of Memory Error
```bash
# Reduce batch size
python train_yolov8s.py  # Edit batch=4 in script
```

### Slow Training on CPU
```bash
# Use GPU if available
python -c "from ultralytics import YOLO; model = YOLO('yolov8s.pt'); model.train(data='data/expanded_dataset/data.yaml', epochs=150, batch=8, device='cuda')"
```

### Dataset Not Found
```bash
# Verify dataset path
ls data/expanded_dataset/data.yaml
ls data/expanded_dataset/train/images/
ls data/expanded_dataset/train/labels/
```

### Resume Training from Specific Epoch
```bash
# Use last.pt to resume from where you stopped
python -c "from ultralytics import YOLO; model = YOLO('runs/best_accuracy/yolov8s_massive/weights/last.pt'); model.train(resume=True)"
```

---

## Additional Notes

- **Training Time**: Approximately 30 minutes per epoch (based on actual training)
- **Total Training Time**: **4,500 minutes (75 hours / ~3.1 days)** for 150 epochs
  - Calculation: 30 minutes/epoch × 150 epochs = 4,500 minutes
  - Equivalent to: 75 hours or approximately 3 days of continuous training
- **Disk Space**: Requires ~5-10GB for checkpoints and results
- **RAM Usage**: Minimum 8GB recommended, 16GB preferred
- **Hardware Used**: CPU-based training (as configured in args.yaml)

---

**For your FYP report, use the commands and code from this document to demonstrate your training methodology.** ✅
