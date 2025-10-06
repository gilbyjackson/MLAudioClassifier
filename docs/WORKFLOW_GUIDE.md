# Complete Workflow: From Sourcing Samples to Strict Classification

## Overview

This guide mirrors the current end-to-end pipeline for MLAudioClassifier. It covers preparing strict training/test datasets from the master archive, training the neural networks, classifying fresh libraries, and monitoring results. All commands assume you start in the project root (`/Users/Gilby/Projects/MLAudioClassifier`).

## 0. Prerequisites

- **Python environment**: Python 3.10+ with TensorFlow/Keras, Librosa, NumPy, Pandas, Matplotlib.
- **Audio data**: The `complete_drum_archive/` vendor tree (20,086 curated samples across 34 categories as documented in `docs/ARCHIVE_ORGANIZATION.md`).
- **Project folders**: Run the setup helper to ensure expected directories exist:

  ```bash
  python3 scripts/setup_directories.py
  ```

  This creates `complete_drum_archive/` for unsorted clips and verifies `TrainingData/AudioSamples/` and `TestData/`.

## 1. Build Strict TrainingData

The EXTREMELY STRICT classifier enforces explicit filename tokens, forbidden token lists, and ambiguity rejection. Use `STRICT_POPULATE_README.md` for quick reference and `docs/STRICT_CLASSIFICATION_GUIDE.md` for exhaustive rules.

1. **Dry-run validation** (no files copied):

   ```bash
   python3 scripts/strict_populate_training.py --validate-only
   ```

2. **Generate review logs** (accepted/rejected lists saved to `logs/`):

   ```bash
   python3 scripts/strict_populate_training.py --validate-only --save-logs
   ```

3. **Populate `TrainingData/AudioSamples/`** (cleans existing folders by default):

   ```bash
   python3 scripts/strict_populate_training.py --copy
   ```

   - Use `--no-clean` to append instead of replace.
   - Add `--source` or `--target` to work with alternate paths.
4. **Optional quality audits**:
   - `python3 scripts/deep_folder_analysis.py` – report instrument-token crossovers per folder.
   - `python3 scripts/inspect_catchment.py` – sample ambiguous filenames for spot checks.

Typical output after a fresh run (see `STRICT_POPULATE_README.md`):

- ~46,962 files scanned
- 10,791 strict matches accepted (≈23% acceptance)
- 34 instrument categories populated (drum kit, cymbals, hand percussion, Latin/world, melodic/pitched, special, sound design)

## 2. Derive Strict TestData

`TestData/` holds an evaluation subset selected from TrainingData with even tighter thresholds (explicit tokens, maximum four-word names, category quotas).

1. **Populate or refresh**:

   ```bash
   python3 scripts/populate_test_data.py
   ```

   This cleans each strict category and copies up to 100 files (≈20% sample) if at least 50 strict matches exist.
2. **Review the summary** in `TEST_DATA_SUMMARY.md`:
   - 18 categories filled (810 total samples)
   - Core kit categories reach 100 clips each (Kick, Snare, Tom)
   - Cymbals/percussion populated to availability (e.g., Hihat 46, Crash 38, Ride 36, Perc 96, Bell 16, Rim 37)
   - 12 categories skipped when strict matches < 50 (Cabasa, Clave, Agogo, Guiro, China, Splash, Whistle, Cuica, Woodblock, Metal, Timpani, Vibraslap)
3. **Adjust thresholds** by editing `MIN_MATCHES` logic inside `scripts/populate_test_data.py` if you need more categories at lower sample counts.

## 3. Feature Extraction

Run the MFCC notebook to generate feature datasets used by both models:

1. Launch Jupyter (or open in VS Code) and execute `notebooks/MFCC_Feature_Extractor.ipynb`.
2. Ensure paths resolve to:
   - Input: `TrainingData/AudioSamples/` and `TestData/`
   - Output: `data/mfcc_train_data.json`, `data/mfcc_test_data.json`
3. Confirm MFCCs use 40 coefficients, 50,000-sample waveform windows (≈1.13s), mono, 44.1 kHz.

## 4. Model Training

### Option A – Model 1 (Direct MFCC CNN)

1. Open `notebooks/Model1_Train.ipynb`.
2. Train using the MFCC datasets (6-class configuration by default).
3. Saved artefacts:
   - `models/model1.keras`
   - `models/model1_history.json`
   - TensorBoard logs in `logs/train/` (if callbacks enabled)

### Option B – Model 2 (Autoencoder + Classifier)

1. Open `notebooks/Model2_Train.ipynb`.
2. Train the autoencoder encoder plus downstream classifier.
3. Saved artefacts:
   - `models/encoder.keras`
   - `models/model2.keras`
   - `models/model2_history.json`

Both notebooks can be run sequentially; they share the MFCC source data.

## 5. Evaluation & Monitoring

1. Execute `notebooks/Model_Evaluation.ipynb` to compare both models.
   - Reads `data/mfcc_test_data.json` and all saved `.keras` weights.
   - Generates confusion matrices for six drum-kit classes.
   - Stores plots in `results/accuracy.png`, `results/loss.png`, `results/model2_accuracy.png`, `results/model2_loss.png`.
2. Inspect TensorBoard dashboards by pointing to `logs/train/` for deeper training diagnostics.

## 6. Classification Pipelines

### A. Practical Demo (Sample Library Sorting)

1. Place unsorted `.wav` clips into `complete_drum_archive/`.
2. Run `notebooks/PracticalDemo.ipynb`.
3. The notebook:
   - Loads `model1.keras` or `model2.keras` (set in the first cells).
   - Normalizes audio, extracts MFCCs, predicts instrument class + confidence.
   - Moves files into `ClassifiedArchive/<Instrument>/` with filenames formatted as `{instrument}_{confidence:.3f}_{original}.wav`.
4. Review `ClassifiedArchive/metadata/` for prediction logs if enabled.

### B. Archive-scale Experiments

Use `notebooks/ArchiveClassifier.ipynb` to prototype large batch scoring directly against `complete_drum_archive/` or other datasets. Configure batch paths per cell instructions.

## 7. Maintenance & Utilities

- **Notebook path updates**: If you reorganize assets, run `python3 scripts/update_notebook_paths.py` to rewrite hard-coded paths inside all notebooks.
- **Strict workflow rehearsal**: `scripts/run_strict_examples.sh` provides an interactive, step-by-step shell walkthrough of the strict population script (validation → logs → copy).
- **Log review**: Inspect `logs/accepted_samples_*.txt` and `logs/rejected_samples_*.txt` (when `--save-logs` is used) to understand filtering outcomes.

## 8. Troubleshooting

| Symptom | Likely Cause | Resolution |
| --- | --- | --- |
| `TrainingData/AudioSamples/<Category>/` empty | Strict rules rejected all samples | Revisit rejection logs, relax tokens in `STRICT_CATEGORIES`, or run original `scripts/organize_drum_archive.py` for a broader sweep. |
| TestData missing categories | Category has <50 strict matches | Lower the threshold in `scripts/populate_test_data.py` or augment TrainingData. |
| Notebook path errors | Running outside project root | `cd /Users/Gilby/Projects/MLAudioClassifier` before launching notebooks or rerun `scripts/update_notebook_paths.py`. |
| Low classification confidence in `PracticalDemo` | Sample distribution differs from training data | Add similar samples to TrainingData, rerun strict population, regenerate MFCCs, and retrain models. |
| Script performance issues on large archives | Processing >100k files in strict mode | Run overnight or narrow `--source` to subdirectories. |

## 9. Next Steps & Extensions

- Expand class coverage by tweaking strict category definitions (see `docs/STRICT_CLASSIFICATION_GUIDE.md`).
- Incorporate additional metrics (precision/recall per class) inside evaluation notebooks.
- Integrate strict scripts into automated cron jobs to keep Training/Test splits and `complete_drum_archive/` classifications fresh.
