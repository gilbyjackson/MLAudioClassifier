#!/usr/bin/env python3
import re
from pathlib import Path
from collections import defaultdict

target_dir = Path('/Users/Gilby/Projects/MLAudioClassifier/TrainingData/AudioSamples')

# All category terms to check for crossover
ALL_TERMS = [
    'kick', 'snare', 'snr', 'tom', 'hihat', 'hi-hat', 'hh', 'crash', 'ride', 
    'china', 'splash', 'cymbal', 'sizzle', 'bell', 'clap', 'rim', 'rimshot',
    'cowbell', 'clave', 'clav', 'cabasa', 'shaker', 'tambourine', 'tamb',
    'triangle', 'woodblock', 'wood block', 'whistle', 'cuica', 'agogo',
    'vibraslap', 'guiro', 'conga', 'bongo', 'timbale', 'maracas', 'maraca',
    'timpani', 'metal', 'perc', 'percussion', 'fx', 'sfx', 'vox', 'vocal'
]

def find_terms_in_filename(filename):
    name_lower = filename.lower()
    found = []
    for term in ALL_TERMS:
        if re.search(r'\b' + re.escape(term) + r'\b', name_lower):
            found.append(term)
    return found

def main():
    crossover_files = defaultdict(list)
    
    for category_dir in sorted(target_dir.iterdir()):
        if not category_dir.is_dir():
            continue
        
        print(f"\n{'='*60}")
        print(f"Inspecting: {category_dir.name}")
        print(f"{'='*60}")
        
        files = list(category_dir.glob('*.wav'))
        crossover_count = 0
        
        for wav_file in files[:10]:  # Sample first 10
            terms = find_terms_in_filename(wav_file.name)
            if len(terms) > 1:
                crossover_count += 1
                crossover_files[category_dir.name].append((wav_file.name, terms))
        
        if crossover_count > 0:
            print(f"⚠️  Found {crossover_count} crossover files in sample")
            for fname, terms in crossover_files[category_dir.name][:5]:
                print(f"   {fname} → {terms}")
        else:
            print(f"✓ Clean (sampled {min(10, len(files))} files)")
        
        print(f"Total files: {len(files)}")
    
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    
    if crossover_files:
        print("\nCategories with crossover issues:")
        for cat, files in crossover_files.items():
            print(f"  {cat}: {len(files)} crossover files")
    else:
        print("\n✓ All categories clean!")

if __name__ == '__main__':
    main()
