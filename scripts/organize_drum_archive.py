#!/usr/bin/env python3
import shutil
import re
from pathlib import Path

CATEGORIES = {
    'Kick': {'patterns': [r'\bkick\d*\b'], 'folders': ['kick', 'kik'], 'exclude': ['metal', 'snare']},
    'Snare': {'patterns': [r'\bsnare?\d*\b', r'\bsnr\d*\b'], 'folders': ['snare', 'snr'], 'exclude': ['kick', 'rim']},
    'Tom': {'patterns': [r'\btom\d*\b'], 'folders': ['tom'], 'exclude': ['rim']},
    'Hihat': {'patterns': [r'\b(?:hi-?hat)\d*\b'], 'folders': ['hihat', 'hi-hat'], 'exclude': ['crash']},
    'Crash': {'patterns': [r'\bcrash\d*\b'], 'folders': ['crash'], 'exclude': []},
    'Ride': {'patterns': [r'\bride\d*\b'], 'folders': ['ride'], 'exclude': []},
    'China': {'patterns': [r'\bchina\d*\b'], 'folders': ['china'], 'exclude': []},
    'Splash': {'patterns': [r'\bsplash\d*\b'], 'folders': ['splash'], 'exclude': []},
    'Sizzle': {'patterns': [r'\bsizzle\d*\b'], 'folders': ['sizzle'], 'exclude': []},
    'Bell': {'patterns': [r'\bbell\d*\b'], 'folders': ['bell'], 'exclude': ['cowbell', 'ride', 'agogo']},
    'Cymbal': {'patterns': [r'\bcymbal\d\b'], 'folders': [], 'exclude': ['crash', 'ride', 'china', 'splash', 'sizzle', 'bell']},  # Only cymbal[0-9].wav
    'Clap': {'patterns': [r'\bclap\d*\b'], 'folders': ['clap'], 'exclude': []},
    'Rim': {'patterns': [r'\brim(?:shot)?\d*\b'], 'folders': ['rim', 'rimshot'], 'exclude': ['conga', 'bongo', 'timbale', 'tom', 'berimbau', 'snare', 'clav', 'tamb', 'caixa', 'drum']},
    'Cowbell': {'patterns': [r'\bcowbell\d*\b'], 'folders': ['cowbell'], 'exclude': ['vocal', 'vox', 'bongo', 'timbale', 'metal', 'drum']},
    'Clave': {'patterns': [r'\bclav[e]?\d*\b'], 'folders': ['clav'], 'exclude': ['metal']},
    'Cabasa': {'patterns': [r'\bcabasa\d*\b'], 'folders': ['cabasa'], 'exclude': ['drum']},
    'Shaker': {'patterns': [r'\bshaker\d*\b'], 'folders': ['shaker'], 'exclude': []},
    'Tambourine': {'patterns': [r'\btamb(?:ourine)?\d*\b'], 'folders': ['tamb'], 'exclude': []},
    'Triangle': {'patterns': [r'\btriangle\d*\b'], 'folders': ['triangle'], 'exclude': []},
    'Woodblock': {'patterns': [r'\bwood\s?block\d*\b'], 'folders': ['woodblock'], 'exclude': ['vocal', 'vox', 'drum']},
    'Whistle': {'patterns': [r'\bwhistle\d*\b'], 'folders': ['whistle'], 'exclude': []},
    'Cuica': {'patterns': [r'\bcuica\d*\b'], 'folders': ['cuica'], 'exclude': []},
    'Agogo': {'patterns': [r'\bagogo\d*\b'], 'folders': ['agogo'], 'exclude': ['fx', 'bell']},
    'Vibraslap': {'patterns': [r'\bvibraslap\d*\b'], 'folders': ['vibraslap'], 'exclude': []},
    'Guiro': {'patterns': [r'\bguiro\d*\b'], 'folders': ['guiro'], 'exclude': []},
    'Conga': {'patterns': [r'\bconga\d*\b'], 'folders': ['conga'], 'exclude': ['rim']},
    'Bongo': {'patterns': [r'\bbongo\d*\b'], 'folders': ['bongo'], 'exclude': ['rim', 'fx']},
    'Timbale': {'patterns': [r'\btimbale\d*\b'], 'folders': ['timbale'], 'exclude': ['rim']},
    'Maracas': {'patterns': [r'\bmaracas?\d*\b'], 'folders': ['maraca'], 'exclude': []},
    'Timpani': {'patterns': [r'\btimpani\d*\b'], 'folders': ['timpani'], 'exclude': []},
    'Metal': {'patterns': [r'\bmetal\d*\b'], 'folders': ['metal'], 'exclude': ['bell', 'cymbal', 'hat', 'clave']},
    'Perc': {'patterns': [r'\bperc\d+\b'], 'folders': [], 'exclude': ['kick', 'snare', 'tom', 'hat', 'crash', 'ride', 'clap', 'rim', 'conga', 'bongo', 'clave']},
    'FX': {
        'patterns': [r'\b(?:fx|sfx|se_fx|noise|noiz|effect|thang|sweep|riser?|falls?|whoosh|glitch|hits?|impact|laser|pops?|revs?|reverse|zaps?|scratch|swish|swoop|buzz|crackle|hiss|static|whine|drones?|morph|transform|twist|warp|winds?|shine|sparkle|texture|atmosphere|space|special|filter|modulate|guns?|zips?|booms?|bangs?|clanks?|clangs?|clash|fizz|hums?|pews?|plinks?|plunks?|sizzle|thunder|tings?|tinkle|twangs?|whomps?)\d*\b'],
        'folders': ['fx', 'sfx', 'effect'],
        'exclude': ['kick', 'bass', 'snare', 'tom', 'hat', 'crash', 'ride', 'clap', 'vocal', 'vox']
    },
    'Vox': {
        'patterns': [r'\b(?:vox|vocal|voice|sings?|sung|screams?|shouts?|talks?|speech|chants?|choirs?|chorus|verse|words?|lyrics?|breaths?|humans?|males?|females?|heys?|ahs?|yeahs?|ohs?|oohs?|aahs?|mmms?|whispers?|growls?|grunts?|hums?|speaks?|yells?)\d*\b'],
        'folders': ['vox', 'vocal', 'voice'],
        'exclude': ['kick', 'snare', 'tom', 'hat', 'crash', 'ride']
    },
}

source_dir = Path('/Users/Gilby/complete_drum_archive')
target_dir = Path('/Users/Gilby/Projects/MLAudioClassifier/TrainingData/AudioSamples')

def matches_category(filename, cat_config):
    name_lower = filename.lower()
    # Exclude combo samples with "&"
    if ' & ' in filename or '&' in filename:
        return False
    if any(term in name_lower for term in cat_config['exclude']):
        return False
    return any(re.search(pattern, name_lower) for pattern in cat_config['patterns'])

def is_category_folder(folder_name, cat_config):
    name_lower = folder_name.lower()
    # Use word boundaries for folder matching too
    return any(re.search(r'\b' + re.escape(term) + r'\b', name_lower) for term in cat_config['folders'])

def main():
    for cat in CATEGORIES:
        cat_dir = target_dir / cat
        if cat_dir.exists():
            shutil.rmtree(cat_dir)
    
    results = {cat: set() for cat in CATEGORIES}
    
    for wav_file in source_dir.rglob('*.wav'):
        # Skip combo samples with "&"
        if '&' in wav_file.name:
            continue
        for cat, config in CATEGORIES.items():
            if is_category_folder(wav_file.parent.name, config) or matches_category(wav_file.name, config):
                results[cat].add(wav_file)
                break
    
    for cat, files in results.items():
        if files:
            cat_dir = target_dir / cat
            cat_dir.mkdir(exist_ok=True)
            for src in files:
                dst = cat_dir / src.name
                if not dst.exists():
                    shutil.copy2(src, dst)
            print(f"{cat}: {len(files)}")
    
    print(f"\nTotal: {sum(len(f) for f in results.values())}")

if __name__ == '__main__':
    main()
