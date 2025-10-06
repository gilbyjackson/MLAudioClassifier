# MLAudioClassifier Project Structure

## Overview

MLAudioClassifier combines curated drum sample archives, strict dataset curation utilities, neural-network training notebooks, and documentation for reproducing the full classification workflow. This document reflects the repository layout as of October 2025 and highlights how the data, scripts, notebooks, and models connect.

## Top-Level Contents

- `ClassifiedArchive/` – Output library produced by the demo classifier. Contains instrument-specific folders (Crash, Hihat, Kick, Ride, Snare, Tom, etc.) plus `metadata/` for prediction logs.
- `complete_drum_archive/` – Master source library organized by manufacturer (Akai, Roland, Yamaha, …). `docs/ARCHIVE_ORGANIZATION.md` summarises the **20,086** curated samples stored in 34 instrument categories.
- `data/` – Serialized MFCC feature sets (`mfcc_train_data.json`, `mfcc_test_data.json`).
- `docs/` – Project documentation, including this file, workflow guides, strict-classification guide, and expansion notes.
- `logs/` – TensorBoard event files generated during notebook training runs (under `logs/train/`).
- `models/` – Saved Keras checkpoints (`model1.keras`, `model2.keras`, `encoder.keras`, histories) plus a legacy `models/model.h5` snapshot.
- `notebooks/` – End-to-end pipeline notebooks for feature extraction, model training, evaluation, archive classification, and demos.
- `results/` – Training visualisations (`accuracy.png`, `loss.png`, `model2_accuracy.png`, `model2_loss.png`).
- `scripts/` – Python and shell utilities for dataset curation, archive analysis, and notebook maintenance.
- `TestData/` – Evaluation split with 18 high-precision categories and **810** samples populated by `scripts/populate_test_data.py`.
- `TrainingData/AudioSamples/` – Strictly curated training split covering 34 instrument categories populated via `scripts/strict_populate_training.py`.
- Root reference files: `STRICT_POPULATE_README.md`, `TEST_DATA_SUMMARY.md`, and automation artefacts such as `tmp.txt`.

## Data Repositories

### Training & Test Splits

- **TrainingData/AudioSamples/** – Holds ~10.8k WAV files filtered by the EXTREMELY STRICT rules described in `docs/STRICT_CLASSIFICATION_GUIDE.md`. Categories span core drum kit pieces, cymbals, hand percussion, Latin/world percussion, melodic pitched instruments, and special/FX groupings (34 total).
- **TestData/** – Generated from TrainingData using the same strict criteria but with tighter thresholds (20% draw, max 100 files). `TEST_DATA_SUMMARY.md` documents the populated categories (e.g., Kick/Snare/Tom at 100 files each; Hihat/Crash/Ride limited by availability; Percussion, Bell, Rim, Cowbell, etc.) and skipped classes when fewer than 50 strict matches exist. Regenerate with `python3 scripts/populate_test_data.py`.

### Source Archives

- **complete_drum_archive/** – Vendor-based folder tree (Access, Akai, Roland, Yamaha, …) used as the raw source for strict curation. Use `scripts/strict_populate_training.py` or `scripts/organize_drum_archive.py` to pull instrument-specific subsets from this archive.
- **ClassifiedArchive/** – Output staging area for running models against an unsorted library (e.g., `complete_drum_archive/`). Files are renamed `{instrument}_{confidence}_{original}.wav` and grouped into instrument folders after classification demos.

## Experiments, Models & Results

### Notebooks

- `MFCC_Feature_Extractor.ipynb` – Stage 1: Extract 40-coefficient MFCC features for Training/Test splits and store them in `data/`.
- `Model1_Train.ipynb` – CNN classifier trained directly on MFCC maps (6-class workflow; extendible to expanded taxonomy).
- `Model2_Train.ipynb` – Autoencoder-assisted classifier (trains encoder + classifier; saves `encoder.keras` and `model2.keras`).
- `Model_Evaluation.ipynb` – Compares Model 1 & Model 2 performance, generates confusion matrices, and logs metrics to `results/`.
- `PracticalDemo.ipynb` – Loads trained weights, processes files in `complete_drum_archive/`, and writes classified results into `ClassifiedArchive/` with confidence-ranked filenames.
- `ArchiveClassifier.ipynb` – Archive-scale experimentation on the curated datasets.

### Models & Training Artefacts

- `models/` contains the latest saved Keras weights (`model1.keras`, `model2.keras`, `encoder.keras`), alongside training history JSON exports and a nested `models/model.h5` legacy checkpoint.
- `results/` captures accuracy/loss curves for both neural-network configurations.
- `logs/train/` stores TensorBoard event files generated during notebook runs for visual analytics.

## Automation Scripts

- `scripts/strict_populate_training.py` – EXTREMELY STRICT TrainingData generator with validation, logging, and copy modes. Consult `STRICT_POPULATE_README.md` and `docs/STRICT_CLASSIFICATION_GUIDE.md` for rules and usage.
- `scripts/populate_test_data.py` – Creates the strict TestData split (18 categories, 810 samples) from TrainingData with tunable thresholds.
- `scripts/organize_drum_archive.py` – Original archive-to-training copier that leverages folder names and regex patterns for broader (less strict) collection.
- `scripts/deep_folder_analysis.py` – Audits TrainingData folders for token crossovers, highlighting potential mislabelled files.
- `scripts/inspect_catchment.py` – Samples TrainingData directories to surface ambiguous filenames containing multiple instrument tokens.
- `scripts/setup_directories.py` – Initializes project folders (`complete_drum_archive/`, checks TrainingData/TestData) and reports instrument counts.
- `scripts/update_notebook_paths.py` – Rewrites notebook asset paths so they reference the reorganized `data/`, `models/`, and `results/` locations.
- `scripts/run_strict_examples.sh` – Interactive shell walkthrough for running the strict population script (validation, logging, copy modes).

## Documentation

- `docs/WORKFLOW_GUIDE.md` – End-to-end instructions from data preparation through classification.
- `docs/STRICT_CLASSIFICATION_GUIDE.md` – Complete rulebook for strict token-based classification.
- `docs/EXPANSION_NOTES.md` – Notes on expanding the classifier to six core drum-kit classes.
- `docs/ARCHIVE_ORGANIZATION.md` – Detailed counts per category within the complete drum archive.
- `TEST_DATA_SUMMARY.md` – Breakdown of populated test categories and thresholds.
- Additional references include the academic report (`PatternRecognitionProjectReport.pdf`) and supporting workflow documents.

## Related Resources & Notes

- `STRICT_POPULATE_README.md` mirrors quick-start commands for the strict training population script.
- `logs/` and `results/` are safe to clear/regenerate when retraining models; they pair with the notebooks above.
- Maintain the project root as the working directory when running notebooks or scripts so relative paths resolve correctly.
