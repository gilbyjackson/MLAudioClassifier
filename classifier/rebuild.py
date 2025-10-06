"""
Archive regeneration from index files.
"""

import os
import shutil
from pathlib import Path
from typing import Dict, Any, Optional, List
from collections import defaultdict
from tqdm.auto import tqdm

from classifier.io import JSONLReader


class ArchiveRebuilder:
    """Rebuild organized archive from index JSONL."""
    
    def __init__(
        self,
        index_path: Path,
        output_root: Path,
        copy_mode: str = 'copy',
        override_mapping: Optional[Dict[str, str]] = None,
        allowed_labels: Optional[List[str]] = None,
        force_all: bool = False
    ):
        """
        Initialize rebuilder.
        
        Args:
            index_path: Path to index.jsonl
            output_root: Root directory for regenerated archive
            copy_mode: 'copy', 'symlink', or 'hardlink'
            override_mapping: Optional hash->label overrides
            allowed_labels: Optional subset of labels to emit
            force_all: If True, ignore allowed_labels filter
        """
        self.index_path = index_path
        self.output_root = output_root
        self.copy_mode = copy_mode
        self.override_mapping = override_mapping or {}
        self.allowed_labels = allowed_labels
        self.force_all = force_all
        
        self.stats = defaultdict(int)
        self.manifests = defaultdict(list)
    
    def rebuild(self):
        """
        Rebuild archive from index.
        
        Reads index JSONL and materializes files into organized structure.
        """
        print(f"Rebuilding archive from {self.index_path}")
        print(f"Output: {self.output_root}")
        
        self.output_root.mkdir(parents=True, exist_ok=True)
        
        reader = JSONLReader(self.index_path)
        records = list(reader)
        
        print(f"Processing {len(records)} records...")
        
        for record in tqdm(records, desc='Rebuilding'):
            self._process_record(record)
        
        # Write manifests
        self._write_manifests()
        
        # Write summary
        self._write_summary()
        
        print(f"\n✓ Rebuild complete")
        print(f"  Total processed: {self.stats['total']}")
        print(f"  Files emitted: {self.stats['emitted']}")
        print(f"  Errors skipped: {self.stats['errors']}")
        print(f"  Duplicates skipped: {self.stats['duplicates']}")
    
    def _process_record(self, record: Dict[str, Any]):
        """Process a single record from index."""
        self.stats['total'] += 1
        
        # Skip errors
        if record.get('errors'):
            self.stats['errors'] += 1
            return
        
        # Skip duplicates
        if record.get('skipped_duplicate'):
            self.stats['duplicates'] += 1
            return
        
        # Get assigned label
        label = record.get('assigned_label')
        
        if not label:
            self.stats['no_label'] += 1
            return
        
        # Apply overrides
        file_hash = record.get('hash')
        if file_hash and file_hash in self.override_mapping:
            label = self.override_mapping[file_hash]
            self.stats['overridden'] += 1
        
        # Check allowed labels
        if not self.force_all and self.allowed_labels:
            if label not in self.allowed_labels and label != 'misc':
                label = 'misc'
                self.stats['filtered_to_misc'] += 1
        
        # Get source path
        abs_path = Path(record['abs_path'])
        
        if not abs_path.exists():
            self.stats['missing_source'] += 1
            return
        
        # Determine destination
        dest_dir = self.output_root / label
        dest_dir.mkdir(parents=True, exist_ok=True)
        
        # Preserve relative structure or flatten
        relative_path = record.get('relative_path', abs_path.name)
        dest_path = dest_dir / Path(relative_path).name
        
        # Handle name collisions
        if dest_path.exists():
            stem = dest_path.stem
            suffix = dest_path.suffix
            counter = 1
            while dest_path.exists():
                dest_path = dest_dir / f"{stem}_{counter}{suffix}"
                counter += 1
        
        # Copy/link file
        try:
            if self.copy_mode == 'copy':
                shutil.copy2(abs_path, dest_path)
            elif self.copy_mode == 'symlink':
                os.symlink(abs_path, dest_path)
            elif self.copy_mode == 'hardlink':
                os.link(abs_path, dest_path)
            else:
                raise ValueError(f"Unknown copy_mode: {self.copy_mode}")
            
            self.stats['emitted'] += 1
            self.stats[f'label_{label}'] += 1
            
            # Add to manifest
            self.manifests[label].append(str(relative_path))
            
        except Exception as e:
            print(f"Error copying {abs_path}: {e}")
            self.stats['copy_errors'] += 1
    
    def _write_manifests(self):
        """Write per-class manifest files."""
        manifest_dir = self.output_root / '_manifests'
        manifest_dir.mkdir(exist_ok=True)
        
        for label, paths in self.manifests.items():
            manifest_file = manifest_dir / f"{label}.txt"
            with manifest_file.open('w') as f:
                f.write('\n'.join(sorted(paths)))
        
        print(f"✓ Wrote {len(self.manifests)} manifest files")
    
    def _write_summary(self):
        """Write rebuild summary."""
        import json
        from datetime import datetime
        
        summary = {
            'timestamp': datetime.now().isoformat(),
            'index_path': str(self.index_path),
            'output_root': str(self.output_root),
            'copy_mode': self.copy_mode,
            'stats': dict(self.stats),
            'class_counts': {
                k.replace('label_', ''): v 
                for k, v in self.stats.items() 
                if k.startswith('label_')
            }
        }
        
        summary_file = self.output_root / '_rebuild_summary.json'
        with summary_file.open('w') as f:
            json.dump(summary, f, indent=2)
        
        print(f"✓ Wrote summary: {summary_file}")
