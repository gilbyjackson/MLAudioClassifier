"""
Utility script to validate label mapping against trained model.

Usage:
    python scripts/validate_mapping.py
"""

import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from classifier import model
import keras


def main():
    """Validate label mapping."""
    model_path = Path('models/model1.keras')
    mapping_path = Path('models/label_mapping.json')
    
    if not model_path.exists():
        print(f"❌ Model not found: {model_path}")
        print("   Looking for model files...")
        model_dir = Path('models')
        if model_dir.exists():
            models = list(model_dir.glob('*.keras'))
            if models:
                print("   Found models:")
                for m in models:
                    print(f"     - {m}")
                model_path = models[0]
                print(f"   Using: {model_path}")
            else:
                print("   No .keras files found in models/")
                return 1
        else:
            print("   models/ directory not found")
            return 1
    
    print(f"\nLoading model: {model_path}")
    keras_model = keras.models.load_model(model_path)
    
    print(f"Model output dimension: {keras_model.output_shape[-1]}")
    
    if not mapping_path.exists():
        print(f"\n⚠️  Label mapping not found: {mapping_path}")
        print(f"   Creating stub file...")
        
        stub_path = Path('models/label_mapping_stub.json')
        model.save_label_mapping_stub(
            stub_path,
            keras_model.output_shape[-1]
        )
        
        print(f"\n✓ Created stub: {stub_path}")
        print(f"  Please edit this file to provide canonical class names.")
        print(f"  Then rename to: {mapping_path}")
        
        return 0
    
    print(f"\nValidating: {mapping_path}")
    valid = model.validate_label_mapping(mapping_path, keras_model)
    
    if valid:
        # Load and display
        import json
        labels = json.loads(mapping_path.read_text())
        print(f"\nLabel mapping ({len(labels)} classes):")
        for i, label in enumerate(labels):
            print(f"  {i:2d}: {label}")
    
    return 0 if valid else 1


if __name__ == '__main__':
    sys.exit(main())
