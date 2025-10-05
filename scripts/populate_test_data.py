#!/usr/bin/env python3
import shutil
import re
from pathlib import Path

# Strict patterns - must match exactly, no ambiguity
STRICT_TEST_CATEGORIES = {
    'Clap': {
        'required': [r'\bclap\d*\b'],
        'forbidden': ['hand', 'snap', 'slap', 'perc', 'fx', '&']
    },
    'Rim': {
        'required': [r'\brim(?:shot)?\d*\b'],
        'forbidden': ['conga', 'bongo', 'timbale', 'tom', 'snare', 'perc', 'fx', '&']
    },
    'Cowbell': {
        'required': [r'\bcowbell\d*\b'],
        'forbidden': ['perc', 'fx', 'metal', '&']
    },
    'China': {
        'required': [r'\bchina\d*\b'],
        'forbidden': ['crash', 'ride', 'cymbal', 'perc', 'fx', '&']
    },
    'Bell': {
        'required': [r'\bbell\d*\b'],
        'forbidden': ['cow', 'ride', 'agogo', 'perc', 'fx', '&']
    },
    'Clave': {
        'required': [r'\bclav[e]?\d*\b'],
        'forbidden': ['wood', 'perc', 'fx', '&']
    },
}

source_dir = Path('/Users/Gilby/Projects/MLAudioClassifier/TrainingData/AudioSamples')
target_dir = Path('/Users/Gilby/Projects/MLAudioClassifier/TestData')

def is_strict_match(filename, folder_name, config):
    name_lower = filename.lower()
    folder_lower = folder_name.lower()
    
    # Must not contain forbidden terms
    for forbidden in config['forbidden']:
        if forbidden in name_lower or forbidden in folder_lower:
            return False
    
    # Must match required pattern
    if not any(re.search(pattern, name_lower) for pattern in config['required']):
        return False
    
    # Additional strictness: filename should be simple (no complex descriptions)
    if len(name_lower.replace('.wav', '').split()) > 3:
        return False
    
    return True

def main():
    results = {cat: [] for cat in STRICT_TEST_CATEGORIES}
    
    # Collect strictly matching files
    for cat, config in STRICT_TEST_CATEGORIES.items():
        cat_source = source_dir / cat
        if not cat_source.exists():
            continue
        
        for wav_file in cat_source.glob('*.wav'):
            if is_strict_match(wav_file.name, cat, config):
                results[cat].append(wav_file)
    
    # Copy to TestData (limit to reasonable test set size)
    for cat, files in results.items():
        if not files:
            continue
        
        # Limit test samples to ~20% of available or max 100
        test_count = min(len(files) // 5, 100)
        if test_count < 10:  # Need at least 10 samples for meaningful test
            print(f"⚠️  {cat}: Only {len(files)} strict matches, skipping (need 50+)")
            continue
        
        cat_dir = target_dir / cat
        cat_dir.mkdir(exist_ok=True)
        
        # Take evenly distributed samples
        step = len(files) // test_count
        selected = files[::step][:test_count]
        
        for src in selected:
            dst = cat_dir / src.name
            if not dst.exists():
                shutil.copy2(src, dst)
        
        print(f"✅ {cat}: {len(selected)} samples (from {len(files)} strict matches)")

if __name__ == '__main__':
    main()
