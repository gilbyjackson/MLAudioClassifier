#!/usr/bin/env python3
from pathlib import Path
from collections import defaultdict
import re

target_dir = Path('/Users/Gilby/Projects/MLAudioClassifier/TrainingData/AudioSamples')

# All category terms
ALL_TERMS = [
    'kick', 'snare', 'snr', 'tom', 'hihat', 'hi-hat', 'hh', 'crash', 'ride',
    'china', 'splash', 'cymbal', 'sizzle', 'bell', 'clap', 'rim', 'rimshot',
    'cowbell', 'clave', 'clav', 'cabasa', 'shaker', 'tambourine', 'tamb',
    'triangle', 'woodblock', 'wood block', 'whistle', 'cuica', 'agogo',
    'vibraslap', 'guiro', 'conga', 'bongo', 'timbale', 'maracas', 'maraca',
    'timpani', 'metal', 'perc', 'percussion', 'fx', 'sfx', 'vox', 'vocal',
    'drum', 'berimbau', 'caixa', 'tamborim'
]

def find_all_terms(text):
    found = []
    text_lower = text.lower()
    for term in ALL_TERMS:
        if re.search(r'\b' + re.escape(term) + r'\b', text_lower):
            found.append(term)
    return found

def main():
    issues = defaultdict(list)
    
    for cat_dir in sorted(target_dir.iterdir()):
        if not cat_dir.is_dir():
            continue
        
        cat_name = cat_dir.name
        files = list(cat_dir.glob('*.wav'))
        
        print(f"\n{'='*70}")
        print(f"Analyzing: {cat_name} ({len(files)} files)")
        print(f"{'='*70}")
        
        crossover = []
        for wav_file in files:
            terms = find_all_terms(wav_file.name)
            # Check if file has terms other than the category
            other_terms = [t for t in terms if t.lower() not in cat_name.lower()]
            if other_terms:
                crossover.append((wav_file.name, other_terms))
        
        if crossover:
            print(f"⚠️  {len(crossover)} files with crossover terms:")
            for fname, terms in crossover[:10]:
                print(f"   {fname} → {terms}")
            if len(crossover) > 10:
                print(f"   ... and {len(crossover) - 10} more")
            issues[cat_name] = crossover
        else:
            print(f"✓ Clean")
    
    print(f"\n{'='*70}")
    print("SUMMARY")
    print(f"{'='*70}")
    
    if issues:
        print(f"\n{len(issues)} categories with issues:")
        for cat, items in sorted(issues.items(), key=lambda x: -len(x[1])):
            print(f"  {cat}: {len(items)} crossover files")
    else:
        print("\n✓ All categories clean!")

if __name__ == '__main__':
    main()
