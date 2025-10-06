"""
Extract label list from training data JSON.

This script helps recover the original label ordering used during training.

Usage:
    python scripts/extract_training_labels.py
"""

import json
import sys
from pathlib import Path


def extract_from_mfcc_json(json_path: Path):
    """Try to extract labels from MFCC training data."""
    print(f"Attempting to extract labels from: {json_path}")
    
    # Read first few KB to find metadata
    with open(json_path, 'r') as f:
        # Read first 50KB
        head = f.read(50000)
    
    # Try to parse as partial JSON
    try:
        # Find first complete object
        data = json.loads(head)
        
        # Look for label-related keys
        if 'labels' in data:
            return data['labels']
        if 'classes' in data:
            return data['classes']
        if 'label_mapping' in data:
            return data['label_mapping']
        if 'mapping' in data:
            return data['mapping']
        
        # Check for label_to_index
        if 'label_to_index' in data:
            # Reverse mapping
            index_to_label = {v: k for k, v in data['label_to_index'].items()}
            return [index_to_label[i] for i in sorted(index_to_label.keys())]
        
    except json.JSONDecodeError:
        pass
    
    print("Could not find label metadata in JSON header")
    return None


def extract_from_training_dirs():
    """Extract labels from TrainingData directory structure."""
    train_dir = Path('TrainingData/AudioSamples')
    
    if not train_dir.exists():
        print(f"Training directory not found: {train_dir}")
        return None
    
    # Get subdirectories (class folders)
    class_dirs = [d.name for d in train_dir.iterdir() if d.is_dir()]
    
    if not class_dirs:
        print("No class subdirectories found")
        return None
    
    # Sort alphabetically (common pattern)
    class_dirs.sort()
    
    return class_dirs


def main():
    """Main extraction logic."""
    print("Extracting training label ordering...\n")
    
    # Method 1: From MFCC JSON
    mfcc_path = Path('data/mfcc_train_data.json')
    if mfcc_path.exists():
        labels = extract_from_mfcc_json(mfcc_path)
        if labels:
            print("\n✓ Extracted from training data JSON:")
            for i, label in enumerate(labels):
                print(f"  {i:2d}: {label}")
            
            # Offer to save
            output_path = Path('models/label_mapping.json')
            if not output_path.exists():
                confirm = input(f"\nSave to {output_path}? [y/N]: ")
                if confirm.lower() == 'y':
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                    with output_path.open('w') as f:
                        json.dump(labels, f, indent=2)
                    print(f"✓ Saved to {output_path}")
            
            return 0
    
    # Method 2: From directory structure
    print("Trying to extract from directory structure...")
    labels = extract_from_training_dirs()
    
    if labels:
        print(f"\n✓ Found {len(labels)} class directories:")
        for i, label in enumerate(labels):
            print(f"  {i:2d}: {label}")
        
        print("\n⚠️  WARNING: This assumes alphabetical ordering was used during training!")
        print("   Verify this matches the original training script logic.")
        
        # Offer to save
        output_path = Path('models/label_mapping_from_dirs.json')
        confirm = input(f"\nSave to {output_path}? [y/N]: ")
        if confirm.lower() == 'y':
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with output_path.open('w') as f:
                json.dump(labels, f, indent=2)
            print(f"✓ Saved to {output_path}")
            print(f"  Review and rename to label_mapping.json if correct")
        
        return 0
    
    print("\n❌ Could not extract label ordering")
    print("   Please manually create models/label_mapping.json")
    
    return 1


if __name__ == '__main__':
    sys.exit(main())
