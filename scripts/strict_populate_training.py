#!/usr/bin/env python3
"""
EXTREMELY STRICT Training Data Population Script

This script copies drum samples from complete_drum_archive to TrainingData
with EXTREMELY STRICT classification rules. Only files with EXPLICIT tokens
in their filenames are copied. Ambiguous files are rejected.

Features:
- Only exact token matches (word boundaries enforced)
- No folder-based classification (filename only)
- Strict exclusion rules to prevent contamination
- Detailed logging of accepted and rejected files
- Validation mode to preview before copying
"""

import shutil
import re
from pathlib import Path
from collections import defaultdict
import argparse
from datetime import datetime


# EXTREMELY STRICT CATEGORIES - Only explicit filename tokens
STRICT_CATEGORIES = {
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


def is_strictly_valid(filename: str, category_config: dict) -> bool:
    """
    EXTREMELY STRICT validation:
    - reject combo files (contains '&')
    - reject if any forbidden_tokens substring is present
    - accept only if at least one required_tokens regex matches
    """
    name_lower = filename.lower()
    if '&' in name_lower:
        return False

    for term in category_config.get('forbidden_tokens', []):
        if term and term in name_lower:
            return False

    for pattern in category_config.get('required_tokens', []):
        try:
            if re.search(pattern, name_lower):
                return True
        except re.error:
            # skip malformed pattern
            continue

    return False


def classify_file(filepath: Path, strict_mode: bool = True) -> tuple[str | None, str]:
    """
    Classify a file into a category using STRICT rules.
    
    Args:
        filepath: Path to the file
        strict_mode: If True, use extremely strict rules (default)
        
    Returns:
        Tuple of (category_name, reason) or (None, rejection_reason)
    """
    filename = filepath.name
    filename_lower = filename.lower()
    
    # Global exclusions - always reject these
    global_exclusions = ['&', 'fx', 'sfx', 'effect', 'vox', 'vocal', 'voice', 'loop', 
                         'noise', 'sweep', 'riser', 'whoosh', 'impact']
    
    for exclusion in global_exclusions:
        if exclusion in filename_lower:
            return None, f"Global exclusion: contains '{exclusion}'"
    
    # Try to match against each category
    matches = []
    for category, config in STRICT_CATEGORIES.items():
        if is_strictly_valid(filename, config):
            matches.append(category)
    
    # No matches
    if len(matches) == 0:
        return None, "No explicit category token found in filename"
    
    # Multiple matches - ambiguous, reject
    if len(matches) > 1:
        return None, f"Ambiguous: matches multiple categories {matches}"
    
    # Exactly one match - perfect!
    return matches[0], f"Matched by explicit token"


def scan_archive(source_dir: Path, validate_only: bool = False) -> dict:
    """
    Scan the archive and classify all WAV files.
    
    Args:
        source_dir: Path to complete_drum_archive
        validate_only: If True, only scan without copying
        
    Returns:
        Dictionary with classification results
    """
    results = {
        'accepted': defaultdict(list),
        'rejected': defaultdict(list),
        'stats': defaultdict(int)
    }
    
    print(f"\n{'='*80}")
    print(f"SCANNING: {source_dir}")
    print(f"{'='*80}\n")
    
    wav_files = list(source_dir.rglob('*.wav'))
    total_files = len(wav_files)
    
    print(f"Found {total_files:,} WAV files\n")
    
    for i, wav_file in enumerate(wav_files, 1):
        if i % 1000 == 0:
            print(f"Progress: {i:,}/{total_files:,} files processed...", end='\r')
        
        category, reason = classify_file(wav_file)
        
        if category:
            results['accepted'][category].append((wav_file, reason))
            results['stats']['accepted'] += 1
        else:
            results['rejected'][reason].append(wav_file)
            results['stats']['rejected'] += 1
    
    print(f"\nProgress: {total_files:,}/{total_files:,} files processed... DONE\n")
    
    return results


def print_results_summary(results: dict):
    """Print a summary of classification results."""
    print(f"\n{'='*80}")
    print("CLASSIFICATION RESULTS SUMMARY")
    print(f"{'='*80}\n")
    
    # Accepted files by category
    print("ACCEPTED FILES BY CATEGORY:")
    print("-" * 80)
    total_accepted = 0
    for category in sorted(STRICT_CATEGORIES.keys()):
        count = len(results['accepted'][category])
        total_accepted += count
        if count > 0:
            print(f"  {category:.<30} {count:>6,} samples")
    
    print(f"  {'TOTAL ACCEPTED':.<30} {total_accepted:>6,} samples")
    
    # Rejection summary
    print(f"\n\nREJECTED FILES BY REASON:")
    print("-" * 80)
    rejection_reasons = sorted(results['rejected'].items(), key=lambda x: len(x[1]), reverse=True)
    total_rejected = 0
    for reason, files in rejection_reasons[:10]:  # Show top 10 reasons
        count = len(files)
        total_rejected += count
        print(f"  {reason[:50]:.<52} {count:>6,} files")
    
    remaining_rejected = sum(len(files) for reason, files in rejection_reasons[10:])
    if remaining_rejected > 0:
        print(f"  {'(other reasons)':.<52} {remaining_rejected:>6,} files")
        total_rejected += remaining_rejected
    
    print(f"  {'TOTAL REJECTED':.<52} {total_rejected:>6,} files")
    
    # Overall stats
    print(f"\n\nOVERALL STATISTICS:")
    print("-" * 80)
    total_files = total_accepted + total_rejected
    acceptance_rate = (total_accepted / total_files * 100) if total_files > 0 else 0
    print(f"  Total files scanned: {total_files:,}")
    print(f"  Accepted: {total_accepted:,} ({acceptance_rate:.1f}%)")
    print(f"  Rejected: {total_rejected:,} ({100-acceptance_rate:.1f}%)")
    print()


def copy_samples(results: dict, target_dir: Path, clean_first: bool = True):
    """
    Copy accepted samples to TrainingData directory.
    
    Args:
        results: Results dictionary from scan_archive()
        target_dir: Target directory for TrainingData
        clean_first: If True, clean target directories first
    """
    print(f"\n{'='*80}")
    print("COPYING SAMPLES TO TRAINING DATA")
    print(f"{'='*80}\n")
    
    # Clean existing directories if requested
    if clean_first:
        print("Cleaning existing category directories...")
        for category in STRICT_CATEGORIES.keys():
            cat_dir = target_dir / category
            if cat_dir.exists():
                shutil.rmtree(cat_dir)
                print(f"  Removed: {cat_dir}")
        print()
    
    # Copy files
    total_copied = 0
    for category in sorted(STRICT_CATEGORIES.keys()):
        files = results['accepted'][category]
        if not files:
            continue
        
        cat_dir = target_dir / category
        cat_dir.mkdir(parents=True, exist_ok=True)
        
        copied = 0
        skipped = 0
        
        for src_file, reason in files:
            dst_file = cat_dir / src_file.name
            
            # Handle filename conflicts
            if dst_file.exists():
                # Add parent folder name to make unique
                parent_name = src_file.parent.name
                new_name = f"{parent_name}_{src_file.name}"
                dst_file = cat_dir / new_name
                
                if dst_file.exists():
                    skipped += 1
                    continue
            
            try:
                shutil.copy2(src_file, dst_file)
                copied += 1
                total_copied += 1
            except Exception as e:
                print(f"  ERROR copying {src_file.name}: {e}")
                skipped += 1
        
        print(f"  {category:.<30} {copied:>6,} files copied", end='')
        if skipped > 0:
            print(f" ({skipped} skipped due to conflicts)")
        else:
            print()
    
    print(f"\n  {'TOTAL COPIED':.<30} {total_copied:>6,} files")
    print()


def save_detailed_log(results: dict, output_dir: Path):
    """Save detailed logs of accepted and rejected files."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save accepted files log
    accepted_log = output_dir / f"accepted_samples_{timestamp}.txt"
    with open(accepted_log, 'w') as f:
        f.write("ACCEPTED SAMPLES - STRICT CLASSIFICATION\n")
        f.write("=" * 80 + "\n\n")
        
        for category in sorted(STRICT_CATEGORIES.keys()):
            files = results['accepted'][category]
            if files:
                f.write(f"\n{category} ({len(files)} samples):\n")
                f.write("-" * 80 + "\n")
                for filepath, reason in sorted(files, key=lambda x: x[0].name):
                    f.write(f"  {filepath.name}\n")
                    f.write(f"    Path: {filepath.parent}\n")
                    f.write(f"    Reason: {reason}\n")
    
    # Save rejected files log
    rejected_log = output_dir / f"rejected_samples_{timestamp}.txt"
    with open(rejected_log, 'w') as f:
        f.write("REJECTED SAMPLES - STRICT CLASSIFICATION\n")
        f.write("=" * 80 + "\n\n")
        
        for reason, files in sorted(results['rejected'].items()):
            f.write(f"\n{reason} ({len(files)} files):\n")
            f.write("-" * 80 + "\n")
            for filepath in sorted(files, key=lambda x: x.name)[:50]:  # Limit to first 50
                f.write(f"  {filepath.name}\n")
            if len(files) > 50:
                f.write(f"  ... and {len(files) - 50} more files\n")
    
    print(f"\nDetailed logs saved:")
    print(f"  Accepted: {accepted_log}")
    print(f"  Rejected: {rejected_log}")


def main():
    parser = argparse.ArgumentParser(
        description='EXTREMELY STRICT Training Data Population Script',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Validate only (preview without copying)
  python strict_populate_training.py --validate-only

  # Copy samples to TrainingData (with clean)
  python strict_populate_training.py --copy

  # Copy without cleaning existing data
  python strict_populate_training.py --copy --no-clean

  # Save detailed logs
  python strict_populate_training.py --validate-only --save-logs
        '''
    )
    
    parser.add_argument(
        '--source',
        type=str,
        default='/Users/Gilby/complete_drum_archive',
        help='Source directory (complete_drum_archive)'
    )
    
    parser.add_argument(
        '--target',
        type=str,
        default='/Users/Gilby/Projects/MLAudioClassifier/TrainingData/AudioSamples',
        help='Target directory (TrainingData/AudioSamples)'
    )
    
    parser.add_argument(
        '--validate-only',
        action='store_true',
        help='Only validate and show results, do not copy files'
    )
    
    parser.add_argument(
        '--copy',
        action='store_true',
        help='Copy files to TrainingData directory'
    )
    
    parser.add_argument(
        '--no-clean',
        action='store_true',
        help='Do not clean existing category directories before copying'
    )
    
    parser.add_argument(
        '--save-logs',
        action='store_true',
        help='Save detailed logs of accepted and rejected files'
    )
    
    args = parser.parse_args()
    
    # Validate directories
    source_dir = Path(args.source)
    target_dir = Path(args.target)
    
    if not source_dir.exists():
        print(f"ERROR: Source directory not found: {source_dir}")
        return 1
    
    # Print configuration
    print(f"\n{'='*80}")
    print("EXTREMELY STRICT TRAINING DATA POPULATION")
    print(f"{'='*80}")
    print(f"\nSource: {source_dir}")
    print(f"Target: {target_dir}")
    print(f"Mode: {'VALIDATE ONLY' if args.validate_only else 'COPY FILES'}")
    print(f"Clean before copy: {not args.no_clean}")
    print(f"Save logs: {args.save_logs}")
    
    # Scan and classify
    results = scan_archive(source_dir, validate_only=args.validate_only)
    
    # Print summary
    print_results_summary(results)
    
    # Save logs if requested
    if args.save_logs:
        logs_dir = Path('/Users/Gilby/Projects/MLAudioClassifier/logs')
        logs_dir.mkdir(exist_ok=True)
        save_detailed_log(results, logs_dir)
    
    # Copy files if requested
    if args.copy and not args.validate_only:
        target_dir.mkdir(parents=True, exist_ok=True)
        copy_samples(results, target_dir, clean_first=not args.no_clean)
        print(f"\n{'='*80}")
        print("COPY COMPLETED SUCCESSFULLY")
        print(f"{'='*80}\n")
    elif args.validate_only:
        print(f"\n{'='*80}")
        print("VALIDATION COMPLETED - NO FILES COPIED")
        print("Run with --copy to copy files to TrainingData")
        print(f"{'='*80}\n")
    
    return 0


if __name__ == '__main__':
    exit(main())