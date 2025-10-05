#!/usr/bin/env python3
import json
import os

# Path mappings
path_mappings = {
    'mfcc_train_data.json': 'data/mfcc_train_data.json',
    'mfcc_test_data.json': 'data/mfcc_test_data.json',
    'model.keras': 'models/model.keras',
    'model2.keras': 'models/model2.keras',
    'encoder.keras': 'models/encoder.keras',
    'accuracy.png': 'results/accuracy.png',
    'loss.png': 'results/loss.png',
}

notebooks_dir = '../notebooks'
notebooks = [
    'MFCC_Feature_Extractor.ipynb',
    'Model1_Train.ipynb',
    'Model2_Train.ipynb',
    'Model_Evaluation.ipynb',
    'PracticalDemo.ipynb',
    'ArchiveClassifier.ipynb'
]

for notebook_name in notebooks:
    notebook_path = os.path.join(notebooks_dir, notebook_name)
    
    with open(notebook_path, 'r') as f:
        notebook = json.load(f)
    
    # Update all cells
    for cell in notebook['cells']:
        if 'source' in cell:
            for i, line in enumerate(cell['source']):
                for old_path, new_path in path_mappings.items():
                    if old_path in line:
                        cell['source'][i] = line.replace(old_path, new_path)
    
    with open(notebook_path, 'w') as f:
        json.dump(notebook, f, indent=1)
    
    print(f"Updated {notebook_name}")

print("All notebooks updated!")
