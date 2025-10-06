# EXTREMELY STRICT Classification Guide

## Overview

The `strict_populate_training.py` script implements **EXTREMELY STRICT** classification rules for populating TrainingData from the complete_drum_archive. Unlike the original `organize_drum_archive.py`, this script:

- ✅ **Only accepts files with EXPLICIT tokens in filenames**
- ✅ **Ignores folder structure completely**
- ✅ **Rejects ambiguous files** (files matching multiple categories)
- ✅ **Enforces forbidden token lists** to prevent contamination
- ✅ **Provides detailed logging** of accepted and rejected files

## Usage

### 1. Validate First (Recommended)

Preview what would be copied without making any changes:

```bash
cd /Users/Gilby/Projects/MLAudioClassifier
python scripts/strict_populate_training.py --validate-only
```

### 2. Save Detailed Logs

Generate logs of accepted/rejected files for review:

```bash
python scripts/strict_populate_training.py --validate-only --save-logs
```

Logs are saved to: `/Users/Gilby/Projects/MLAudioClassifier/logs/`

### 3. Copy Files

Once satisfied with validation results, copy files:

```bash
python scripts/strict_populate_training.py --copy
```

### 4. Copy Without Cleaning

Append to existing TrainingData without removing current files:

```bash
python scripts/strict_populate_training.py --copy --no-clean
```

## Classification Rules

### Core Principles

1. **Explicit Token Required**: Filename MUST contain an explicit category token
2. **No Forbidden Tokens**: Filename MUST NOT contain ANY forbidden tokens
3. **No Ambiguity**: File must match EXACTLY ONE category (multi-matches rejected)
4. **Global Exclusions**: Certain tokens always reject (FX, vocal, loops, etc.)

### Example Classifications

#### ✅ ACCEPTED

| Filename | Category | Reason |
|----------|----------|--------|
| `kick01.wav` | Kick | Has explicit "kick" token |
| `snare_acoustic.wav` | Snare | Has "snare" token, no forbidden tokens |
| `hihat_closed.wav` | Hihat | Has "hihat" token |
| `crash_16.wav` | Crash | Has "crash" token |
| `cowbell_dry.wav` | Cowbell | Has "cowbell" token |

#### ❌ REJECTED

| Filename | Rejection Reason |
|----------|------------------|
| `kit01.wav` | No explicit category token |
| `drum_hit.wav` | No explicit category token |
| `kick_snare_combo.wav` | Ambiguous: matches multiple categories |
| `808_perc.wav` | No explicit token (perc without number) |
| `kick_fx.wav` | Global exclusion: contains 'fx' |
| `vocal_shout.wav` | Global exclusion: contains 'vocal' |

## Category Definitions

### Basic Drum Kit (6 categories)

| Category | Required Tokens | Forbidden Tokens |
|----------|----------------|------------------|
| **Kick** | kick, kik, bd | snare, tom, hat, crash, ride, metal, clap, rim |
| **Snare** | snare, snar, snr | kick, tom, rim, clap, metal, conga, bongo |
| **Tom** | tom | kick, snare, rim, atom, custom, bottom |
| **Hihat** | hihat, hi-hat, hh, hat | kick, snare, tom, crash, ride, cymbal, chat |
| **Crash** | crash | ride, china, splash, sizzle, bell, hat |
| **Ride** | ride | crash, china, splash, bell, hat |

### Cymbals (5 categories)

| Category | Required Tokens | Forbidden Tokens |
|----------|----------------|------------------|
| **China** | china | crash, ride, splash |
| **Splash** | splash | crash, ride, china, sizzle |
| **Bell** | bell | cowbell, ride, agogo, cymbal, crash |
| **Cymbal** | cymbal + number (cymbal1, cymbal2) | crash, ride, china, splash, hihat, bell |
| **Sizzle** | sizzle | crash, ride, splash |

### Hand Percussion (6 categories)

| Category | Required Tokens | Forbidden Tokens |
|----------|----------------|------------------|
| **Clap** | clap | snare, kick, rim |
| **Tambourine** | tamb, tambourine, tamborine | timbale, cymbal |
| **Shaker** | shaker | maraca |
| **Maracas** | maraca, maracas | shaker |
| **Cabasa** | cabasa | - |
| **Triangle** | triangle | - |

### Latin/World Percussion (6 categories)

| Category | Required Tokens | Forbidden Tokens |
|----------|----------------|------------------|
| **Conga** | conga | rim, bongo |
| **Bongo** | bongo | rim, conga |
| **Timbale** | timbale, timbal | rim, tambourine, tamb |
| **Clave** | clav, clave | metal, wood, drum |
| **Agogo** | agogo | bell |
| **Guiro** | guiro | - |

### Melodic/Pitched (5 categories)

| Category | Required Tokens | Forbidden Tokens |
|----------|----------------|------------------|
| **Cowbell** | cowbell | bell, agogo, metal |
| **Woodblock** | woodblock, wood block, woodblk | drum |
| **Timpani** | timpani, kettle drum | - |
| **Metal** | metal | bell, cymbal, hat, clave, cowbell, agogo, crash, ride |
| **Rim** | rim, rimshot | snare, tom, kick, conga, bongo, timbale |

### Special (5 categories)

| Category | Required Tokens | Forbidden Tokens |
|----------|----------------|------------------|
| **Whistle** | whistle | - |
| **Cuica** | cuica | - |
| **Vibraslap** | vibraslap, vibra-slap | - |
| **Perc** | perc + number (perc1, perc2) | kick, snare, tom, hat, crash, ride, clap |

## Global Exclusions

Files containing ANY of these tokens are ALWAYS rejected:

- `&` (combo samples)
- `fx`, `sfx`, `effect`
- `vox`, `vocal`, `voice`
- `loop`
- `noise`, `sweep`, `riser`, `whoosh`, `impact`

## Output

### Console Output

The script provides:

- Real-time progress updates
- Category-by-category acceptance counts
- Top 10 rejection reasons
- Overall statistics with acceptance rate

### Log Files (with --save-logs)

Two detailed log files are generated:

1. **`accepted_samples_YYYYMMDD_HHMMSS.txt`**
   - Full list of accepted files
   - Organized by category
   - Includes file paths and classification reasons

2. **`rejected_samples_YYYYMMDD_HHMMSS.txt`**
   - Full list of rejected files
   - Organized by rejection reason
   - Up to 50 examples per reason

## Expected Results

Based on EXTREMELY STRICT classification:

- **Acceptance Rate**: ~30-50% (much lower than original script)
- **Total Samples**: ~6,000-10,000 (vs ~20,000 in original)
- **Quality**: Very high - only unambiguous, clearly labeled samples

### Typical Rejection Breakdown

- ~40%: No explicit category token
- ~20%: Ambiguous (matches multiple categories)
- ~15%: Contains forbidden tokens
- ~10%: Global exclusions (FX, vocals, loops)
- ~15%: Other reasons

## Comparison with Original Script

| Aspect | Original `organize_drum_archive.py` | New `strict_populate_training.py` |
|--------|-------------------------------------|-----------------------------------|
| **Folder-based** | Yes, uses folder names | No, filename only |
| **Ambiguity** | First match wins | Rejects ambiguous files |
| **Acceptance** | ~20,000 samples | ~6,000-10,000 samples |
| **False Positives** | Possible | Extremely rare |
| **Validation** | No preview mode | Full validation mode |
| **Logging** | Basic counts | Detailed acceptance/rejection logs |

## Best Practices

1. **Always validate first**: Use `--validate-only` before copying
2. **Review logs**: Use `--save-logs` to inspect decisions
3. **Iterative refinement**: Adjust rules and re-validate as needed
4. **Clean copies**: Use default `--copy` (with clean) for fresh start
5. **Backup**: Keep a backup of existing TrainingData if appending

## Customization

To modify classification rules, edit the `STRICT_CATEGORIES` dictionary in the script:

```python
'CategoryName': {
    'required_tokens': [r'\btoken1\b', r'\btoken2\b'],
    'forbidden_tokens': ['forbidden1', 'forbidden2'],
    'description': 'Category description'
}
```

- Use `\b` for word boundaries in regex patterns
- Add to `forbidden_tokens` to prevent contamination
- Test changes with `--validate-only` first

## Troubleshooting

### Too Few Samples Accepted

- Review rejection logs to understand why files are rejected
- Consider relaxing some forbidden token rules
- Check if required tokens match actual filenames

### Still Getting Ambiguous Files

- Add more forbidden tokens to separate similar categories
- Make required token patterns more specific
- Review the detailed logs to see which categories are conflicting

### Performance Issues

- Script processes ~1000 files/second
- For very large archives (>100k files), consider running overnight
- Progress updates every 1000 files

## Support

For issues or questions:

1. Check the rejection logs in `/logs/` directory
2. Review this guide for classification rules
3. Test with `--validate-only` before copying
4. Examine specific rejected files to understand decisions
