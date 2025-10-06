#!/usr/bin/env python3
"""
Setup script for MLAudioClassifier
Creates the necessary directory structure for unsorted sample classification
"""

import os

def setup_directories():
    """Create the necessary directory structure"""
    
    # Get current directory
    project_dir = os.getcwd()
    print(f"Setting up directories in: {project_dir}")
    
    # Create complete_drum_archive directory for unsorted samples
    sample_lib = "complete_drum_archive"
    if not os.path.exists(sample_lib):
        os.makedirs(sample_lib)
        print(f"✅ Created {sample_lib}/ directory")
        print(f"   → Place your unsorted .wav files here")
    else:
        print(f"✅ {sample_lib}/ directory already exists")
    
    # Check for required training data structure
    training_data = "TrainingData/AudioSamples"
    if os.path.exists(training_data):
        print(f"✅ Found {training_data}/ directory")
        
        # Check for instrument folders
        instruments = ["Crash", "Hihat", "Kick", "Ride", "Snare", "Tom"]
        missing_folders = []
        
        for instrument in instruments:
            folder_path = os.path.join(training_data, instrument)
            if os.path.exists(folder_path):
                file_count = len([f for f in os.listdir(folder_path) if f.endswith('.wav')])
                print(f"   → {instrument}/: {file_count} samples")
            else:
                missing_folders.append(instrument)
        
        if missing_folders:
            print(f"⚠️  Missing training folders: {', '.join(missing_folders)}")
    else:
        print(f"⚠️  Training data not found at {training_data}/")
        print("   You'll need training data organized by instrument type to train the model")
    
    # Check for test data
    test_data = "TestData"
    if os.path.exists(test_data):
        print(f"✅ Found {test_data}/ directory")
    else:
        print(f"⚠️  Test data not found at {test_data}/")
    
    print("\n" + "="*50)
    print("SETUP COMPLETE")
    print("="*50)
    print("\nNext steps:")
    print("1. Add your sorted training samples to TrainingData/AudioSamples/[Instrument]/")
    print("2. Run MFCC_Feature_Extractor.ipynb")
    print("3. Run Model1_Train.ipynb or Model2_Train.ipynb")
    print("4. Add unsorted samples to complete_drum_archive/")
    print("5. Run PracticalDemo.ipynb to classify them!")

if __name__ == "__main__":
    setup_directories()