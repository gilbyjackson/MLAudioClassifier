# ML Audio Classifier - GitHub Copilot Instructions

## Project Overview
This project implements machine learning models for classifying drum and percussion audio samples. It features:
- MFCC and spectrogram feature extraction pipelines
- Two model architectures (direct MFCC-based and autoencoder-based)
- Production-ready archive classifier with batching and optimization
- Support for 6 primary instrument classes: Crash, Hihat, Kick, Ride, Snare, Tom

## Repository Structure
- `notebooks/`: Jupyter notebooks implementing the workflow
  - `MFCC_Feature_Extractor.ipynb`: Extracts MFCC features from audio files
  - `Model1_Train.ipynb`: Trains a model directly on MFCC features
  - `Model2_Train.ipynb`: Uses an autoencoder approach with spectrograms
  - `Model_Evaluation.ipynb`: Compares both models' performance
  - `ArchiveClassifier.ipynb`: Production tool for classifying large audio archives
- `data/`: Preprocessed data (MFCC features in JSON format)
- `models/`: Saved Keras models and training history
- `results/`: Training visualizations and performance metrics
- `TrainingData/AudioSamples/`: Training audio samples by instrument class
- `TestData/`: Test audio samples by instrument class

## Dependencies
Primary libraries:
- `numpy`, `pandas`, `matplotlib` (data handling and visualization)
- `librosa` (audio processing and feature extraction)
- `keras`/`tensorflow` (model development)
- `scikit-learn` (evaluation metrics)
- `soundfile` (audio I/O)
- `tqdm` (progress tracking for long operations)

## Workflow
1. **Feature Extraction** → Extract MFCC features or spectrograms from audio samples
2. **Model Training** → Train classifiers using either direct features or autoencoder
3. **Evaluation** → Compare models using accuracy metrics and confusion matrices
4. **Archive Classification** → Apply trained models to large audio archives

## Data Preprocessing Standards
- **Audio Parameters**:
  - MFCC pipeline: sr=44100Hz, fixed length=50000 samples
  - Spectrogram pipeline: sr=22050Hz, fixed length=32600 samples
- **Feature Extraction**:
  - MFCC: n_mfcc=40, n_fft=2048, hop_length=512
  - Spectrogram: n_fft=512, hop_length=256
- **Normalization**: Applied to all extracted features

## Model Architectures

### Model 1 (MFCC-based)
```python
model = keras.Sequential([
    # input layer
    keras.layers.Flatten(input_shape=(X.shape[1], X.shape[2])),
    # hidden layers
    keras.layers.Dense(512, activation='relu'),
    keras.layers.Dropout(0.3),
    keras.layers.Dense(256, activation='relu'),
    keras.layers.Dropout(0.3),
    keras.layers.Dense(128, activation='relu'),
    keras.layers.Dropout(0.3),
    # output layer
    keras.layers.Dense(num_classes, activation='softmax')
])
```

### Model 2 (Autoencoder-based)
1. Autoencoder for dimensionality reduction:
```python
# Encoder
x = Conv2D(16, (3, 3), activation='relu', padding='same')(input_img)
x = MaxPooling2D((2, 2), padding='same')(x)
x = Conv2D(8, (3, 3), activation='relu', padding='same')(x)
x = MaxPooling2D((2, 2), padding='same')(x)
x = Conv2D(8, (3, 3), activation='relu', padding='same')(x)
encoded = MaxPooling2D((2, 2), padding='same')(x)
```

2. Classification on encoded features (similar to Model 1)

## Code Patterns

### Audio Loading and Feature Extraction
```python
def load_and_preprocess(path: Path) -> Tuple[np.ndarray, Dict[str, Any]]:
    """Load audio and compute MFCC feature tensor plus metadata."""
    try:
        y, sr = safe_load_audio(path)
        if len(y) < TARGET_SAMPLES:
            y = librosa.util.fix_length(y, size=TARGET_SAMPLES)
        else:
            y = y[:TARGET_SAMPLES]
        mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=N_MFCC, n_fft=N_FFT, hop_length=HOP_LENGTH)
        if NORMALIZE:
            mfcc = librosa.util.normalize(mfcc)
        return mfcc, {'error': None, 'orig_sr': sr}
    except Exception as e:
        return None, {'error': str(e)}
```

### Model Training
```python
callbacks = [
    EarlyStopping(monitor='val_loss', patience=5, restore_best_weights=True),
    ReduceLROnPlateau(monitor='val_loss', factor=0.5, patience=3, verbose=1)
]

history = model.fit(
    X_train, y_train,
    validation_data=(X_val, y_val),
    batch_size=32,
    epochs=50,
    callbacks=callbacks,
    verbose=1
)
```

### Batch Processing
```python
def classify_batch(batch_paths: List[Path]) -> None:
    feats = []
    valid_paths = []
    for p in batch_paths:
        feat, meta = load_and_preprocess(p)
        if feat is None:
            errors.append({'file': str(p), 'error': meta['error']})
            continue
        feats.append(feat)
        valid_paths.append(p)
    if not feats:
        return
    X = batch_tensorize(feats)
    probs = model.predict(X, verbose=0)
    # Process predictions...
```

## Optimization Goals
- **Memory Efficiency**: Batch processing for large archives
- **Performance**: Parallel feature extraction where possible
- **Deduplication**: Hash-based detection of identical audio files
- **Robustness**: Error handling for corrupt/invalid audio files
- **Reproducibility**: Metadata generation for classification runs

## Preferred Coding Styles
- **Type Hints**: Use for function signatures
- **Error Handling**: Try/except with specific error details
- **Logging**: Progress bars with tqdm for long operations
- **Variable Naming**: Descriptive names related to audio/ML domains
- **Comments**: Document key parameters and algorithmic choices
- **Notebook Structure**: Markdown cells explaining major steps

## Audio Processing Domain Knowledge
- **MFCC**: Mel-frequency cepstral coefficients, compact spectrum representation
- **Spectrogram**: Visual frequency/time representation
- **Sample Rate**: Samples per second (44.1kHz standard, 22.05kHz for efficiency)
- **n_fft**: FFT window size affecting frequency resolution
- **hop_length**: Frame step size affecting temporal resolution
- **Normalization**: Feature scaling for improved model training

## Common Issues & Solutions
- **Class Imbalance**: Use stratification in train_test_split
- **Model Overfitting**: Implement Dropout and Early Stopping
- **Audio Length Variation**: Fix length with librosa.util.fix_length
- **Label Consistency**: Ensure contiguous 0...N-1 class indices
- **Memory Limitations**: Implement batching for large archives