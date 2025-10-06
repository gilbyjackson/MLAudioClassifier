"""
Audio feature extraction utilities.

Handles loading audio files and computing MFCC and spectral features.
"""

import numpy as np
import librosa
import soundfile as sf
from pathlib import Path
from typing import Tuple, Dict, Any, Optional
import warnings

# Suppress repetitive librosa warnings
warnings.filterwarnings("ignore", category=UserWarning, module='librosa')


class AudioFeatureExtractor:
    """Extract MFCC and spectral features from audio files."""
    
    def __init__(
        self,
        target_sr: int = 44100,
        target_samples: int = 50_000,
        n_mfcc: int = 40,
        n_fft: int = 2048,
        hop_length: int = 512,
        normalize: bool = True,
        min_duration_sec: float = 0.05
    ):
        """
        Initialize feature extractor.
        
        Args:
            target_sr: Target sample rate
            target_samples: Fixed length in samples
            n_mfcc: Number of MFCC coefficients
            n_fft: FFT window size
            hop_length: Hop length for STFT
            normalize: Whether to normalize features
            min_duration_sec: Minimum audio duration
        """
        self.target_sr = target_sr
        self.target_samples = target_samples
        self.n_mfcc = n_mfcc
        self.n_fft = n_fft
        self.hop_length = hop_length
        self.normalize = normalize
        self.min_duration_sec = min_duration_sec
    
    def safe_load_audio(self, path: Path) -> Tuple[np.ndarray, int]:
        """
        Robustly load audio file.
        
        Tries soundfile first, falls back to librosa/audioread.
        
        Args:
            path: Audio file path
            
        Returns:
            (audio_array, sample_rate)
            
        Raises:
            Exception if loading fails
        """
        try:
            # Try soundfile first (fast, native)
            y, sr = sf.read(path)
            if y.ndim > 1:
                y = np.mean(y, axis=1)
            if sr != self.target_sr:
                y = librosa.resample(y, orig_sr=sr, target_sr=self.target_sr)
                sr = self.target_sr
            return y, sr
        except Exception:
            # Fallback to librosa (handles more formats)
            y, sr = librosa.load(path, sr=self.target_sr, mono=True)
            return y, sr
    
    def compute_audio_stats(self, y: np.ndarray, sr: int) -> Dict[str, float]:
        """
        Compute basic audio statistics.
        
        Args:
            y: Audio array
            sr: Sample rate
            
        Returns:
            Dictionary with duration_sec, rms, spectral_centroid, spectral_rolloff
        """
        duration = len(y) / sr
        rms = float(librosa.feature.rms(y=y).mean())
        
        # Convert to dB
        rms_db = 20 * np.log10(rms + 1e-10)
        
        # Spectral features
        spectral_centroid = float(librosa.feature.spectral_centroid(y=y, sr=sr).mean())
        spectral_rolloff = float(librosa.feature.spectral_rolloff(y=y, sr=sr).mean())
        
        return {
            'duration_sec': duration,
            'rms_db': rms_db,
            'spectral_centroid': spectral_centroid,
            'spectral_rolloff': spectral_rolloff
        }
    
    def extract_mfcc(
        self,
        path: Path,
        include_stats: bool = True
    ) -> Tuple[Optional[np.ndarray], Dict[str, Any]]:
        """
        Extract MFCC features from audio file.
        
        Args:
            path: Audio file path
            include_stats: Whether to compute audio statistics
            
        Returns:
            (mfcc_array, metadata_dict)
            Returns (None, error_dict) on failure
        """
        try:
            # Load audio
            y, sr = self.safe_load_audio(path)
            
            # Check minimum duration
            if len(y) < self.min_duration_sec * sr:
                return None, {'error': 'too_short'}
            
            # Fix length
            if len(y) < self.target_samples:
                y = librosa.util.fix_length(y, size=self.target_samples)
            else:
                y = y[:self.target_samples]
            
            # Compute MFCC
            mfcc = librosa.feature.mfcc(
                y=y,
                sr=sr,
                n_mfcc=self.n_mfcc,
                n_fft=self.n_fft,
                hop_length=self.hop_length
            )
            
            if self.normalize:
                mfcc = librosa.util.normalize(mfcc)
            
            # Metadata
            meta = {'error': None, 'orig_sr': sr}
            
            if include_stats:
                meta.update(self.compute_audio_stats(y, sr))
            
            return mfcc, meta
            
        except Exception as e:
            return None, {'error': str(e)}
    
    def batch_tensorize(self, feature_list: list) -> np.ndarray:
        """
        Convert list of MFCC arrays to batch tensor.
        
        Args:
            feature_list: List of MFCC arrays
            
        Returns:
            Batch tensor with shape (batch, n_mfcc, time, 1)
        """
        arr = np.stack(feature_list, axis=0)
        if arr.ndim == 3:
            arr = arr[..., np.newaxis]
        return arr
