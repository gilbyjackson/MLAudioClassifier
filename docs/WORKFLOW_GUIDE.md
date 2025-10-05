# Complete Workflow: From Training to Classifying Unsorted Data

## Overview
This guide walks you through the complete process of training the model with sorted data and then using it to classify your unsorted data bank.

## 📁 Data Structure Setup

### Step 1: Organize Your Training Data
Your training data should be organized like this:
```
TrainingData/AudioSamples/
├── Crash/          # Crash cymbal samples
├── Hihat/          # Hi-hat samples  
├── Kick/           # Kick drum samples
├── Ride/           # Ride cymbal samples
├── Snare/          # Snare drum samples
└── Tom/            # Tom drum samples
```

### Step 2: Prepare Unsorted Data Directory
Create a `SampleLib/` folder for your unsorted samples:
```
SampleLib/          # Put all your unsorted .wav files here
├── sample1.wav
├── sample2.wav
└── ...
```

### Step 3: Run Setup Script (Optional)
```bash
python setup_directories.py
```

## 🎯 Training Pipeline

### Step 1: Extract Features
Run `MFCC_Feature_Extractor.ipynb`:
- Processes all audio files in `TrainingData/AudioSamples/`
- Extracts MFCC features from each sample
- Creates labeled dataset for training
- Saves features to `mfcc_train_data.json` and `mfcc_test_data.json`

### Step 2: Train Model
Choose one (or both) training approaches:

**Option A: Model 1 (Direct MFCC Classification)**
- Run `Model1_Train.ipynb`
- Trains CNN directly on MFCC features
- Saves trained model as `model.keras`

**Option B: Model 2 (Autoencoder + Classification)**  
- Run `Model2_Train.ipynb`
- Trains autoencoder for feature extraction
- Trains classifier on encoded features
- Saves `encoder.keras` and `model2.keras`

### Step 3: Evaluate Performance (Optional)
- Run `Model_Evaluation.ipynb`
- Compares both models' performance
- Generates confusion matrices

## 🔄 Classification Pipeline

### Step 4: Classify Unsorted Data
Run `PracticalDemo.ipynb`:

1. **Loads** your trained model
2. **Processes** each `.wav` file in `SampleLib/`
3. **Predicts** instrument class with confidence score
4. **Organizes** files into folders:
   ```
   SampleLib/
   ├── Crash/
   │   └── crash_0.892_sample1.wav
   ├── Hihat/
   │   └── hihat_0.756_sample2.wav
   ├── Kick/
   ├── Ride/
   ├── Snare/
   └── Tom/
   ```

## 🎛️ Classification Details

### Input Processing
- Loads audio at 44.1kHz, mono
- Fixes length to 50,000 samples (~1.13 seconds)
- Extracts 40 MFCC coefficients
- Normalizes features

### Output Classes
- **0**: Crash cymbal
- **1**: Hi-hat
- **2**: Kick drum  
- **3**: Ride cymbal
- **4**: Snare drum
- **5**: Tom drum

### File Naming Convention
Classified files are renamed with format:
`{instrument}_{confidence}_{original_name}.wav`

Example: `kick_0.923_BD_001.wav`
- Instrument: kick
- Confidence: 92.3%
- Original: BD_001.wav

## 🔧 Troubleshooting

### Common Issues

**"Model not found"**
- Ensure you've run training notebooks first
- Check that `model.keras` exists in project directory

**"SampleLib not found"**
- Create `SampleLib/` folder
- Add your unsorted `.wav` files to it

**Low classification confidence**
- May indicate samples unlike training data
- Consider adding similar samples to training set and retraining

**Audio loading errors**
- Ensure files are valid audio formats (.wav recommended)
- Check sample rate and bit depth compatibility

## 💡 Tips for Better Results

1. **Balanced Training Data**: Use roughly equal numbers of samples per class
2. **Quality Training Data**: Use clean, representative samples
3. **Consistent Audio Format**: Stick to same sample rate/bit depth
4. **Review Low Confidence**: Manually check samples with confidence < 0.7
5. **Retrain if Needed**: Add misclassified samples to training data and retrain

## 🚀 Advanced Usage

### Batch Processing
For large datasets, consider modifying the classification loop to:
- Process files in batches
- Add progress bars
- Log results to file
- Handle different audio formats

### Custom Confidence Thresholds
Modify the demo to only move files above certain confidence:
```python
if confidence > 0.8:  # Only move high-confidence predictions
    shutil.move(wav, destination)
else:
    print(f"Low confidence ({confidence:.3f}), keeping in unsorted")
```

### Integration with DAWs
The classified samples can be easily imported into:
- Ableton Live (drag folders to browser)
- Logic Pro (add to sample library)
- FL Studio (add to browser)
- Pro Tools (import to workspace)