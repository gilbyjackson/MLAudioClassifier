python scripts/setup_directories.py  # create complete_drum_archive and verify training/test folders
python scripts/populate_test_data.py  # refresh strict test data subset
python scripts/strict_populate_training.py  # curate strict training splits
python scripts/organize_drum_archive.py  # move classified samples into archive folders
python scripts/deep_folder_analysis.py  # summarize archive contents