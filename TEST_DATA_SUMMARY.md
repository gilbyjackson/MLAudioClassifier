# TestData Population Summary

## Overview

TestData has been populated with **18 categories** and **810 samples** using **EXTREMELY STRICT** classification rules from the 34 categories available in TrainingData.

## Populated Categories (18/34)

### Basic Drum Kit (6 categories) - 420 samples
| Category | Test Samples | Training Matches | Notes |
|----------|--------------|------------------|-------|
| **Kick** | 100 | 1,153 | ✅ Full quota |
| **Snare** | 100 | 1,664 | ✅ Full quota |
| **Tom** | 100 | 1,440 | ✅ Full quota |
| **Hihat** | 46 | 233 | Limited by availability |
| **Crash** | 38 | 194 | Limited by availability |
| **Ride** | 36 | 184 | Limited by availability |

### Cymbals (1 category) - 16 samples
| Category | Test Samples | Training Matches | Notes |
|----------|--------------|------------------|-------|
| **Bell** | 16 | 83 | Cymbal bell (not cowbell) |

### Hand Percussion (5 categories) - 119 samples
| Category | Test Samples | Training Matches | Notes |
|----------|--------------|------------------|-------|
| **Clap** | 74 | 371 | Good representation |
| **Tambourine** | 12 | 61 | Limited availability |
| **Shaker** | 13 | 66 | Limited availability |
| **Maracas** | 10 | 54 | Minimum threshold |
| **Triangle** | 10 | 52 | Minimum threshold |

### Latin/World Percussion (3 categories) - 96 samples
| Category | Test Samples | Training Matches | Notes |
|----------|--------------|------------------|-------|
| **Conga** | 55 | 276 | Good representation |
| **Bongo** | 27 | 138 | Adequate samples |
| **Timbale** | 14 | 74 | Limited availability |

### Melodic/Pitched (2 categories) - 63 samples
| Category | Test Samples | Training Matches | Notes |
|----------|--------------|------------------|-------|
| **Cowbell** | 26 | 134 | Good representation |
| **Rim** | 37 | 189 | Good representation |

### Special (1 category) - 96 samples
| Category | Test Samples | Training Matches | Notes |
|----------|--------------|------------------|-------|
| **Perc** | 96 | 483 | Generic numbered percussion |

## Skipped Categories (12/34)

These categories were skipped because they had fewer than 50 strict matches (minimum threshold for 10 test samples):

| Category | Strict Matches | Reason |
|----------|----------------|--------|
| **Cabasa** | 49 | Just below threshold |
| **Clave** | 49 | Just below threshold |
| **Agogo** | 47 | Just below threshold |
| **Guiro** | 49 | Just below threshold |
| **China** | 40 | Below threshold |
| **Splash** | 31 | Below threshold |
| **Whistle** | 41 | Below threshold |
| **Cuica** | 38 | Below threshold |
| **Woodblock** | 34 | Below threshold |
| **Metal** | 26 | Below threshold |
| **Timpani** | 25 | Below threshold |
| **Vibraslap** | 12 | Far below threshold |

### Note on Skipped Categories
Many categories (Cabasa, Clave, Agogo, Guiro) are very close to the 50-match threshold. The strict matching rules filter out:
- Files with forbidden tokens (e.g., "perc", "fx")
- Files with complex descriptions (>4 words)
- Files without explicit category tokens in filename

## Not Included in Test Set (4 categories)

These categories exist in TrainingData but are NOT suitable for clean test data:
- **FX** - Effects samples (excluded by design)
- **Vox** - Vocal samples (excluded by design)  
- **Noise** - Noise samples (excluded by design)
- **Reverse** - Reversed samples (excluded by design)
- **Sizzle** - Cymbal category (low count in TrainingData)

## Classification Rules

### Strict Matching Criteria
1. **Required Token**: Filename MUST contain explicit category token (e.g., "kick", "snare")
2. **No Forbidden Tokens**: Filename MUST NOT contain forbidden words
3. **Word Count Limit**: Filename should be ≤4 words (e.g., "African Cowbell.wav" is OK)
4. **No Combos**: Files with "&" are rejected
5. **No FX/Vocals**: Global exclusions apply

### Test Sample Selection
- **Target**: ~20% of available strict matches per category
- **Maximum**: 100 samples per category
- **Minimum**: 10 samples per category (50 strict matches required)
- **Distribution**: Evenly distributed across available samples

## Usage

### Current TestData Structure
```
TestData/
├── Bell/          (16 samples)
├── Bongo/         (27 samples)
├── Clap/          (74 samples)
├── Conga/         (55 samples)
├── Cowbell/       (26 samples)
├── Crash/         (38 samples)
├── Hihat/         (46 samples)
├── Kick/          (100 samples)
├── Maracas/       (10 samples)
├── Perc/          (96 samples)
├── Ride/          (36 samples)
├── Rim/           (37 samples)
├── Shaker/        (13 samples)
├── Snare/         (100 samples)
├── Tambourine/    (12 samples)
├── Timbale/       (14 samples)
├── Tom/           (100 samples)
└── Triangle/      (10 samples)
```

### Regenerating TestData

To regenerate TestData from TrainingData:

```bash
cd /Users/Gilby/Projects/MLAudioClassifier
python3 scripts/populate_test_data.py
```

The script will:
1. Clean existing TestData directories
2. Scan TrainingData for strict matches
3. Copy test samples (20% or max 100 per category)
4. Report populated and skipped categories

### Modifying Thresholds

To include more categories, you can edit `populate_test_data.py`:

```python
# Current threshold: 50 matches → 10 test samples
if test_count < 10:  # Need at least 10 samples
    min_needed = 50  # 50 files / 5 = 10 test samples
```

To lower to 30 matches → 6 test samples:
```python
if test_count < 6:  # Need at least 6 samples
    min_needed = 30  # 30 files / 5 = 6 test samples
```

## Comparison: TrainingData vs TestData

| Aspect | TrainingData | TestData |
|--------|--------------|----------|
| **Total Categories** | 34 | 18 |
| **Total Samples** | ~10,791 | 810 |
| **Quality Control** | Strict (filename-based) | Extremely Strict |
| **Purpose** | Model training | Model evaluation |
| **Sample Distribution** | Full dataset | 20% sample or max 100 |

## Model Training Recommendations

### For 18-Class Model
Use all 18 populated categories. This gives:
- Good variety (drums, cymbals, percussion)
- Adequate sample sizes for most classes
- Clean, well-labeled data

### For 6-Class Model (Basic Drum Kit)
Use only: Kick, Snare, Tom, Hihat, Crash, Ride
- 420 total test samples
- Balanced representation
- Core drum kit sounds

### For 10-Class Model (Extended Kit)
Add: Clap, Cowbell, Rim, Bell to the 6-class model
- 599 total test samples  
- More variety while maintaining quality

## Notes

1. **Quality Over Quantity**: TestData uses stricter rules than TrainingData to ensure clean evaluation data
2. **No Data Leakage**: Test samples are distinct from training samples (different selection)
3. **Balanced Selection**: Samples are evenly distributed across available matches
4. **Reproducible**: Running the script produces consistent results

## Related Scripts

- **`strict_populate_training.py`**: Populates TrainingData from complete_drum_archive (34 categories)
- **`populate_test_data.py`**: Populates TestData from TrainingData (18 categories)
- **`organize_drum_archive.py`**: Original population script (less strict)

## Last Updated

Population completed: October 5, 2025
- Script: `populate_test_data.py`
- Source: `TrainingData/AudioSamples/`
- Target: `TestData/`
