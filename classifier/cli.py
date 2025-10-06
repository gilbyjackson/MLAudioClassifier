"""
Command-line interface for drum sample classifier.

Usage:
    python -m classifier.cli infer --config config.yml
    python -m classifier.cli rebuild --index runs/20251005_145016/index.jsonl --out RegeneratedArchive
    python -m classifier.cli validate-mapping --model models/model1.keras --mapping models/label_mapping.json
    python -m classifier.cli stats --index runs/20251005_145016/index.jsonl
"""

import argparse
import json
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from classifier import io, features, model, infer, rebuild


def cmd_infer(args):
    """Run inference on archive."""
    import yaml
    
    # Load config
    config_path = Path(args.config)
    if not config_path.exists():
        print(f"❌ Config not found: {config_path}")
        return 1
    
    with config_path.open() as f:
        config = yaml.safe_load(f)
    
    # Setup paths
    model_path = Path(config['model_path'])
    archive_root = Path(config['paths']['archive_root'])
    runs_root = Path(config['paths']['runs_root'])
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    run_dir = runs_root / f'run_{timestamp}'
    run_dir.mkdir(parents=True, exist_ok=True)
    
    # Load model and labels
    print("Loading model...")
    keras_model = model.load_model(model_path)
    
    label_map_file = Path(config.get('label_map', 'models/label_mapping.json'))
    labels = model.load_label_mapping(
        label_map_file,
        keras_model,
        fallback_labels=config.get('fallback_labels')
    )
    
    print(f"Model outputs {len(labels)} classes")
    print(f"First 10 labels: {labels[:10]}")
    
    # Load canonical mapping if available
    canonical_map_file = Path(config.get('canonical_mapping', 'models/canonical_mapping.json'))
    canonical_mapping = model.load_canonical_mapping(canonical_map_file) if canonical_map_file.exists() else None
    
    # Setup feature extractor
    extractor = features.AudioFeatureExtractor(
        target_sr=config.get('target_sr', 44100),
        target_samples=config.get('target_samples', 50000),
        n_mfcc=config.get('n_mfcc', 40),
        n_fft=config.get('n_fft', 2048),
        hop_length=config.get('hop_length', 512),
        normalize=config.get('normalize', True),
        min_duration_sec=config.get('min_duration_sec', 0.05)
    )
    
    # Discover files
    print(f"\nScanning {archive_root}...")
    formats = config.get('supported_formats', ['.wav', '.flac', '.aiff', '.aif'])
    audio_files = io.discover_audio_files(
        archive_root,
        formats,
        max_files=config.get('max_files_per_run')
    )
    audio_files = io.filter_valid_files(audio_files)
    print(f"Found {len(audio_files)} audio files")
    
    # Setup inference config
    inf_config = infer.InferenceConfig(
        batch_size=config.get('batch_size', 32),
        confidence_threshold=config.get('confidence_threshold', 0.0),
        misc_confidence_threshold=config['misc']['threshold'],
        target_labels=config.get('target_labels'),
        dedup_hash=config.get('dedup_hash', True),
        hash_algorithm=config.get('hash_algorithm', 'md5'),
        include_audio_stats=config.get('include_audio_stats', True),
        top_k=config.get('top_k', 3)
    )
    
    # Create engine
    engine = infer.InferenceEngine(
        model=keras_model,
        labels=labels,
        feature_extractor=extractor,
        config=inf_config,
        canonical_mapping=canonical_mapping
    )
    
    # Load hash cache
    cache_dir = Path(config.get('cache_dir', '.cache/archive_classifier'))
    cache_dir.mkdir(parents=True, exist_ok=True)
    hash_cache_path = cache_dir / 'seen_hashes.txt'
    engine.load_hash_cache(hash_cache_path)
    
    # Run inference
    index_path = run_dir / 'index.jsonl'
    compressed = config.get('compress_index', False)
    
    summary = engine.run(
        audio_files=audio_files,
        archive_root=archive_root,
        output_path=index_path,
        compressed=compressed
    )
    
    # Save hash cache
    engine.save_hash_cache(hash_cache_path)
    
    # Save summary
    summary['config'] = config
    summary['timestamp'] = datetime.now().isoformat()
    summary['run_dir'] = str(run_dir)
    
    summary_path = run_dir / 'summary.json'
    with summary_path.open('w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"\n✓ Inference complete")
    print(f"  Index: {index_path}")
    print(f"  Summary: {summary_path}")
    
    return 0


def cmd_rebuild(args):
    """Rebuild archive from index."""
    index_path = Path(args.index)
    output_root = Path(args.out)
    
    if not index_path.exists():
        print(f"❌ Index not found: {index_path}")
        return 1
    
    # Load overrides if provided
    overrides = {}
    if args.overrides:
        override_path = Path(args.overrides)
        if override_path.exists():
            from classifier.io import JSONLReader
            reader = JSONLReader(override_path)
            for rec in reader:
                overrides[rec['hash']] = rec['correct_label']
            print(f"Loaded {len(overrides)} overrides")
    
    # Parse allowed labels
    allowed_labels = None
    if args.labels:
        allowed_labels = args.labels.split(',')
    
    # Create rebuilder
    rebuilder = rebuild.ArchiveRebuilder(
        index_path=index_path,
        output_root=output_root,
        copy_mode=args.copy_mode,
        override_mapping=overrides,
        allowed_labels=allowed_labels,
        force_all=args.allow_all
    )
    
    # Run rebuild
    rebuilder.rebuild()
    
    return 0


def cmd_validate_mapping(args):
    """Validate label mapping against model."""
    model_path = Path(args.model)
    mapping_path = Path(args.mapping)
    
    if not model_path.exists():
        print(f"❌ Model not found: {model_path}")
        return 1
    
    print(f"Loading model: {model_path}")
    keras_model = model.load_model(model_path)
    
    valid = model.validate_label_mapping(mapping_path, keras_model)
    
    return 0 if valid else 1


def cmd_create_stub(args):
    """Create stub label mapping."""
    model_path = Path(args.model)
    output_path = Path(args.output)
    
    if not model_path.exists():
        print(f"❌ Model not found: {model_path}")
        return 1
    
    print(f"Loading model: {model_path}")
    keras_model = model.load_model(model_path)
    
    num_classes = keras_model.output_shape[-1]
    
    model.save_label_mapping_stub(output_path, num_classes)
    
    return 0


def cmd_stats(args):
    """Generate statistics from index."""
    index_path = Path(args.index)
    
    if not index_path.exists():
        print(f"❌ Index not found: {index_path}")
        return 1
    
    from classifier.io import JSONLReader
    from collections import Counter
    
    print(f"Reading {index_path}...")
    reader = JSONLReader(index_path)
    
    total = 0
    errors = 0
    duplicates = 0
    labels = Counter()
    confidences = []
    durations = []
    
    for record in reader:
        total += 1
        
        if record.get('errors'):
            errors += 1
            continue
        
        if record.get('skipped_duplicate'):
            duplicates += 1
            continue
        
        label = record.get('assigned_label')
        if label:
            labels[label] += 1
        
        conf = record.get('conf_top1')
        if conf is not None:
            confidences.append(conf)
        
        dur = record.get('duration_sec')
        if dur is not None:
            durations.append(dur)
    
    print(f"\n{'='*60}")
    print(f"Index Statistics")
    print(f"{'='*60}")
    print(f"Total records: {total}")
    print(f"Errors: {errors}")
    print(f"Duplicates: {duplicates}")
    print(f"Unique files: {total - errors - duplicates}")
    
    if confidences:
        import numpy as np
        print(f"\nConfidence Statistics:")
        print(f"  Mean: {np.mean(confidences):.3f}")
        print(f"  Median: {np.median(confidences):.3f}")
        print(f"  Min: {np.min(confidences):.3f}")
        print(f"  Max: {np.max(confidences):.3f}")
    
    if durations:
        import numpy as np
        print(f"\nDuration Statistics:")
        print(f"  Mean: {np.mean(durations):.3f}s")
        print(f"  Median: {np.median(durations):.3f}s")
        print(f"  Total: {np.sum(durations)/3600:.2f}h")
    
    print(f"\nLabel Distribution:")
    for label, count in labels.most_common():
        pct = 100 * count / (total - errors - duplicates)
        print(f"  {label:<20} {count:>6} ({pct:>5.1f}%)")
    
    return 0


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Drum Sample Classifier CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # Infer command
    p_infer = subparsers.add_parser('infer', help='Run inference on archive')
    p_infer.add_argument('--config', default='config.yml', help='Config file path')
    
    # Rebuild command
    p_rebuild = subparsers.add_parser('rebuild', help='Rebuild archive from index')
    p_rebuild.add_argument('--index', required=True, help='Path to index.jsonl')
    p_rebuild.add_argument('--out', required=True, help='Output directory')
    p_rebuild.add_argument('--copy-mode', default='copy', choices=['copy', 'symlink', 'hardlink'])
    p_rebuild.add_argument('--overrides', help='Path to overrides.jsonl')
    p_rebuild.add_argument('--labels', help='Comma-separated allowed labels')
    p_rebuild.add_argument('--allow-all', action='store_true', help='Emit all labels')
    
    # Validate mapping
    p_validate = subparsers.add_parser('validate-mapping', help='Validate label mapping')
    p_validate.add_argument('--model', required=True, help='Path to model file')
    p_validate.add_argument('--mapping', required=True, help='Path to label mapping')
    
    # Create stub
    p_stub = subparsers.add_parser('create-stub', help='Create label mapping stub')
    p_stub.add_argument('--model', required=True, help='Path to model file')
    p_stub.add_argument('--output', default='models/label_mapping_stub.json', help='Output path')
    
    # Stats command
    p_stats = subparsers.add_parser('stats', help='Generate statistics from index')
    p_stats.add_argument('--index', required=True, help='Path to index.jsonl')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Dispatch to command handler
    handlers = {
        'infer': cmd_infer,
        'rebuild': cmd_rebuild,
        'validate-mapping': cmd_validate_mapping,
        'create-stub': cmd_create_stub,
        'stats': cmd_stats
    }
    
    return handlers[args.command](args)


if __name__ == '__main__':
    sys.exit(main())
