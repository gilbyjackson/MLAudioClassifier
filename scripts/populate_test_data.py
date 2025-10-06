#!/usr/bin/env python3
import shutil
import re
from pathlib import Path

# Strict patterns - must match exactly, no ambiguity
# All 34 categories from TrainingData
STRICT_TEST_CATEGORIES = {
    # === Main Drum Kit (6 categories) ===
    'Kick': {
        'required_tokens': [r'\bkick\d*\b', r'\bkik\d*\b', r'\bbd\d*\b'],
        'forbidden_tokens': ['snare', 'tom', 'hat', 'crash', 'ride', 'perc', 'fx', '&']
    },
    'Snare': {
        'required_tokens': [r'\bsnare?\d*\b', r'\bsnr\d*\b'],
        'forbidden_tokens': ['kick', 'tom', 'rim', 'perc', 'fx', '&']
    },
    'Tom': {
        'required_tokens': [r'\btom\d*\b'],
        'forbidden_tokens': ['kick', 'snare', 'rim', 'perc', 'fx', '&', 'atom', 'custom', 'bottom']
    },
    'Hihat': {
        'required_tokens': [r'\bhihat\d*\b', r'\bhi-hat\d*\b', r'\bhh\d*\b'],
        'forbidden_tokens': ['crash', 'ride', 'perc', 'fx', '&', 'chat']
    },
    'Crash': {
        'required_tokens': [r'\bcrash\d*\b'],
        'forbidden_tokens': ['ride', 'china', 'splash', 'hihat', 'perc', 'fx', '&']
    },
    'Ride': {
        'required_tokens': [r'\bride\d*\b'],
        'forbidden_tokens': ['crash', 'china', 'splash', 'bell', 'perc', 'fx', '&']
    },
    'China': {
        'required_tokens': [r'\bchina\d*\b'],
        'forbidden_tokens': ['crash', 'ride', 'splash', 'perc', 'fx', '&']
    },
    'Splash': {
        'required_tokens': [r'\bsplash\d*\b'],
        'forbidden_tokens': ['crash', 'ride', 'china', 'sizzle', 'perc', 'fx', '&']
    },
    'Bell': {
        'required_tokens': [r'\bbell\d*\b'],
        'forbidden_tokens': ['cow', 'ride', 'agogo', 'perc', 'fx', '&']
    },
    'Clap': {
        'required_tokens': [r'\bclap\d*\b'],
        'forbidden_tokens': ['hand', 'snap', 'slap', 'perc', 'fx', '&']
    },
    'Tambourine': {
        'required_tokens': [r'\btamb(?:ourine)?\d*\b', r'\btamborine\d*\b'],
        'forbidden_tokens': ['timbale', 'cymbal', 'perc', 'fx', '&']
    },
    'Shaker': {
        'required_tokens': [r'\bshaker\d*\b'],
        'forbidden_tokens': ['maraca', 'perc', 'fx', '&']
    },
    'Maracas': {
        'required_tokens': [r'\bmaraca[s]?\d*\b'],
        'forbidden_tokens': ['shaker', 'perc', 'fx', '&']
    },
    'Cabasa': {
        'required_tokens': [r'\bcabasa\d*\b'],
        'forbidden_tokens': ['perc', 'fx', '&']
    },
    'Triangle': {
        'required_tokens': [r'\btriangle\d*\b'],
        'forbidden_tokens': ['perc', 'fx', '&']
    },
    'Conga': {
        'required_tokens': [r'\bconga\d*\b'],
        'forbidden_tokens': ['rim', 'bongo', 'perc', 'fx', '&']
    },
    'Bongo': {
        'required_tokens': [r'\bbongo\d*\b'],
        'forbidden_tokens': ['rim', 'conga', 'perc', 'fx', '&']
    },
    'Timbale': {
        'required_tokens': [r'\btimbale?\d*\b', r'\btimbal\d*\b'],
        'forbidden_tokens': ['rim', 'tambourine', 'tamb', 'perc', 'fx', '&']
    },
    'Clave': {
        'required_tokens': [r'\bclav[e]?\d*\b'],
        'forbidden_tokens': ['wood', 'metal', 'perc', 'fx', '&']
    },
    'Agogo': {
        'required_tokens': [r'\bagogo\d*\b'],
        'forbidden_tokens': ['bell', 'perc', 'fx', '&']
    },
    'Guiro': {
        'required_tokens': [r'\bguiro\d*\b'],
        'forbidden_tokens': ['perc', 'fx', '&']
    },
    
    # === Melodic/Pitched (5 categories) ===
    'Bass': {
        'required_tokens': [r'\bbass\d*\b', r'\bsub?kick\d*\b', r'\b(?:synth)\s?bass\d*\b', r'\bass(?:hit)\d*\b', r'\b(?:sub)\s?bass\d*\b', r'\bbd\d*\b'],
        'forbidden_tokens': ['drum', 'snare', 'tom', 'hat', 'crash', 'ride', 'perc', 'fx', '&']
    },
    'Cowbell': {
        'required_tokens': [r'\bcowbell\d*\b'],
        'forbidden_tokens': ['agogo', 'metal', 'perc', 'fx', '&']  # Note: 'bell' removed since cowbell contains 'bell'
    },
    'Woodblock': {
        'required_tokens': [r'\bwood\s?block\d*\b', r'\bwoodblk\d*\b'],
        'forbidden_tokens': ['drum', 'perc', 'fx', '&']
    },
    'Timpani': {
        'required_tokens': [r'\btimpani\d*\b', r'\bkettle\s?drum\d*\b'],
        'forbidden_tokens': ['perc', 'fx', '&']
    },
    'Metal': {
        'required_tokens': [r'\bmetal\d*\b'],
        'forbidden_tokens': ['bell', 'cymbal', 'hat', 'clave', 'cowbell', 'agogo', 'crash', 'ride', 'perc', 'fx', '&']
    },
    'Rim': {
        'required_tokens': [r'\brim(?:shot)?\d*\b'],
        'forbidden_tokens': ['conga', 'bongo', 'timbale', 'tom', 'snare', 'perc', 'fx', '&', 'prim', 'trim']
    },
    'Whistle': {
        'required_tokens': [r'\bwhistle\d*\b'],
        'forbidden_tokens': ['perc', 'fx', '&']
    },
    'Cuica': {
        'required_tokens': [r'\bcuica\d*\b'],
        'forbidden_tokens': ['perc', 'fx', '&']
    },
    'Vibraslap': {
        'required_tokens': [r'\bvibraslap\d*\b', r'\bvibra-slap\d*\b'],
        'forbidden_tokens': ['perc', 'fx', '&']
    },
    'Perc': {
        'required_tokens': [r'\bperc\d+\b'],
        'forbidden_tokens': ['kick', 'snare', 'tom', 'hat', 'crash', 'ride', 'clap', 'fx', '&']
    },
}

source_dir = Path('/Users/Gilby/Projects/MLAudioClassifier/TrainingData/AudioSamples')
target_dir = Path('/Users/Gilby/Projects/MLAudioClassifier/TestData')

def is_strict_match(filename, folder_name, config):
    name_lower = filename.lower()
    folder_lower = folder_name.lower()
    
    # Must not contain forbidden terms
    for forbidden in config['forbidden_tokens']:
        if forbidden in name_lower or forbidden in folder_lower:
            return False
    
    # Must match required pattern
    if not any(re.search(pattern, name_lower) for pattern in config['required_tokens']):
        return False
    
    # Additional strictness: filename should be simple (no complex descriptions)
    # Allow up to 4 words for named variations (e.g., "African Cowbell.wav")
    if len(name_lower.replace('.wav', '').split()) > 4:
        return False
    
    return True

def main():
    print(f"\n{'='*80}")
    print("POPULATING TEST DATA")
    print(f"{'='*80}\n")
    print(f"Source: {source_dir}")
    print(f"Target: {target_dir}\n")
    
    # Clean existing TestData directories
    print("Cleaning existing TestData directories...")
    for cat in STRICT_TEST_CATEGORIES.keys():
        cat_dir = target_dir / cat
        if cat_dir.exists():
            shutil.rmtree(cat_dir)
            print(f"  Removed: {cat}/")
    print()
    
    results = {cat: [] for cat in STRICT_TEST_CATEGORIES}
    
    # Collect strictly matching files
    print("Scanning TrainingData for test samples...")
    for cat, config in STRICT_TEST_CATEGORIES.items():
        cat_source = source_dir / cat
        if not cat_source.exists():
            print(f"  ⚠️  {cat}: Source folder not found in TrainingData")
            continue
        
        for wav_file in cat_source.glob('*.wav'):
            if is_strict_match(wav_file.name, cat, config):
                results[cat].append(wav_file)
    
    print()
    
    # Copy to TestData (limit to reasonable test set size)
    print("Copying test samples...")
    populated_categories = []
    skipped_categories = []
    
    for cat, files in results.items():
        if not files:
            skipped_categories.append((cat, "No files found in TrainingData"))
            continue
        
        # Limit test samples to ~20% of available or max 100
        test_count = min(len(files) // 5, 100)
        # Lowered threshold to 20 to include more categories
        if test_count < 4:  # Need at least 4 samples for meaningful test
            min_needed = 20  # 20 files / 5 = 4 test samples
            skipped_categories.append((cat, f"Only {len(files)} strict matches (need {min_needed}+)"))
            print(f"  ⚠️  {cat}: Only {len(files)} strict matches, skipping (need {min_needed}+)")
            continue
        
        cat_dir = target_dir / cat
        cat_dir.mkdir(parents=True, exist_ok=True)
        
        # Take evenly distributed samples
        step = len(files) // test_count
        selected = files[::step][:test_count]
        
        for src in selected:
            dst = cat_dir / src.name
            if not dst.exists():
                shutil.copy2(src, dst)
        
        populated_categories.append(cat)
        print(f"  ✅ {cat}: {len(selected)} samples copied (from {len(files)} strict matches)")
    
    print(f"\n{'='*80}")
    print("TEST DATA POPULATION COMPLETED")
    print(f"{'='*80}\n")
    
    # Print summary
    total_samples = sum(len(list((target_dir / cat).glob('*.wav'))) 
                       for cat in STRICT_TEST_CATEGORIES.keys() 
                       if (target_dir / cat).exists())
    print(f"✅ Categories populated: {len(populated_categories)}/34")
    print(f"✅ Total test samples: {total_samples}")
    
    if skipped_categories:
        print(f"\n⚠️  Skipped categories ({len(skipped_categories)}):")
        for cat, reason in skipped_categories:
            print(f"   - {cat}: {reason}")
    
    print(f"\n{'='*80}\n")

if __name__ == '__main__':
    main()
