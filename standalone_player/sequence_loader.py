"""
Sequence Loader: Detects, sorts, and manages image sequences for the Nuke-style player.
Handles memory estimation, preloading, and LRU caching for large sequences.
"""
import os
import re
from collections import OrderedDict
from pathlib import Path

class SequenceLoader:
    """
    Loads and manages image sequences (EXR, DPX, PNG, JPG, etc.) with support for
    memory-limited preloading and LRU caching.
    """
    SEQUENCE_PATTERN = re.compile(r"(.*?)([0-9]{4,10})(\.[^.]+)$")
    SUPPORTED_EXTS = {'.exr', '.dpx', '.png', '.jpg', '.jpeg', '.tif', '.tiff', '.bmp'}

    def __init__(self, path, mem_limit_gb=128):
        self.path = Path(path)
        self.mem_limit = mem_limit_gb * (1024 ** 3)
        self.sequence_files = []
        self.frame_numbers = []
        self._detect_sequence()
        self.cache = OrderedDict()
        self.cache_size = 0

    def _detect_sequence(self):
        """Detect all frames in the sequence and sort them numerically."""
        directory = self.path.parent if self.path.is_file() else self.path
        basename, frame, ext = self._parse_filename(self.path.name)
        if not ext or ext.lower() not in self.SUPPORTED_EXTS:
            raise ValueError(f"Unsupported file format: {ext}")
        pattern = re.compile(rf"{re.escape(basename)}([0-9]{{4,10}}){re.escape(ext)}$")
        files = []
        for f in os.listdir(directory):
            m = pattern.match(f)
            if m:
                files.append((int(m.group(1)), str(directory / f)))
        files.sort()
        self.frame_numbers = [f[0] for f in files]
        self.sequence_files = [f[1] for f in files]

    @staticmethod
    def _parse_filename(filename):
        m = SequenceLoader.SEQUENCE_PATTERN.match(filename)
        if not m:
            raise ValueError(f"Filename does not match sequence pattern: {filename}")
        return m.group(1), m.group(2), m.group(3)

    def estimate_total_memory(self, imageio_loader):
        """Estimate total memory usage for the sequence using the loader's shape/dtype."""
        if not self.sequence_files:
            return 0
        sample = imageio_loader(self.sequence_files[0])
        size = sample.nbytes
        return size * len(self.sequence_files)

    def get_frame(self, idx, imageio_loader):
        """Return frame at idx, loading from disk or cache. Uses LRU cache."""
        path = self.sequence_files[idx]
        if path in self.cache:
            self.cache.move_to_end(path)
            return self.cache[path]
        arr = imageio_loader(path)
        arr_bytes = arr.nbytes
        while self.cache_size + arr_bytes > self.mem_limit and self.cache:
            _, old = self.cache.popitem(last=False)
            self.cache_size -= old.nbytes
        self.cache[path] = arr
        self.cache_size += arr_bytes
        return arr

    def num_frames(self):
        return len(self.sequence_files)

    def frame_paths(self):
        return list(self.sequence_files)
