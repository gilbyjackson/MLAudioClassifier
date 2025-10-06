"""
Drum Sample Classifier Package
===============================

A production-ready audio classification system for organizing drum sample archives.

Modules:
    io: File discovery, hashing, JSONL I/O
    features: Audio loading and feature extraction (MFCC, spectral)
    model: Model loading, label mapping, calibration
    infer: Batch inference and probability post-processing
    rebuild: Archive regeneration from index files
"""

__version__ = "0.1.0"

from classifier import io, features, model, infer, rebuild

__all__ = ["io", "features", "model", "infer", "rebuild"]
