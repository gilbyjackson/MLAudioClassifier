"""
I/O utilities for classifier package.

Handles file discovery, hashing, and JSONL streaming.
"""

import json
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional, Iterator
import gzip


def discover_audio_files(
    archive_path: Path,
    formats: List[str],
    max_files: Optional[int] = None,
    exclude_patterns: Optional[List[str]] = None
) -> List[Path]:
    """
    Recursively discover audio files in archive.
    
    Args:
        archive_path: Root directory to search
        formats: List of file extensions (e.g., ['.wav', '.flac'])
        max_files: Optional limit on number of files
        exclude_patterns: Optional glob patterns to exclude
        
    Returns:
        Sorted list of audio file paths
    """
    files: List[Path] = []
    exclude_patterns = exclude_patterns or []
    
    for ext in formats:
        candidates = archive_path.rglob(f'*{ext}')
        for candidate in candidates:
            # Check exclusions
            excluded = False
            for pattern in exclude_patterns:
                if candidate.match(pattern):
                    excluded = True
                    break
            if not excluded:
                files.append(candidate)
    
    files.sort()
    
    if max_files is not None and len(files) > max_files:
        files = files[:max_files]
    
    return files


def filter_valid_files(paths: List[Path]) -> List[Path]:
    """Filter out empty or inaccessible files."""
    valid = []
    for p in paths:
        try:
            if p.stat().st_size > 0:
                valid.append(p)
        except OSError:
            continue
    return valid


def hash_file(path: Path, algorithm: str = 'md5', block_size: int = 65536) -> str:
    """
    Compute hash of file content.
    
    Args:
        path: File to hash
        algorithm: Hash algorithm ('md5', 'sha256', etc.)
        block_size: Read buffer size
        
    Returns:
        Hex digest string
    """
    if algorithm == 'md5':
        hasher = hashlib.md5()
    elif algorithm == 'sha256':
        hasher = hashlib.sha256()
    else:
        raise ValueError(f"Unsupported hash algorithm: {algorithm}")
    
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(block_size), b''):
            hasher.update(chunk)
    
    return hasher.hexdigest()


class JSONLWriter:
    """Streaming JSONL writer with optional gzip compression."""
    
    def __init__(self, path: Path, compressed: bool = False):
        """
        Initialize writer.
        
        Args:
            path: Output file path
            compressed: If True, write gzip-compressed JSONL
        """
        self.path = path
        self.compressed = compressed
        self._file = None
        
        if compressed and not str(path).endswith('.gz'):
            self.path = Path(str(path) + '.gz')
    
    def __enter__(self):
        if self.compressed:
            self._file = gzip.open(self.path, 'wt', encoding='utf-8')
        else:
            self._file = self.path.open('w', encoding='utf-8')
        return self
    
    def __exit__(self, *args):
        if self._file:
            self._file.close()
    
    def write(self, record: Dict[str, Any]):
        """Write a single JSON record."""
        self._file.write(json.dumps(record) + '\n')
    
    def write_batch(self, records: List[Dict[str, Any]]):
        """Write multiple records."""
        for record in records:
            self.write(record)


class JSONLReader:
    """Streaming JSONL reader with optional gzip decompression."""
    
    def __init__(self, path: Path):
        """
        Initialize reader.
        
        Args:
            path: Input file path (auto-detects .gz)
        """
        self.path = path
        self.compressed = str(path).endswith('.gz')
    
    def __iter__(self) -> Iterator[Dict[str, Any]]:
        """Iterate over records in file."""
        if self.compressed:
            f = gzip.open(self.path, 'rt', encoding='utf-8')
        else:
            f = self.path.open('r', encoding='utf-8')
        
        try:
            for line in f:
                line = line.strip()
                if line:
                    yield json.loads(line)
        finally:
            f.close()
    
    def read_all(self) -> List[Dict[str, Any]]:
        """Read all records into memory."""
        return list(self)


def load_hash_cache(cache_path: Path) -> set:
    """Load hash cache from text file."""
    if not cache_path.exists():
        return set()
    return set(h.strip() for h in cache_path.read_text().splitlines() if h.strip())


def save_hash_cache(cache_path: Path, hashes: set):
    """Save hash cache to text file."""
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    with cache_path.open('w') as f:
        f.write('\n'.join(sorted(hashes)))
