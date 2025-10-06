"""
Model loading, label mapping, and calibration utilities.
"""

import json
from pathlib import Path
from typing import List, Optional, Dict
import keras
import numpy as np


def load_model(model_path: Path) -> keras.Model:
    """
    Load Keras model from file.
    
    Args:
        model_path: Path to .keras model file
        
    Returns:
        Loaded Keras model
    """
    print(f"Loading model: {model_path}")
    return keras.models.load_model(model_path)


def load_latest_model(model_dir: Path, pattern: str = 'model*.keras') -> keras.Model:
    """
    Load most recently modified model matching pattern.
    
    Args:
        model_dir: Directory containing models
        pattern: Glob pattern for model files
        
    Returns:
        Loaded Keras model
    """
    candidates = sorted(model_dir.glob(pattern))
    
    if not candidates:
        # Fallback: any .keras file
        candidates = sorted(model_dir.glob('*.keras'))
    
    if not candidates:
        raise FileNotFoundError(f"No model files found in {model_dir}")
    
    # Sort by modification time, newest first
    candidates = sorted(candidates, key=lambda p: p.stat().st_mtime, reverse=True)
    
    return load_model(candidates[0])


def load_label_mapping(
    mapping_file: Optional[Path],
    model: keras.Model,
    fallback_labels: Optional[List[str]] = None
) -> List[str]:
    """
    Load label mapping with fallback logic.
    
    Priority:
    1. Explicit mapping file (if exists and length matches)
    2. Fallback labels (if length matches)
    3. Generic class_<idx> labels
    
    Args:
        mapping_file: Path to label_mapping.json
        model: Keras model (to check output dimension)
        fallback_labels: Optional fallback label list
        
    Returns:
        List of label names matching model output dimension
    """
    out_dim = model.output_shape[-1]
    
    # Try explicit mapping file
    if mapping_file and mapping_file.exists():
        try:
            data = json.loads(mapping_file.read_text())
            if isinstance(data, list) and len(data) == out_dim:
                print(f"✓ Using label mapping from {mapping_file}")
                return data
            else:
                print(f"⚠️  Label mapping length mismatch: {len(data)} vs {out_dim}")
        except Exception as e:
            print(f"⚠️  Failed to load label mapping: {e}")
    
    # Try fallback labels
    if fallback_labels and len(fallback_labels) == out_dim:
        print(f"✓ Using fallback labels (length={out_dim})")
        return fallback_labels
    
    # Generate generic labels
    print(f"⚠️  Generating generic class_<idx> labels (n={out_dim})")
    return [f'class_{i}' for i in range(out_dim)]


def save_label_mapping_stub(
    output_path: Path,
    num_classes: int,
    existing_labels: Optional[List[str]] = None
):
    """
    Create a stub label mapping file for user to fill in.
    
    Args:
        output_path: Where to write stub file
        num_classes: Number of classes
        existing_labels: Optional known labels to prepopulate
    """
    if existing_labels and len(existing_labels) == num_classes:
        labels = existing_labels
    else:
        labels = [f"<class_{i}_name_here>" for i in range(num_classes)]
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with output_path.open('w') as f:
        json.dump(labels, f, indent=2)
    
    print(f"✓ Created label mapping stub: {output_path}")
    print(f"  Please edit this file to provide canonical class names.")


def validate_label_mapping(mapping_file: Path, model: keras.Model) -> bool:
    """
    Validate that label mapping matches model output dimension.
    
    Args:
        mapping_file: Path to label_mapping.json
        model: Keras model
        
    Returns:
        True if valid, False otherwise
    """
    if not mapping_file.exists():
        print(f"❌ Label mapping not found: {mapping_file}")
        return False
    
    try:
        labels = json.loads(mapping_file.read_text())
        out_dim = model.output_shape[-1]
        
        if not isinstance(labels, list):
            print(f"❌ Label mapping must be a list")
            return False
        
        if len(labels) != out_dim:
            print(f"❌ Length mismatch: {len(labels)} labels vs {out_dim} outputs")
            return False
        
        print(f"✓ Label mapping valid ({len(labels)} classes)")
        return True
        
    except Exception as e:
        print(f"❌ Failed to validate: {e}")
        return False


class TemperatureScaling:
    """Temperature scaling for probability calibration."""
    
    def __init__(self, temperature: float = 1.0):
        """
        Initialize with temperature parameter.
        
        Args:
            temperature: Scaling factor (1.0 = no scaling)
        """
        self.temperature = temperature
    
    def apply(self, logits: np.ndarray) -> np.ndarray:
        """
        Apply temperature scaling to logits.
        
        Args:
            logits: Raw model outputs (before softmax)
            
        Returns:
            Calibrated probabilities
        """
        scaled_logits = logits / self.temperature
        exp_logits = np.exp(scaled_logits - np.max(scaled_logits, axis=-1, keepdims=True))
        return exp_logits / np.sum(exp_logits, axis=-1, keepdims=True)
    
    @staticmethod
    def load(calibration_file: Path) -> 'TemperatureScaling':
        """Load calibration from JSON file."""
        data = json.loads(calibration_file.read_text())
        return TemperatureScaling(temperature=data['temperature'])
    
    def save(self, calibration_file: Path):
        """Save calibration to JSON file."""
        calibration_file.parent.mkdir(parents=True, exist_ok=True)
        with calibration_file.open('w') as f:
            json.dump({'temperature': self.temperature}, f, indent=2)


def load_canonical_mapping(mapping_file: Path) -> Dict[str, str]:
    """
    Load model_class -> canonical_class mapping.
    
    Format: {"Splash": "Crash", "China": "Crash", ...}
    
    Args:
        mapping_file: Path to canonical mapping JSON
        
    Returns:
        Dictionary mapping model classes to canonical classes
    """
    if not mapping_file.exists():
        return {}
    
    data = json.loads(mapping_file.read_text())
    
    if 'model_class_to_canonical' in data:
        return data['model_class_to_canonical']
    
    return data
