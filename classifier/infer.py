"""
Batch inference and result processing.
"""

import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass
import numpy as np
from tqdm.auto import tqdm

from classifier.io import JSONLWriter, hash_file, load_hash_cache, save_hash_cache
from classifier.features import AudioFeatureExtractor


@dataclass
class InferenceConfig:
    """Configuration for inference run."""
    batch_size: int = 32
    confidence_threshold: float = 0.0
    misc_confidence_threshold: float = 0.50
    target_labels: Optional[List[str]] = None
    dedup_hash: bool = True
    hash_algorithm: str = 'md5'
    include_audio_stats: bool = True
    top_k: int = 3


class InferenceEngine:
    """Batch inference engine with JSONL streaming output."""
    
    def __init__(
        self,
        model,
        labels: List[str],
        feature_extractor: AudioFeatureExtractor,
        config: InferenceConfig,
        canonical_mapping: Optional[Dict[str, str]] = None
    ):
        """
        Initialize inference engine.
        
        Args:
            model: Loaded Keras model
            labels: List of label names
            feature_extractor: AudioFeatureExtractor instance
            config: InferenceConfig instance
            canonical_mapping: Optional model->canonical class mapping
        """
        self.model = model
        self.labels = labels
        self.feature_extractor = feature_extractor
        self.config = config
        self.canonical_mapping = canonical_mapping or {}
        
        self.seen_hashes: Set[str] = set()
        self.results: List[Dict[str, Any]] = []
        self.errors: List[Dict[str, Any]] = []
        self.error_causes: Dict[str, int] = {}
    
    def load_hash_cache(self, cache_path: Path):
        """Load existing hash cache."""
        if self.config.dedup_hash:
            self.seen_hashes = load_hash_cache(cache_path)
            print(f"Loaded {len(self.seen_hashes)} hashes from cache")
    
    def save_hash_cache(self, cache_path: Path):
        """Save hash cache."""
        if self.config.dedup_hash:
            save_hash_cache(cache_path, self.seen_hashes)
            print(f"✓ Updated hash cache: {cache_path}")
    
    def process_batch(
        self,
        batch_paths: List[Path],
        archive_root: Path,
        writer: JSONLWriter
    ):
        """
        Process a batch of files.
        
        Args:
            batch_paths: List of file paths to process
            archive_root: Root of archive (for relative paths)
            writer: JSONL writer for streaming output
        """
        # Extract features
        feats = []
        metas = []
        valid_paths = []
        
        for path in batch_paths:
            feat, meta = self.feature_extractor.extract_mfcc(
                path,
                include_stats=self.config.include_audio_stats
            )
            
            if feat is None:
                error_rec = {
                    'file': str(path),
                    'relative_path': str(path.relative_to(archive_root)),
                    'error': meta['error']
                }
                self.errors.append(error_rec)
                self.error_causes[meta['error']] = self.error_causes.get(meta['error'], 0) + 1
                writer.write(error_rec)
                continue
            
            feats.append(feat)
            metas.append(meta)
            valid_paths.append(path)
        
        if not feats:
            return
        
        # Batch predict
        X = self.feature_extractor.batch_tensorize(feats)
        probs = self.model.predict(X, verbose=0)
        
        # Process predictions
        for i, path in enumerate(valid_paths):
            record = self._process_prediction(
                path=path,
                archive_root=archive_root,
                probs=probs[i],
                meta=metas[i]
            )
            
            self.results.append(record)
            writer.write(record)
    
    def _process_prediction(
        self,
        path: Path,
        archive_root: Path,
        probs: np.ndarray,
        meta: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process a single prediction."""
        # Basic file info
        stat = path.stat()
        relative_path = path.relative_to(archive_root)
        
        record = {
            'relative_path': str(relative_path),
            'abs_path': str(path),
            'size': stat.st_size,
            'mtime': stat.st_mtime,
        }
        
        # Add audio stats if available
        if 'duration_sec' in meta:
            record['duration_sec'] = meta['duration_sec']
            record['rms_db'] = meta['rms_db']
            record['spectral_centroid'] = meta.get('spectral_centroid')
            record['spectral_rolloff'] = meta.get('spectral_rolloff')
        
        # Hash (for deduplication)
        if self.config.dedup_hash:
            file_hash = hash_file(path, algorithm=self.config.hash_algorithm)
            record['hash'] = file_hash
            
            if file_hash in self.seen_hashes:
                record['skipped_duplicate'] = True
                record['assigned_label'] = None
                record['assigned_reason'] = 'duplicate'
                return record
            
            self.seen_hashes.add(file_hash)
        
        # Top predictions
        top_indices = np.argsort(probs)[::-1][:self.config.top_k]
        top_k = [[self.labels[idx], float(probs[idx])] for idx in top_indices]
        
        label_idx = int(np.argmax(probs))
        conf = float(np.max(probs))
        pred_label = self.labels[label_idx]
        
        record['label_top1'] = pred_label
        record['conf_top1'] = conf
        record['topk'] = top_k
        record['probs'] = probs.tolist()
        
        # Apply canonical mapping if available
        canonical_label = self.canonical_mapping.get(pred_label, pred_label)
        
        # Assignment logic
        assigned_label = canonical_label
        assigned_reason = 'top1'
        misc_routed = False
        
        # Check target labels filter
        if self.config.target_labels is not None:
            if canonical_label not in self.config.target_labels:
                assigned_label = 'misc'
                assigned_reason = 'out_of_target'
                misc_routed = True
        
        # Check confidence threshold
        if not misc_routed and conf < self.config.misc_confidence_threshold:
            assigned_label = 'misc'
            assigned_reason = 'low_confidence'
            misc_routed = True
        
        record['assigned_label'] = assigned_label
        record['assigned_reason'] = assigned_reason
        record['misc_routed'] = misc_routed
        record['below_misc_threshold'] = conf < self.config.misc_confidence_threshold
        record['out_of_target'] = canonical_label not in (self.config.target_labels or [canonical_label])
        record['errors'] = None
        
        return record
    
    def run(
        self,
        audio_files: List[Path],
        archive_root: Path,
        output_path: Path,
        compressed: bool = False
    ) -> Dict[str, Any]:
        """
        Run inference on all files and write results.
        
        Args:
            audio_files: List of audio files to process
            archive_root: Root of archive
            output_path: Output JSONL path
            compressed: Whether to compress output
            
        Returns:
            Summary dictionary
        """
        batch_size = self.config.batch_size
        batches = [audio_files[i:i+batch_size] for i in range(0, len(audio_files), batch_size)]
        
        print(f"Processing {len(audio_files)} files in {len(batches)} batches")
        
        start_time = time.time()
        
        with JSONLWriter(output_path, compressed=compressed) as writer:
            for batch in tqdm(batches, desc='Classifying'):
                self.process_batch(batch, archive_root, writer)
        
        elapsed = time.time() - start_time
        
        print(f"⏱️  Classification complete in {elapsed:.2f}s ({len(audio_files)/elapsed:.1f} files/sec)")
        
        # Summary
        emitted = [r for r in self.results if r.get('assigned_label') and r['assigned_label'] != 'misc']
        misc_count = len([r for r in self.results if r.get('assigned_label') == 'misc'])
        
        class_counts = {}
        for r in self.results:
            label = r.get('assigned_label')
            if label:
                class_counts[label] = class_counts.get(label, 0) + 1
        
        if self.error_causes:
            print("Top error causes:")
            for k, v in sorted(self.error_causes.items(), key=lambda x: -x[1])[:10]:
                print(f"  {k:<25} {v}")
        
        summary = {
            'total_examined': len(audio_files),
            'successful': len(self.results),
            'errors': len(self.errors),
            'emitted': len(emitted),
            'misc_routed': misc_count,
            'class_distribution': class_counts,
            'error_breakdown': self.error_causes,
            'elapsed_sec': elapsed,
            'files_per_sec': len(audio_files) / elapsed
        }
        
        return summary
