#!/usr/bin/env python3
import shutil
import re
from pathlib import Path

CATEGORIES = {
    'Kick': {
        'required_tokens': [r'\bkick\b', r'\bkik\b', r'\bass\s?drum\b'],  # bd = bass drum
        'forbidden_tokens': ['snare', 'snr', 'tom', 'hat', 'crash', 'ride', 'metal', 'clap', 'rim'],
        'description': 'Bass drum / kick drum samples'
    },
    'Bass': {
        'required_tokens': [r'\bbass\d*\b', r'\bsub?bass\d*\b', r'\bsubkick\b', r'\bsub?kick\d*\b', r'\b(?:synth)\s?bass\d*\b', r'\bass(?:hit)\d*\b', r'\b(?:sub)\s?bass\d*\b'],
        'forbidden_tokens': ['drum', 'snare', 'tom', 'hat', 'crash', 'ride', 'perc', 'fx', '&'],
        'description': 'Bass samples'
    },
    'Snare': {
        'required_tokens': [r'\bsnare?\b', r'\bsnr\b', r'\bsnaredrum\b', r'\bsnare\s?drum\b'],
        'forbidden_tokens': ['kick', 'tom', 'rim', 'clap', 'metal', 'conga', 'bongo', 'timbale'],
        'description': 'Snare drum samples'
    },
    'Tom': {
        'required_tokens': [r'\btom\b'],
        'forbidden_tokens': ['kick', 'snare', 'rim', 'atom', 'custom', 'bottom'],
        'description': 'Tom drum samples'
    },
    'Hihat': {
        'required_tokens': [r'\bhihat\b', r'\bhi-hat\b', r'\bhi\s?hat\b', r'\bchh\b', r'\bohh\b', r'\bhat\b'],
        'forbidden_tokens': ['kick', 'snare', 'tom', 'crash', 'ride', 'cymbal', 'chat'],  # chat = Charleston (French for hihat, but ambiguous)
        'description': 'Hi-hat cymbal samples'
    },
    'Crash': {
        'required_tokens': [r'\bcrash\b', r'\bcrash\s?cymbal\b'],
        'forbidden_tokens': ['ride', 'china', 'splash', 'sizzle', 'bell', 'hat'],
        'description': 'Crash cymbal samples'
    },
    'Ride': {
        'required_tokens': [r'\bride\b'],
        'forbidden_tokens': ['crash', 'china', 'splash', 'bell', 'hat'],
        'description': 'Ride cymbal samples'
    },
    'China': {
        'required_tokens': [r'\bchina\b'],
        'forbidden_tokens': ['crash', 'ride', 'splash'],
        'description': 'China cymbal samples'
    },
    'Splash': {
        'required_tokens': [r'\bsplash\b'],
        'forbidden_tokens': ['crash', 'ride', 'china', 'sizzle'],
        'description': 'Splash cymbal samples'
    },
    'Bell': {
        'required_tokens': [r'\bbell\b'],
        'forbidden_tokens': ['cowbell', 'ride', 'agogo', 'cymbal', 'crash'],
        'description': 'Cymbal bell samples (NOT cowbell)'
    },
    'Cymbal': {
        'required_tokens': [r'\bcymbal\d+\b'],  # Only numbered cymbals like cymbal1, cymbal2
        'forbidden_tokens': ['crash', 'ride', 'china', 'splash', 'hihat', 'hat', 'bell'],
        'description': 'Generic numbered cymbal samples'
    },
    'Clap': {
        'required_tokens': [r'\bclap\b'],
        'forbidden_tokens': ['snare', 'kick', 'rim'],
        'description': 'Handclap samples'
    },
    'Rim': {
        'required_tokens': [r'\brim\b', r'\brimshot\b'],
        'forbidden_tokens': ['snare', 'tom', 'kick', 'conga', 'bongo', 'timbale', 'prim', 'trim', 'grim'],
        'description': 'Rimshot samples'
    },
    'Cowbell': {
        'required_tokens': [r'\bcowbell\b'],
        'forbidden_tokens': ['bell', 'agogo', 'metal'],
        'description': 'Cowbell samples'
    },
    'Clave': {
        'required_tokens': [r'\bclav[e]?\b'],
        'forbidden_tokens': ['metal', 'wood', 'drum'],
        'description': 'Clave samples'
    },
    'Cabasa': {
        'required_tokens': [r'\bcabasa\b'],
        'forbidden_tokens': [],
        'description': 'Cabasa samples'
    },
    'Shaker': {
        'required_tokens': [r'\bshaker\b'],
        'forbidden_tokens': ['maraca'],
        'description': 'Shaker samples'
    },
    'Tambourine': {
        'required_tokens': [r'\btamb(?:ourine)?\b', r'\btamborine\b'],
        'forbidden_tokens': ['timbale', 'cymbal'],
        'description': 'Tambourine samples'
    },
    'Triangle': {
        'required_tokens': [r'\btriangle\b'],
        'forbidden_tokens': [],
        'description': 'Triangle samples'
    },
    'Woodblock': {
        'required_tokens': [r'\bwood\s?block\b', r'\bwoodblk\b'],
        'forbidden_tokens': ['drum'],
        'description': 'Woodblock samples'
    },
    'Whistle': {
        'required_tokens': [r'\bwhistle\b'],
        'forbidden_tokens': [],
        'description': 'Whistle samples'
    },
    'Cuica': {
        'required_tokens': [r'\bcuica\b'],
        'forbidden_tokens': [],
        'description': 'Cuica samples'
    },
    'Agogo': {
        'required_tokens': [r'\bagogo\b'],
        'forbidden_tokens': ['bell'],
        'description': 'Agogo bell samples'
    },
    'Vibraslap': {
        'required_tokens': [r'\bvibraslap\b', r'\bvibra-slap\b'],
        'forbidden_tokens': [],
        'description': 'Vibraslap samples'
    },
    'Guiro': {
        'required_tokens': [r'\bguiro\b'],
        'forbidden_tokens': [],
        'description': 'Guiro samples'
    },
    'Conga': {
        'required_tokens': [r'\bconga\b'],
        'forbidden_tokens': ['rim', 'bongo'],
        'description': 'Conga drum samples'
    },
    'Bongo': {
        'required_tokens': [r'\bbongo\b'],
        'forbidden_tokens': ['rim', 'conga'],
        'description': 'Bongo drum samples'
    },
    'Timbale': {
        'required_tokens': [r'\btimbale\b', r'\btimbal\b'],
        'forbidden_tokens': ['rim', 'tambourine', 'tamb'],
        'description': 'Timbale drum samples'
    },
    'Maracas': {
        'required_tokens': [r'\bmaraca[s]?\b'],
        'forbidden_tokens': ['shaker'],
        'description': 'Maracas samples'
    },
    'Timpani': {
        'required_tokens': [r'\btimpani\b', r'\bkettle\s?drum\b'],
        'forbidden_tokens': [],
        'description': 'Timpani samples'
    },
    'Metal': {
        'required_tokens': [r'\bmetal\b'],
        'forbidden_tokens': ['bell', 'cymbal', 'hat', 'clave', 'cowbell', 'agogo', 'crash', 'ride'],
        'description': 'Generic metal percussion'
    },
    'Perc': {
        'required_tokens': [r'\bperc\d+\b'],  # Only numbered perc like perc1, perc2
        'forbidden_tokens': ['kick', 'snare', 'tom', 'hat', 'crash', 'ride', 'clap'],
        'description': 'Generic numbered percussion samples'
    },
    'Sizzle': {
        'required_tokens': [r'\bsizzle\b'],
        'forbidden_tokens': ['crash', 'ride', 'splash'],
        'description': 'Sizzle cymbal samples'
    },
}

source_dir = Path('/Users/Gilby/complete_drum_archive')
target_dir = Path('/Users/Gilby/Projects/MLAudioClassifier/TrainingData/AudioSamples')

def matches_category(filename, cat_config):
    """
    Match using canonical keys:
    - required_tokens: list of regex patterns (must match at least one)
    - forbidden_tokens: list of plain substrings (if any present -> reject)
    """
    name_lower = filename.lower()
    # Exclude combo samples with "&"
    if '&' in filename:
        return False

    # Reject if any forbidden token (substring) is present
    for term in cat_config.get('forbidden_tokens', []):
        if term and term in name_lower:
            return False

    # Accept if any required regex pattern matches
    for pattern in cat_config.get('required_tokens', []):
        try:
            if re.search(pattern, name_lower):
                return True
        except re.error:
            # ignore malformed pattern and continue
            continue

    return False

def is_category_folder(folder_name, cat_config):
    """
    Check folder name for required token patterns as a fallback.
    Uses same required_tokens patterns (word-boundary aware regex expected).
    """
    name_lower = folder_name.lower()
    for pattern in cat_config.get('required_tokens', []):
        try:
            if re.search(pattern, name_lower):
                return True
        except re.error:
            continue
    return False

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
