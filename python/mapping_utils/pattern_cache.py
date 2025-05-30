"""
Pattern Result Cache

Caches pattern extraction results to avoid repeated regex operations
on the same filenames during mapping generation.
"""

from typing import Dict, Any, Optional, Tuple
from functools import lru_cache
import hashlib


class PatternCache:
    """Cache for pattern extraction results to improve performance."""
    
    def __init__(self, max_size: int = 10000):
        """Initialize pattern cache with maximum size."""
        self.max_size = max_size
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.hit_count = 0
        self.miss_count = 0
    
    def _get_cache_key(self, filename: str, pattern_type: str, patterns_hash: str) -> str:
        """Generate cache key for filename and pattern type."""
        # Use filename + pattern_type + patterns_hash to ensure cache invalidation
        # when patterns change
        content = f"{filename}|{pattern_type}|{patterns_hash}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def _get_patterns_hash(self, patterns) -> str:
        """Generate hash for pattern list/dict to detect changes."""
        if isinstance(patterns, dict):
            # For task patterns which are dict
            pattern_str = str(sorted(patterns.items()))
        elif isinstance(patterns, list):
            # For shot, version, resolution patterns which are lists
            pattern_str = str(sorted(patterns))
        else:
            pattern_str = str(patterns)
        return hashlib.md5(pattern_str.encode()).hexdigest()[:8]
    
    def get(self, filename: str, pattern_type: str, patterns) -> Optional[Any]:
        """Get cached extraction result if available."""
        patterns_hash = self._get_patterns_hash(patterns)
        cache_key = self._get_cache_key(filename, pattern_type, patterns_hash)
        
        if cache_key in self.cache:
            self.hit_count += 1
            return self.cache[cache_key]['result']
        
        self.miss_count += 1
        return None
    
    def set(self, filename: str, pattern_type: str, patterns, result: Any) -> None:
        """Cache extraction result."""
        patterns_hash = self._get_patterns_hash(patterns)
        cache_key = self._get_cache_key(filename, pattern_type, patterns_hash)
        
        # Implement simple LRU by removing oldest entries when cache is full
        if len(self.cache) >= self.max_size:
            # Remove oldest 10% of entries
            oldest_keys = list(self.cache.keys())[:max(1, self.max_size // 10)]
            for old_key in oldest_keys:
                del self.cache[old_key]
        
        self.cache[cache_key] = {
            'result': result,
            'filename': filename,
            'pattern_type': pattern_type
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics."""
        total_requests = self.hit_count + self.miss_count
        hit_rate = (self.hit_count / total_requests * 100) if total_requests > 0 else 0
        
        return {
            'cache_size': len(self.cache),
            'max_size': self.max_size,
            'hit_count': self.hit_count,
            'miss_count': self.miss_count,
            'hit_rate': round(hit_rate, 2),
            'total_requests': total_requests
        }
    
    def clear(self) -> None:
        """Clear all cached results."""
        self.cache.clear()
        self.hit_count = 0
        self.miss_count = 0


# Global pattern cache instance
_global_cache = PatternCache()


def get_global_cache() -> PatternCache:
    """Get the global pattern cache instance."""
    return _global_cache


@lru_cache(maxsize=1000)
def cached_extract_shot(filename: str, patterns_tuple: Tuple) -> Optional[str]:
    """Cached shot extraction using LRU cache."""
    from .shot_extractor import extract_shot_simple
    patterns_list = list(patterns_tuple)
    return extract_shot_simple(filename, "", patterns_list)


@lru_cache(maxsize=1000)
def cached_extract_version(filename: str, patterns_tuple: Tuple) -> Optional[str]:
    """Cached version extraction using LRU cache."""
    from .version_extractor import extract_version_simple
    patterns_list = list(patterns_tuple)
    return extract_version_simple(filename, patterns_list)


@lru_cache(maxsize=1000)
def cached_extract_resolution(filename: str, patterns_tuple: Tuple) -> Optional[str]:
    """Cached resolution extraction using LRU cache."""
    from .resolution_extractor import extract_resolution_simple
    patterns_list = list(patterns_tuple)
    return extract_resolution_simple(filename, "", patterns_list)


@lru_cache(maxsize=1000)
def cached_extract_asset(filename: str, patterns_tuple: Tuple) -> Optional[str]:
    """Cached asset extraction using LRU cache."""
    from .asset_extractor import extract_asset_simple
    patterns_list = list(patterns_tuple)
    return extract_asset_simple(filename, patterns_list)


@lru_cache(maxsize=1000)
def cached_extract_stage(filename: str, patterns_tuple: Tuple) -> Optional[str]:
    """Cached stage extraction using LRU cache."""
    from .stage_extractor import extract_stage_simple
    patterns_list = list(patterns_tuple)
    return extract_stage_simple(filename, patterns_list)


def cached_extract_task(filename: str, task_patterns: Dict[str, list]) -> Optional[str]:
    """Cached task extraction - can't use LRU cache due to dict mutability."""
    cache = get_global_cache()
    
    # Check cache first
    result = cache.get(filename, 'task', task_patterns)
    if result is not None:
        return result
    
    # Extract and cache result
    from .task_extractor import extract_task_simple
    result = extract_task_simple(filename, "", task_patterns)
    cache.set(filename, 'task', task_patterns, result)
    
    return result


def extract_all_patterns_cached(filename: str, 
                               shot_patterns: list,
                               task_patterns: dict,
                               version_patterns: list,
                               resolution_patterns: list,
                               asset_patterns: list,
                               stage_patterns: list) -> Dict[str, Any]:
    """Extract all patterns from filename using caching for optimal performance."""
    
    # Convert lists to tuples for LRU cache compatibility
    shot_tuple = tuple(shot_patterns) if shot_patterns else ()
    version_tuple = tuple(version_patterns) if version_patterns else ()
    resolution_tuple = tuple(resolution_patterns) if resolution_patterns else ()
    asset_tuple = tuple(asset_patterns) if asset_patterns else ()
    stage_tuple = tuple(stage_patterns) if stage_patterns else ()
    
    return {
        'shot': cached_extract_shot(filename, shot_tuple),
        'task': cached_extract_task(filename, task_patterns),
        'version': cached_extract_version(filename, version_tuple),
        'resolution': cached_extract_resolution(filename, resolution_tuple),
        'asset': cached_extract_asset(filename, asset_tuple),
        'stage': cached_extract_stage(filename, stage_tuple)
    } 