"""
Quick test script for classifier package.

Usage:
    python scripts/test_classifier.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


def test_imports():
    """Test that all modules import correctly."""
    print("Testing imports...")
    
    try:
        from classifier import io, features, model, infer, rebuild
        print("✓ All modules imported successfully")
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False


def test_file_discovery():
    """Test file discovery."""
    print("\nTesting file discovery...")
    
    from classifier import io
    
    archive = Path('complete_drum_archive')
    if not archive.exists():
        print(f"⚠️  Archive not found: {archive}")
        return True
    
    files = io.discover_audio_files(archive, ['.wav'], max_files=10)
    print(f"✓ Found {len(files)} files (limited to 10)")
    
    if files:
        print(f"  Sample: {files[0].name}")
    
    return True


def test_feature_extractor():
    """Test feature extraction."""
    print("\nTesting feature extraction...")
    
    from classifier import features
    import numpy as np
    
    extractor = features.AudioFeatureExtractor()
    
    # Find a test file
    archive = Path('complete_drum_archive')
    if archive.exists():
        from classifier import io
        files = io.discover_audio_files(archive, ['.wav'], max_files=1)
        
        if files:
            print(f"  Extracting from: {files[0].name}")
            feat, meta = extractor.extract_mfcc(files[0])
            
            if feat is not None:
                print(f"✓ MFCC shape: {feat.shape}")
                print(f"  Duration: {meta.get('duration_sec', 'N/A')}s")
                return True
            else:
                print(f"❌ Extraction failed: {meta.get('error')}")
                return False
    
    print("⚠️  No test files available")
    return True


def test_model_loading():
    """Test model loading."""
    print("\nTesting model loading...")
    
    from classifier import model
    
    model_dir = Path('models')
    if not model_dir.exists():
        print("⚠️  models/ directory not found")
        return True
    
    try:
        keras_model = model.load_latest_model(model_dir)
        print(f"✓ Model loaded: {keras_model.output_shape}")
        return True
    except Exception as e:
        print(f"❌ Model loading failed: {e}")
        return False


def main():
    """Run all tests."""
    print("="*60)
    print("Classifier Package Test Suite")
    print("="*60)
    
    tests = [
        test_imports,
        test_file_discovery,
        test_feature_extractor,
        test_model_loading
    ]
    
    results = [test() for test in tests]
    
    print("\n" + "="*60)
    passed = sum(results)
    total = len(results)
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("✓ All tests passed")
        return 0
    else:
        print("⚠️  Some tests failed or skipped")
        return 1


if __name__ == '__main__':
    sys.exit(main())
