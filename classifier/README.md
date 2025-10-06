# Drum Sample Classifier Package

Production-ready audio classification system for organizing drum sample archives with a two-phase pipeline architecture.

## Architecture

### Phase 1: Inference & Index Build

- Traverse audio archive
- Extract MFCC features
- Run batch inference
- Stream results to JSONL index
- No file modifications

### Phase 2: Archive Reconstruction

- Read JSONL index
- Apply filtering/mapping rules
- Materialize organized archive
- Generate manifests and stats

## Installation

```bash
# Add to requirements
pip install pyyaml

# Or install in project
cd /path/to/MLAudioClassifier
pip install -e .
```

## Quick Start

### 1. Extract Training Labels

```bash
python scripts/extract_training_labels.py
```

This attempts to recover the original label ordering from your training data.

### 2. Validate Label Mapping

```bash
python scripts/validate_mapping.py
```

Ensures `models/label_mapping.json` matches your model's output dimension.

### 3. Run Inference

```bash
python -m classifier.cli infer --config config.yml
```

Produces `ClassifiedArchive/run_<timestamp>/index.jsonl` with all predictions.

### 4. Rebuild Archive

```bash
python -m classifier.cli rebuild \
  --index ClassifiedArchive/run_20251005_145016/index.jsonl \
  --out RegeneratedArchive \
  --labels Crash,Hihat,Kick,Ride,Snare,Tom
```

Creates organized archive with only specified labels (others go to `misc/`).

## CLI Commands

### `infer`

Run batch inference on archive:

```bash
python -m classifier.cli infer --config config.yml
```

Configuration via `config.yml`:

- Model and label mapping paths
- Audio processing parameters (MFCC, sample rate)
- Confidence thresholds
- Target labels subset
- Hash-based deduplication

### `rebuild`

Regenerate organized archive from index:

```bash
python -m classifier.cli rebuild \
  --index runs/xxx/index.jsonl \
  --out RegeneratedArchive \
  --copy-mode copy \
  --labels Crash,Hihat,Kick \
  --overrides overrides.jsonl
```

Options:

- `--copy-mode`: `copy`, `symlink`, or `hardlink`
- `--labels`: Comma-separated allowed labels
- `--allow-all`: Emit all classes (ignore filter)
- `--overrides`: Apply manual corrections from JSONL

### `validate-mapping`

Check label mapping validity:

```bash
python -m classifier.cli validate-mapping \
  --model models/model1.keras \
  --mapping models/label_mapping.json
```

### `create-stub`

Generate stub mapping file:

```bash
python -m classifier.cli create-stub \
  --model models/model1.keras \
  --output models/label_mapping_stub.json
```

### `stats`

Generate statistics from index:

```bash
python -m classifier.cli stats --index runs/xxx/index.jsonl
```

Shows:

- Label distribution
- Confidence statistics
- Duration totals
- Error breakdown

## Configuration

Edit `config.yml` to customize:

```yaml
# Model
model_path: ../models/model1.keras
label_map: ../models/label_mapping.json

# Target labels (null = emit all)
target_labels:
  - Crash
  - Hihat
  - Kick
  - Ride
  - Snare
  - Tom

# Misc routing
misc:
  threshold: 0.50  # confidence below this -> misc/

# Batch settings
batch_size: 32
dedup_hash: true
```

## JSONL Index Schema

Each line contains one file's metadata and prediction:

```json
{
  "relative_path": "Akai/Layered/BD_019.wav",
  "abs_path": "/path/to/complete_drum_archive/Akai/Layered/BD_019.wav",
  "hash": "d41d8cd98f00b204e9800998ecf8427e",
  "size": 12345,
  "mtime": 1730723456.123,
  "duration_sec": 0.412,
  "rms_db": -24.7,
  "spectral_centroid": 3421.5,
  "spectral_rolloff": 6234.1,
  "label_top1": "Kick",
  "conf_top1": 0.93,
  "topk": [["Kick",0.93], ["Snare",0.04], ["Tom",0.01]],
  "probs": [0.01, 0.04, 0.93, ...],
  "assigned_label": "Kick",
  "assigned_reason": "top1",
  "misc_routed": false,
  "below_misc_threshold": false,
  "out_of_target": false,
  "errors": null
}
```

## Overrides & Active Learning

Create `overrides.jsonl` to correct misclassifications:

```json
{"hash":"abc123...","correct_label":"Snare","note":"rim shot misclassified"}
{"hash":"def456...","correct_label":"misc","note":"non-drum sound"}
```

Apply during rebuild:

```bash
python -m classifier.cli rebuild \
  --index runs/xxx/index.jsonl \
  --out RegeneratedArchive \
  --overrides overrides.jsonl
```

## Canonical Label Mapping

If your model outputs many fine-grained classes but you want canonical organization:

Create `models/canonical_mapping.json`:

```json
{
  "model_class_to_canonical": {
    "Splash": "Crash",
    "China": "Crash",
    "Ride_Bell": "Ride",
    "Floor_Tom": "Tom",
    "Rack_Tom": "Tom"
  }
}
```

Mapping applied automatically during inference.

## Advanced Usage

### Parallel Processing

Edit `config.yml`:

```yaml
batch_size: 64  # larger batches for GPU
```

### Compressed Indexes

For large archives:

```yaml
compress_index: true  # creates index.jsonl.gz
```

### Custom Hash Algorithm

```yaml
hash_algorithm: sha256  # or md5 (faster)
```

### Reprocess Unchanged Files

Delete hash cache:

```bash
rm .cache/archive_classifier/seen_hashes.txt
```

## Module API

### Programmatic Usage

```python
from pathlib import Path
from classifier import model, features, infer, io

# Load model
keras_model = model.load_model(Path('models/model1.keras'))
labels = model.load_label_mapping(
    Path('models/label_mapping.json'),
    keras_model
)

# Setup extractor
extractor = features.AudioFeatureExtractor()

# Configure inference
config = infer.InferenceConfig(
    batch_size=32,
    misc_confidence_threshold=0.50,
    target_labels=['Crash','Hihat','Kick','Ride','Snare','Tom']
)

# Create engine
engine = infer.InferenceEngine(
    model=keras_model,
    labels=labels,
    feature_extractor=extractor,
    config=config
)

# Run
audio_files = io.discover_audio_files(
    Path('complete_drum_archive'),
    ['.wav', '.flac']
)

summary = engine.run(
    audio_files=audio_files,
    archive_root=Path('complete_drum_archive'),
    output_path=Path('output/index.jsonl')
)
```

## Troubleshooting

### "Label mapping length mismatch"

Your model outputs N classes but mapping has M labels.

- Run `python scripts/validate_mapping.py` to diagnose
- Use `create-stub` to generate correct template

### "No model files found"

Check `models/` directory contains `.keras` files.

### "PySoundFile failed" warnings

Some audio formats (MP3) require audioread backend. Either:

- Remove `.mp3` from `supported_formats` in config
- Install ffmpeg: `brew install ffmpeg`

### Slow performance

- Increase `batch_size` (32 → 64+)
- Use `hash_algorithm: md5` instead of sha256
- Set `include_audio_stats: false` to skip spectral features

## Output Structure

### Inference Run

```
ClassifiedArchive/
  run_20251005_145016/
    index.jsonl          # full predictions
    summary.json         # run statistics
```

### Regenerated Archive

```
RegeneratedArchive/
  Crash/
    sample1.wav
    sample2.wav
  Kick/
  ...
  misc/
    uncertain1.wav
  _manifests/
    Crash.txt           # list of files
    Kick.txt
  _rebuild_summary.json
```

## Next Steps

1. **Temperature Calibration**: Improve confidence reliability
   - Requires labeled validation set
   - Fit temperature scaling parameter
   - Apply during inference

2. **Ensemble Models**: Combine multiple models
   - Average probabilities from model1 + model2
   - Improves accuracy and calibration

3. **Active Learning**: Iterative improvement
   - Export low-confidence samples
   - Manual review and correction
   - Retrain with corrected labels

4. **Gating Model**: Two-stage classification
   - Binary: "is canonical drum class?"
   - Main model only for positive gates
   - Reduces misc contamination

## License

Part of MLAudioClassifier project.
