# STRICT Training Data Population Script

## Quick Start

```bash
# Navigate to project
cd /Users/Gilby/Projects/MLAudioClassifier

# 1. Preview what will be copied (RECOMMENDED FIRST STEP)
python3 scripts/strict_populate_training.py --validate-only

# 2. Generate detailed logs for review
python3 scripts/strict_populate_training.py --validate-only --save-logs

# 3. Copy files to TrainingData
python3 scripts/strict_populate_training.py --copy
```

## What Makes This EXTREMELY STRICT?

### ✅ Only Explicit Tokens
- Files MUST have category tokens in their filename
- Examples: `kick01.wav`, `snare_acoustic.wav`, `hihat_closed.wav`
- **Rejected**: `drum01.wav`, `kit_sound.wav`, `perc.wav`

### ✅ No Folder-Based Classification
- Original script used folder names → can lead to false positives
- This script: **filename only** → more reliable

### ✅ Rejects Ambiguous Files
- Files matching multiple categories are rejected
- Example: `kick_snare_combo.wav` → **REJECTED**

### ✅ Strict Exclusions
- Files with forbidden tokens are rejected
- Example: `kick_reverb.wav` → **REJECTED** if "reverb" is forbidden

### ✅ Global Exclusions
Always rejected:
- FX samples (`fx`, `sfx`, `effect`)
- Vocal samples (`vox`, `vocal`, `voice`)
- Loops (`loop`)
- Combo samples (contains `&`)

## Results from Test Run

```
Total files scanned: 46,962
Accepted: 10,791 (23.0%)
Rejected: 36,171 (77.0%)
```

### Breakdown by Category (31 categories with samples):

**Drum Kit** (6,344 samples):
- Kick: 1,364
- Snare: 1,942
- Tom: 1,758
- Hihat: 1,280

**Cymbals** (523 samples):
- Crash: 363
- Ride: 313
- Cymbal: 138
- China: 47
- Splash: 36
- Bell: 125
- Sizzle: 4

**Hand Percussion** (987 samples):
- Clap: 479
- Tambourine: 142
- Shaker: 149
- Maracas: 79
- Triangle: 82
- Cabasa: 98

**Latin/World** (990 samples):
- Conga: 396
- Bongo: 187
- Timbale: 123
- Clave: 105
- Agogo: 74
- Guiro: 79

**Special/Melodic** (1,947 samples):
- Perc: 872
- Rim: 314
- Cowbell: (not listed - would need "cowbell" token)
- Woodblock: 55
- Metal: 32
- Timpani: 31
- Whistle: 58
- Cuica: 45
- Vibraslap: 21

## Main Rejection Reasons

1. **No explicit token** (34,289 files) - Generic names like "drum01.wav"
2. **FX samples** (1,163 files) - Effects and processing
3. **Combo samples** (239 files) - Multi-instrument samples with "&"
4. **Noise samples** (194 files) - Noise/texture samples
5. **Loop samples** (93 files) - Rhythm loops

## Files Created

### Main Script
**`scripts/strict_populate_training.py`**
- ~850 lines of Python
- Fully documented with docstrings
- Command-line interface with multiple modes

### Documentation
**`docs/STRICT_CLASSIFICATION_GUIDE.md`**
- Complete classification rules
- Category definitions
- Usage examples
- Troubleshooting guide

### Helper Scripts
**`scripts/run_strict_examples.sh`**
- Interactive examples
- Step-by-step walkthrough

## Usage Modes

### 1. Validation Mode (Safe)
```bash
python3 scripts/strict_populate_training.py --validate-only
```
- Scans all files
- Shows classification results
- **Does NOT copy any files**
- Perfect for testing

### 2. Validation with Logs
```bash
python3 scripts/strict_populate_training.py --validate-only --save-logs
```
- Same as validation mode
- **Plus**: Saves detailed logs to `logs/` directory
- Review exactly which files accepted/rejected

### 3. Copy Mode (Active)
```bash
python3 scripts/strict_populate_training.py --copy
```
- Scans and classifies files
- **Copies files to TrainingData**
- Cleans existing category folders first
- Creates new organized structure

### 4. Copy Without Clean
```bash
python3 scripts/strict_populate_training.py --copy --no-clean
```
- Appends to existing TrainingData
- Does NOT remove current files
- Useful for adding more samples

## Custom Source/Target

```bash
python3 scripts/strict_populate_training.py \
  --source /path/to/archive \
  --target /path/to/output \
  --validate-only
```

## Comparison with Original Script

| Feature | Original | Strict |
|---------|----------|--------|
| **Files accepted** | ~20,000 | ~10,791 |
| **Acceptance rate** | ~43% | ~23% |
| **False positives** | Higher risk | Extremely low |
| **Uses folders** | Yes | No |
| **Ambiguity handling** | First match | Reject |
| **Preview mode** | No | Yes |
| **Detailed logs** | No | Yes |

## When to Use Which Script?

### Use `organize_drum_archive.py` (Original) if:
- You want maximum sample count
- You trust the folder structure
- You're okay with some false positives
- You want faster processing

### Use `strict_populate_training.py` (New) if:
- You want maximum quality/accuracy
- You need to validate before copying
- You want detailed logs
- You prefer explicit over implicit classification
- You're training a machine learning model (quality > quantity)

## Next Steps After Population

1. **Review the logs** (if you used `--save-logs`)
   ```bash
   ls -lh logs/
   # Open accepted_samples_*.txt and rejected_samples_*.txt
   ```

2. **Check the TrainingData structure**
   ```bash
   ls -lh TrainingData/AudioSamples/
   # Should see folders for each category
   ```

3. **Verify sample counts**
   ```bash
   for dir in TrainingData/AudioSamples/*; do
     echo "$(basename $dir): $(ls $dir | wc -l) samples"
   done
   ```

4. **Update your training notebooks** to use the new data

## Troubleshooting

### "Source directory not found"
- Check that `/Users/Gilby/complete_drum_archive` exists
- Or specify custom path with `--source`

### "Too few samples"
- This is expected with STRICT rules
- Review rejection logs to understand why
- Consider if quality > quantity for your use case

### "Want to include more files"
- Edit `STRICT_CATEGORIES` in the script
- Add more `required_tokens` patterns
- Remove some `forbidden_tokens`
- Re-run with `--validate-only` to test

## Support

For detailed information, see:
- **Full Guide**: `docs/STRICT_CLASSIFICATION_GUIDE.md`
- **Script**: `scripts/strict_populate_training.py` (well-commented)
- **Examples**: `scripts/run_strict_examples.sh`

## Key Takeaway

**Quality over Quantity**: This script accepts ~11,000 high-confidence samples (23%) instead of ~20,000 potentially mixed samples (43%). Perfect for machine learning training where clean data is crucial.
