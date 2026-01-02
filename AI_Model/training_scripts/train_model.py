"""
Model Training Script
Train YOLOv5/YOLOv8 model for hand-pet interaction detection
"""

import torch
import yaml
from pathlib import Path
import shutil
import os


def prepare_dataset(data_dir='data', output_dir='data/yolo_dataset'):
    """
    Prepare dataset in YOLO format
    
    Expected structure:
    data/
      images/
        train/
        val/
        test/
      labels/
        train/
        val/
        test/
    """
    data_path = Path(data_dir)
    output_path = Path(output_dir)
    
    # Create directories
    for split in ['train', 'val', 'test']:
        (output_path / 'images' / split).mkdir(parents=True, exist_ok=True)
        (output_path / 'labels' / split).mkdir(parents=True, exist_ok=True)
    
    print(f"Dataset prepared at: {output_path}")
    return output_path


def create_data_yaml(dataset_path, output_file='data/dataset.yaml'):
    """Create YOLO dataset configuration file"""
    
    data_config = {
        'path': str(Path(dataset_path).absolute()),
        'train': 'images/train',
        'val': 'images/val',
        'test': 'images/test',
        'nc': 2,  # Number of classes (hand, cat only)
        'names': ['hand', 'cat']
    }
    
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        yaml.dump(data_config, f, default_flow_style=False)
    
    print(f"Dataset config created: {output_path}")
    return str(output_path)


def train_yolov5(data_yaml, epochs=100, batch_size=16, img_size=640, 
                 model='yolov5s', device='0', project='runs/train', name='exp'):
    """
    Train YOLOv5 model
    
    Args:
        data_yaml: Path to dataset YAML file
        epochs: Number of training epochs
        batch_size: Batch size
        img_size: Image size
        model: Model architecture (yolov5s, yolov5m, yolov5l)
        device: GPU device (0, cpu)
        project: Project directory
        name: Experiment name
    """
    print("="*50)
    print("Starting YOLOv5 Training")
    print("="*50)
    
    # Clone YOLOv5 if not exists
    yolov5_path = Path('yolov5')
    if not yolov5_path.exists():
        print("Cloning YOLOv5 repository...")
        os.system('git clone https://github.com/ultralytics/yolov5')
        os.system('cd yolov5 && pip install -r requirements.txt')
    
    # Training command
    train_cmd = f"""
    cd yolov5 && python train.py \
        --img {img_size} \
        --batch {batch_size} \
        --epochs {epochs} \
        --data ../{data_yaml} \
        --weights {model}.pt \
        --device {device} \
        --project ../{project} \
        --name {name} \
        --cache
    """
    
    print(f"Training command: {train_cmd}")
    os.system(train_cmd)
    
    print("="*50)
    print("Training completed!")
    print(f"Results saved to: {project}/{name}")
    print("="*50)


def train_yolov8(data_yaml, epochs=100, batch_size=16, img_size=640, 
                 model='yolov8n', device='0', project='runs/train', name='exp'):
    """
    Train YOLOv8 model using Ultralytics
    
    Args:
        data_yaml: Path to dataset YAML file
        epochs: Number of training epochs
        batch_size: Batch size
        img_size: Image size
        model: Model architecture (yolov8n, yolov8s, yolov8m)
        device: GPU device (0, cpu)
        project: Project directory
        name: Experiment name
    """
    try:
        from ultralytics import YOLO
        
        print("="*50)
        print("Starting YOLOv8 Training")
        print("="*50)
        
        # Load model
        model = YOLO(f"{model}.pt")
        
        # Train model
        results = model.train(
            data=data_yaml,
            epochs=epochs,
            imgsz=img_size,
            batch=batch_size,
            device=device,
            project=project,
            name=name
        )
        
        print("="*50)
        print("Training completed!")
        print(f"Results saved to: {project}/{name}")
        print("="*50)
        
        return results
        
    except ImportError:
        print("Ultralytics not installed. Install with: pip install ultralytics")
        print("Falling back to YOLOv5...")
        train_yolov5(data_yaml, epochs, batch_size, img_size, 'yolov5s', 
                    device, project, name)


def optimize_for_jetson(model_path, output_path='models/best_fp16.pt'):
    """
    Optimize model for Jetson Nano (FP16 precision)
    
    Args:
        model_path: Path to trained model
        output_path: Output path for optimized model
    """
    print("="*50)
    print("Optimizing model for Jetson Nano")
    print("="*50)
    
    try:
        # Load model
        model = torch.load(model_path, map_location='cpu')
        
        # Convert to FP16
        if isinstance(model, dict):
            if 'model' in model:
                model['model'] = model['model'].half()
        else:
            model = model.half()
        
        # Save optimized model
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        torch.save(model, output_path)
        
        print(f"Optimized model saved to: {output_path}")
        print("="*50)
        
    except Exception as e:
        print(f"Error optimizing model: {e}")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Train Hand-Pet Interaction Detector')
    parser.add_argument('--data-dir', type=str, default='data/yolo_dataset',
                       help='Dataset directory')
    parser.add_argument('--epochs', type=int, default=100,
                       help='Number of training epochs')
    parser.add_argument('--batch-size', type=int, default=16,
                       help='Batch size')
    parser.add_argument('--img-size', type=int, default=640,
                       help='Image size')
    parser.add_argument('--model', type=str, default='yolov8n',
                       choices=['yolov5s', 'yolov5m', 'yolov5l', 'yolov8n', 'yolov8s', 'yolov8m'],
                       help='Model architecture')
    parser.add_argument('--device', type=str, default='0',
                       help='Device (0, cpu)')
    parser.add_argument('--project', type=str, default='runs/train',
                       help='Project directory')
    parser.add_argument('--name', type=str, default='exp',
                       help='Experiment name')
    parser.add_argument('--optimize', action='store_true',
                       help='Optimize model for Jetson Nano after training')
    
    args = parser.parse_args()
    
    # Prepare dataset
    dataset_path = Path(args.data_dir)
    if not dataset_path.exists():
        print(f"Dataset not found at {dataset_path}")
        print("Please prepare your dataset first")
        return
    
    # Create dataset YAML
    data_yaml = create_data_yaml(dataset_path)
    
    # Train model
    if 'yolov8' in args.model:
        train_yolov8(
            data_yaml=data_yaml,
            epochs=args.epochs,
            batch_size=args.batch_size,
            img_size=args.img_size,
            model=args.model,
            device=args.device,
            project=args.project,
            name=args.name
        )
    else:
        train_yolov5(
            data_yaml=data_yaml,
            epochs=args.epochs,
            batch_size=args.batch_size,
            img_size=args.img_size,
            model=args.model,
            device=args.device,
            project=args.project,
            name=args.name
        )
    
    # Optimize for Jetson Nano
    if args.optimize:
        model_path = Path(args.project) / args.name / 'weights' / 'best.pt'
        if model_path.exists():
            optimize_for_jetson(str(model_path))


if __name__ == '__main__':
    main()
