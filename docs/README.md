# MLAudioClassifier

Classify drum and percussion one-shots with a pair of deep learning pipelines backed by rigorously curated datasets. This README consolidates the full project knowledge base: data sources, strict curation scripts, notebooks, models, workflow, troubleshooting, and supporting documentation.

- 🎯 **Purpose**: Label short percussion recordings and sort sample libraries automatically.
- 🧠 **Models**: CNN classifier trained on MFCC features and an autoencoder-assisted classifier.
- 🗂️ **Data Pipeline**: EXTREMELY STRICT filename-based curation yields high-precision training and test splits.
- 📦 **Artifacts**: Saved Keras weights, MFCC datasets, TensorBoard logs, accuracy/loss plots.
- 📚 **Docs & Scripts**: Comprehensive guides for strict classification, workflow automation, and archive analysis.

## Table of Contents

1. [Project Snapshot](#project-snapshot)
2. [Environment & Setup](#environment--setup)
3. [Strict Dataset Pipeline](#strict-dataset-pipeline)
4. [Training & Evaluation Workflow](#training--evaluation-workflow)
5. [Classification Workflows](#classification-workflows)
6. [Repository Map](#repository-map)
7. [Scripts Reference](#scripts-reference)
8. [Notebooks](#notebooks)
9. [Data Highlights](#data-highlights)
10. [Results & Monitoring](#results--monitoring)
11. [Troubleshooting](#troubleshooting)
12. [Documentation & Resources](#documentation--resources)
13. [License & Attribution](#license--attribution)

## Quick Start (Production)

**Ready to classify your drum archive?** The project now includes a production-ready CLI:

```bash
# 1. Activate environment
source .venv/bin/activate

# 2. Run full archive inference (~4 min for 47K files)
python -m classifier.cli infer --config config.yml

# 3. Generate organized archive
python -m classifier.cli rebuild \
  --index ClassifiedArchive/run_<timestamp>/index.jsonl \
  --out RegeneratedArchive
```

**Result:** `RegeneratedArchive/{Crash,Hihat,Kick,Ride,Snare,Tom,misc}/` with comprehensive manifests.

📖 **See [`QUICKSTART.md`](../QUICKSTART.md) for complete usage guide.**

## Project Snapshot

| Item | Details |
| --- | --- |
| Core Task | Multi-class classification of drum/percussion one-shots |
| Classes | **34-class full taxonomy** with canonical collapse to 6 core drums (Crash, Hihat, Kick, Ride, Snare, Tom) + misc |
| Feature Representation | 40-coefficient MFCCs extracted from 50,000-sample, 44.1 kHz mono clips |
| Models | `model1` (34-class CNN), `model2` (6-class autoencoder), `encoder` (shared feature extractor) |
| Architecture | **Two-phase pipeline**: inference → JSONL index → organized archive |
| Evaluation | Strict `TestData/` split (18 categories, 810 files) + saved accuracy/loss curves |
| Production Usage | **CLI package** with streaming, deduplication, configuration, and regeneration |
| Output | Organized archives: `{Crash,Hihat,Kick,Ride,Snare,Tom,misc}/` + manifests + statistics |

## Environment & Setup

1. **Clone the repository** and ensure you are working from the project root:

   ```bash
   git clone <your-fork-url>
   cd MLAudioClassifier
   ```

2. **Python environment**: Python 3.10+ with TensorFlow/Keras, Librosa, NumPy, Pandas, Matplotlib, and Jupyter.
3. **Verify directory scaffold** (creates `complete_drum_archive/` and checks strict dataset folders):

   ```bash
   python3 scripts/setup_directories.py
   ```

4. **Source data**: Place the vendor-organized `complete_drum_archive/` (20,086 samples across 34 categories) inside the repo root. See `docs/ARCHIVE_ORGANIZATION.md` for counts per instrument group.

## Strict Dataset Pipeline

The strict pipeline enforces explicit filename tokens, forbidden token filters, ambiguity rejection, and reproducible logging. Quick-reference commands live in `STRICT_POPULATE_README.md`; rules are detailed in `docs/STRICT_CLASSIFICATION_GUIDE.md`.

### 1. Build `TrainingData/AudioSamples/`

```bash
# 1. Preview classifications (no copying)
python3 scripts/strict_populate_training.py --validate-only

# 2. Capture accepted/rejected logs in logs/
python3 scripts/strict_populate_training.py --validate-only --save-logs

# 3. Copy strict matches into TrainingData (cleans folders first)
python3 scripts/strict_populate_training.py --copy
```

- Acceptance snapshot (Oct 2025 run): 46,962 files scanned → 10,791 accepted (~23%) across 34 strict categories.
- Optional audits: `python3 scripts/deep_folder_analysis.py` and `python3 scripts/inspect_catchment.py` surface crossover tokens and ambiguous names.
- Need a broader sweep? Use `python3 scripts/organize_drum_archive.py` (folder-aware, less strict).

### 2. Build `TestData/`

```bash
python3 scripts/populate_test_data.py
```

- Target: ≈20% sample per category (max 100 files) requiring ≥50 strict matches.
- Outcome (see `TEST_DATA_SUMMARY.md`): 18 categories populated, 810 samples total.
  - Core kit: Kick/Snare/Tom (100 each), Hihat (46), Crash (38), Ride (36)
  - Percussion highlights: Perc (96), Clap (74), Rim (37), Cowbell (26), Bell (16)
  - Skipped when strict matches <50: Cabasa, Clave, Agogo, Guiro, China, Splash, Whistle, Cuica, Woodblock, Metal, Timpani, Vibraslap
- Adjust thresholds by editing `scripts/populate_test_data.py` (`min_needed` check) if you need lower counts.

## Training & Evaluation Workflow

1. **Feature Extraction** – `notebooks/MFCC_Feature_Extractor.ipynb`
   - Inputs: `TrainingData/AudioSamples/`, `TestData/`
   - Outputs: `data/mfcc_train_data.json`, `data/mfcc_test_data.json`

2. **Train Model 1** – `notebooks/Model1_Train.ipynb`
   - Direct MFCC CNN (6-class by default)
   - Saves `models/model1.keras`, `models/model1_history.json`, TensorBoard logs (if enabled)

3. **Train Model 2** – `notebooks/Model2_Train.ipynb`
   - Autoencoder encoder + classifier
   - Saves `models/encoder.keras`, `models/model2.keras`, `models/model2_history.json`

4. **Evaluate** – `notebooks/Model_Evaluation.ipynb`
   - Generates accuracy/loss plots (`results/*.png`)
   - Produces confusion matrices for the 6-class drum kit problem

5. **Monitor** – Load TensorBoard with `logs/train/` to inspect training runs.

## Classification Workflows

### Production Classifier Package (Recommended)

The project now includes a production-ready CLI classifier with two-phase pipeline architecture for maximum flexibility and performance:

**Phase 1: Inference (Generate Index)**

```bash
# Activate environment
source .venv/bin/activate

# Run full archive inference
python -m classifier.cli infer --config config.yml

```

- Processes complete_drum_archive (~47K files in ~4 minutes)
- Outputs streaming JSONL index: `ClassifiedArchive/run_<timestamp>/index.jsonl`
- Includes per-file predictions, confidence, audio metadata, and deduplication

**Phase 2: Rebuild (Organize Archive)**

```bash
# Generate organized archive from index
python -m classifier.cli rebuild \

  --index ClassifiedArchive/run_<timestamp>/index.jsonl \
  --out RegeneratedArchive
```

- Instant reorganization without re-inference

- Outputs: `RegeneratedArchive/{Crash,Hihat,Kick,Ride,Snare,Tom,misc}/`
- Includes manifests and summary statistics

**Additional Commands:**

```bash
# View classification statistics
python -m classifier.cli stats --index ClassifiedArchive/run_<timestamp>/index.jsonl

# Validate label mapping
python -m classifier.cli validate-mapping


# Create label mapping template
python -m classifier.cli create-stub
```

**Key Features:**

- **34-class model** with canonical collapse to 6 core drums + misc
- **Hash-based deduplication** prevents processing identical files
- **Configurable thresholds** for confidence-based routing

- **Override support** for manual corrections
- **Comprehensive logging** with error cause tracking

### Interactive Notebooks

#### Practical Demo (`notebooks/PracticalDemo.ipynb`)

1. Drop unsorted `.wav` files into `complete_drum_archive/`.
2. Choose a trained model (Model 1 or Model 2) within the notebook.

3. Execute cells to normalize audio, extract MFCCs, predict, and sort outputs.
4. Results land in `ClassifiedArchive/<Instrument>/` with confidence in filenames.

#### Archive Experiments (`notebooks/ArchiveClassifier.ipynb`)

Enhanced notebook with mirror directory structure support and dynamic label loading. Configure paths per notebook instructions.

#### Utility Notebooks

- **`ValidateMapping.ipynb`** - Check label mapping against model output
- **`ExtractTrainingLabels.ipynb`** - Recover training label order from data
- **`TestClassifier.ipynb`** - Test classifier package functionality

## Repository Map

| Path | Purpose |
| --- | --- |
| `classifier/` | **Production classifier package** with CLI, streaming JSONL, and two-phase pipeline |
| `ClassifiedArchive/` | JSONL index files and organized archive outputs |
| `complete_drum_archive/` | Vendor-organized master archive (source for strict scripts) |
| `config.yml` | **Centralized YAML configuration** for classifier package |
| `data/` | Serialized MFCC datasets (`mfcc_train_data.json`, `mfcc_test_data.json`) |
| `docs/` | Documentation (workflow, strict guide, archive stats, project structure, academic report) |
| `logs/train/` | TensorBoard event files for recent training sessions |
| `models/` | Saved Keras weights, **label mappings**, and canonical collapse rules |
| `notebooks/` | Pipeline notebooks (training, evaluation, demos) + **new utility notebooks** |
| `results/` | Accuracy/loss curve images for quick comparison |
| `scripts/` | Python/shell utilities for strict curation, analysis, scaffolding, and notebook maintenance |
| `TestData/` | Strict evaluation split (18 categories, 810 samples) populated via `populate_test_data.py` |
| `TrainingData/AudioSamples/` | Strict training dataset (≈10.8k samples across 34 categories) |
| `QUICKSTART.md`, `IMPLEMENTATION_STATUS.md` | **Production usage guides** and technical documentation |

## Scripts Reference

### Production Classifier CLI

| Command | Description |
| --- | --- |
| `python -m classifier.cli infer` | **Run full archive inference** with streaming JSONL output and deduplication |
| `python -m classifier.cli rebuild` | **Regenerate organized archive** from existing index with configurable parameters |
| `python -m classifier.cli stats` | **View classification statistics** (distribution, confidence, duration, errors) |
| `python -m classifier.cli validate-mapping` | **Check label mapping** against model output dimension |
| `python -m classifier.cli create-stub` | **Generate label mapping template** for manual editing |

### Utility Scripts

| Script | Description |
| --- | --- |
| `strict_populate_training.py` | EXTREMELY STRICT dataset builder with validation mode, logging, copy, and configurable source/target paths |
| `populate_test_data.py` | Creates strict TestData subset with explicit token checks and quota enforcement |
| `organize_drum_archive.py` | Original folder-aware archive copier (less strict, higher recall) |
| `extract_training_labels.py` | **Recover training label order** from MFCC JSON or directory structure |
| `validate_mapping.py` | **Standalone label validation** with auto-stub creation |
| `test_classifier.py` | **Test classifier package** functionality (imports, discovery, features, model) |

| `deep_folder_analysis.py` | Reports cross-category token collisions inside `TrainingData/AudioSamples/` |
| `inspect_catchment.py` | Samples ambiguous filenames to spot potential misclassifications |
| `setup_directories.py` | Initializes `complete_drum_archive/` and verifies training/test directories with instrument counts |
| `update_notebook_paths.py` | Rewrites notebook asset paths to match the current repo structure |
| `run_strict_examples.sh` | Interactive shell walkthrough of strict population commands |

## Notebooks

### Training & Evaluation

| Notebook | Role |
| --- | --- |
| `MFCC_Feature_Extractor.ipynb` | Generate MFCC feature datasets for training and evaluation |
| `Model1_Train.ipynb` | Train CNN classifier directly on MFCC features |

| `Model2_Train.ipynb` | Train autoencoder encoder + classifier stack |
| `Model_Evaluation.ipynb` | Compare model performance, produce confusion matrices & plots |

### Classification & Demos

| Notebook | Role |
| --- | --- |
| `PracticalDemo.ipynb` | Sort unsorted sample libraries using trained models |
| `ArchiveClassifier.ipynb` | Large-scale archive classification experiments (enhanced with mirroring) |

### Utilities & Validation

| Notebook | Role |
| --- | --- |
| `ValidateMapping.ipynb` | **Check label mapping** against model output dimension |
| `ExtractTrainingLabels.ipynb` | **Recover training labels** from MFCC JSON or directory structure |
| `TestClassifier.ipynb` | **Test classifier package** functionality with visual pass/fail results |

## Data Highlights

- **Archive Counts** (`docs/ARCHIVE_ORGANIZATION.md`):
  - Drum Kit (6 categories): Kick 2,427 · Snare 3,996 · Tom 3,084 · Hihat 1,408 · Crash 489 · Ride 667
  - Cymbals (4 categories): China 56 · Splash 39 · Cymbal 666 · Sizzle 4 · Bell 382
  - Hand Percussion (6 categories): Clap 800 · Tambourine 155 · Shaker 218 · Maracas 80 · Cabasa 118 · Triangle 91
  - Latin/World (6 categories): Conga 525 · Bongo 227 · Timbale 130 · Clave 186 · Agogo 84 · Guiro 96
  - Melodic/Pitched (5 categories): Cowbell 188 · Woodblock 59 · Timpani 33 · Metal 33 · Rim 482
  - Special/Sound Design: Perc 865 · Whistle 68 · Cuica 49 · Vibraslap 24 · FX 2,073 · Vox 284
- **Strict TestData Snapshot** (`TEST_DATA_SUMMARY.md`): Balanced draw emphasizing 6-class core kit + key percussion, with thresholds to avoid noisy categories.
- **Classification Naming**: `{instrument}_{confidence}_{original_name}.wav` (e.g., `kick_0.923_BD_001.wav`).

## Results & Monitoring

- Training metrics saved under `results/` (`accuracy.png`, `loss.png`, `model2_accuracy.png`, `model2_loss.png`).
- TensorBoard event logs (`logs/train/events.out.tfevents.*`) provide epoch-by-epoch inspection. Launch with:

  ```bash
  tensorboard --logdir logs/train
  ```

- `ClassifiedArchive/metadata/` (when enabled) stores per-file predictions and confidences for downstream QA.

## Troubleshooting

| Issue | Likely Cause | Fix |
| --- | --- | --- |
| No files copied by strict script | Filenames missing explicit tokens or hitting forbidden lists | Review rejection logs (`--save-logs`), adjust `STRICT_CATEGORIES`, or fall back to `organize_drum_archive.py` |
| Missing TestData categories | Strict matches <50 | Lower the `min_needed` threshold in `populate_test_data.py` or expand TrainingData |
| Notebook path errors | Running outside repo root | `cd /Users/Gilby/Projects/MLAudioClassifier` or run `update_notebook_paths.py` |
| Low classification confidence | Distribution shift between complete_drum_archive and TrainingData | Add similar samples to TrainingData, rerun strict pipeline, regenerate MFCCs, retrain |
| Slow strict run on huge archives | Processing >100k files | Run overnight or limit `--source` to subset directories |

## Documentation & Resources

- `docs/PROJECT_STRUCTURE.md` – Current repository layout and artefact overview
- `docs/WORKFLOW_GUIDE.md` – Step-by-step instructions (mirrors this README with additional detail)
- `docs/STRICT_CLASSIFICATION_GUIDE.md` – Token rules, forbidden lists, logging outputs, customization tips
- `docs/ARCHIVE_ORGANIZATION.md` – Aggregate stats for the vendor archive
- `TEST_DATA_SUMMARY.md` – Detailed population results for strict TestData
- `STRICT_POPULATE_README.md` – Quick-start strict script commands
- `docs/EXPANSION_NOTES.md` – Notes on expanding from 3 to 6 drum classes
- `PatternRecognitionProjectReport.pdf` – Academic write-up

## License & Attribution

- Distributed under the MIT License – see `LICENSE` for details.
- Original project by Nathan Heck (UF EEL6825 Pattern Recognition). Current iteration includes strict dataset tooling, extended documentation, and workflow automation maintained in this fork.
- Acknowledgements: UF ECE Department, advisors, and the broader audio ML community whose open datasets inspired the archive.
