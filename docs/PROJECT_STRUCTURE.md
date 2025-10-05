# MLAudioClassifier Project Structure

## Overview
This document describes the organized file structure of the MLAudioClassifier project.

## Directory Structure

### `/notebooks/`
Contains all Jupyter notebooks for the project:
- `MFCC_Feature_Extractor.ipynb` - Stage 1: Extract MFCC features from audio
- `Model1_Train.ipynb` - Train the first CNN model
- `Model2_Train.ipynb` - Train the second model with autoencoder
- `Model_Evaluation.ipynb` - Evaluate and compare models
- `PracticalDemo.ipynb` - Demonstration notebook
- `ArchiveClassifier.ipynb` - Archive classification notebook

### `/models/`
Contains trained model files:
- `model.keras` - First CNN model
- `model2.keras` - Second model with autoencoder
- `encoder.keras` - Autoencoder model

### `/data/`
Contains processed data files:
- `mfcc_train_data.json` - Training MFCC features
- `mfcc_test_data.json` - Testing MFCC features

### `/docs/`
Contains documentation:
- `README.md` - Main project README
- `EXPANSION_NOTES.md` - Notes on project expansion
- `WORKFLOW_GUIDE.md` - Workflow documentation
- `PatternRecognitionProjectReport.pdf` - Academic paper
- `PROJECT_STRUCTURE.md` - This file

### `/results/`
Contains output images and results:
- `accuracy.png` - Model accuracy plots
- `loss.png` - Model loss plots

### `/scripts/`
Contains utility scripts:
- `setup_directories.py` - Directory setup script
- `update_notebook_paths.py` - Path update utility

### `/TrainingData/`
Contains training audio samples organized by instrument class:
- `AudioSamples/` - Subdirectories for each instrument (Crash, Hihat, Kick, Ride, Snare, Tom)

### `/TestData/`
Contains test audio samples organized by instrument class:
- Subdirectories for each instrument (Crash, Hihat, Kick, Ride, Snare, Tom)

### `/logs/`
Contains TensorFlow training logs

### `/ClassifiedArchive/`
Contains classified drum samples (output from classification)

## Workflow

1. **Feature Extraction**: Run `MFCC_Feature_Extractor.ipynb` to generate MFCC features
   - Reads from: `TrainingData/` and `TestData/`
   - Writes to: `data/mfcc_train_data.json` and `data/mfcc_test_data.json`

2. **Model Training**: Run `Model1_Train.ipynb` and/or `Model2_Train.ipynb`
   - Reads from: `data/mfcc_train_data.json`
   - Writes to: `models/model.keras` or `models/model2.keras`
   - Generates: `results/accuracy.png` and `results/loss.png`

3. **Model Evaluation**: Run `Model_Evaluation.ipynb`
   - Reads from: `data/mfcc_test_data.json` and `models/*.keras`
   - Evaluates model performance

## Notes

- All file paths in notebooks have been updated to reflect this new structure
- The project root should be set as the working directory when running notebooks
- Model files are saved in HDF5 format (.keras)
- Data files are saved in JSON format for easy inspection
