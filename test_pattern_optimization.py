#!/usr/bin/env python3
"""
Pattern Optimization Performance Test

Tests the new cached pattern extraction system vs the old individual
extraction approach to verify performance improvements.
"""

import time
import sys
import os

# Add python directory to path for imports
python_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'python')
if python_dir not in sys.path:
    sys.path.insert(0, python_dir)

try:
    from mapping_utils.pattern_cache import extract_all_patterns_cached, get_global_cache
    from mapping_utils.shot_extractor import extract_shot_simple
    from mapping_utils.task_extractor import extract_task_simple
    from mapping_utils.version_extractor import extract_version_simple
    from mapping_utils.resolution_extractor import extract_resolution_simple
    from mapping_utils.asset_extractor import extract_asset_simple
    from mapping_utils.stage_extractor import extract_stage_simple
except ImportError as e:
    print(f"❌ Import error: {e}")
    print(f"Python path: {sys.path}")
    print(f"Current directory: {os.getcwd()}")
    sys.exit(1)


def generate_test_filenames(count=1000):
    """Generate test filenames for performance testing."""
    test_files = []
    
    shots = ["OLNT0010", "KITC0010", "WTFB0010", "IGB0010"]
    tasks = ["beauty", "render", "comp", "plate"]
    assets = ["FishFlock", "VrayRAW", "arnold", "cycles"]
    versions = ["v001", "v002", "v003", "v010", "v055"]
    resolutions = ["4k", "2k", "1080p", "12k"]
    
    for i in range(count):
        shot = shots[i % len(shots)]
        task = tasks[i % len(tasks)]
        asset = assets[i % len(assets)]
        version = versions[i % len(versions)]
        resolution = resolutions[i % len(resolutions)]
        frame = str(1001 + (i % 100)).zfill(4)
        
        # Create various filename patterns
        patterns = [
            f"{shot}_{task}_{asset}_{version}_{resolution}.{frame}.exr",
            f"{shot}_{task}_{version}.{frame}.jpg",
            f"{asset}_{task}_{shot}_{version}.{frame}.png",
            f"{shot}_{version}_{resolution}.{frame}.tiff",
            f"{task}_{asset}_{shot}_{version}.{frame}.dpx"
        ]
        
        test_files.append(patterns[i % len(patterns)])
    
    return test_files


def test_individual_extraction(filenames, patterns):
    """Test the old individual extraction approach."""
    shot_patterns = patterns['shot']
    task_patterns = patterns['task']
    version_patterns = patterns['version']
    resolution_patterns = patterns['resolution']
    asset_patterns = patterns['asset']
    stage_patterns = patterns['stage']
    
    results = []
    start_time = time.time()
    
    for filename in filenames:
        shot = extract_shot_simple(filename, "", shot_patterns)
        task = extract_task_simple(filename, "", task_patterns)
        version = extract_version_simple(filename, version_patterns)
        resolution = extract_resolution_simple(filename, "", resolution_patterns)
        asset = extract_asset_simple(filename, asset_patterns)
        stage = extract_stage_simple(filename, stage_patterns)
        
        results.append({
            'shot': shot,
            'task': task,
            'version': version,
            'resolution': resolution,
            'asset': asset,
            'stage': stage
        })
    
    end_time = time.time()
    return results, end_time - start_time


def test_cached_extraction(filenames, patterns):
    """Test the new cached extraction approach."""
    results = []
    start_time = time.time()
    
    for filename in filenames:
        result = extract_all_patterns_cached(
            filename,
            patterns['shot'],
            patterns['task'],
            patterns['version'],
            patterns['resolution'],
            patterns['asset'],
            patterns['stage']
        )
        results.append(result)
    
    end_time = time.time()
    return results, end_time - start_time


def load_test_patterns():
    """Load test patterns from patterns.json."""
    import json
    
    patterns_path = "config/patterns.json"
    if not os.path.exists(patterns_path):
        print(f"Error: {patterns_path} not found")
        return None
    
    with open(patterns_path, 'r') as f:
        config = json.load(f)
    
    return {
        'shot': config.get('shotPatterns', []),
        'task': config.get('taskPatterns', {}),
        'version': config.get('versionPatterns', []),
        'resolution': config.get('resolutionPatterns', []),
        'asset': config.get('assetPatterns', []),
        'stage': config.get('stagePatterns', [])
    }


def main():
    """Run performance comparison tests."""
    print("Pattern Optimization Performance Test")
    print("=" * 50)
    
    # Load patterns
    patterns = load_test_patterns()
    if not patterns:
        return
    
    print(f"Loaded patterns:")
    for key, value in patterns.items():
        if isinstance(value, dict):
            print(f"  {key}: {len(value)} categories")
        else:
            print(f"  {key}: {len(value)} patterns")
    
    # Test different file counts
    test_counts = [100, 500, 1000, 2000]
    
    print("\nPerformance Comparison:")
    print("-" * 70)
    print(f"{'Files':<8} {'Individual (s)':<15} {'Cached (s)':<12} {'Speedup':<10} {'Cache Stats'}")
    print("-" * 70)
    
    for count in test_counts:
        # Clear cache before each test
        cache = get_global_cache()
        cache.clear()
        
        # Generate test files
        test_files = generate_test_filenames(count)
        
        # Test individual extraction
        results_individual, time_individual = test_individual_extraction(test_files, patterns)
        
        # Clear cache again for fair comparison
        cache.clear()
        
        # Test cached extraction
        results_cached, time_cached = test_cached_extraction(test_files, patterns)
        
        # Calculate speedup
        speedup = time_individual / time_cached if time_cached > 0 else 0
        
        # Get cache stats
        stats = cache.get_stats()
        
        print(f"{count:<8} {time_individual:<15.3f} {time_cached:<12.3f} {speedup:<10.1f}x {stats['hit_rate']:.1f}% hit rate")
        
        # Verify results are consistent (first 10 files)
        mismatches = 0
        for i in range(min(10, len(results_individual))):
            ind_result = results_individual[i]
            cached_result = results_cached[i]
            
            for key in ind_result:
                if ind_result[key] != cached_result[key]:
                    mismatches += 1
                    break
        
        if mismatches > 0:
            print(f"Warning: {mismatches} mismatches detected in first 10 results")
    
    print("-" * 70)
    
    # Test cache effectiveness with repeated patterns
    print("\nCache Effectiveness Test (repeated patterns):")
    print("-" * 50)
    
    cache.clear()
    
    # Create test with many repeated filenames
    repeated_files = []
    base_files = generate_test_filenames(50)  # 50 unique files
    for _ in range(20):  # Repeat 20 times = 1000 total
        repeated_files.extend(base_files)
    
    start_time = time.time()
    for filename in repeated_files:
        extract_all_patterns_cached(
            filename,
            patterns['shot'],
            patterns['task'],
            patterns['version'],
            patterns['resolution'],
            patterns['asset'],
            patterns['stage']
        )
    end_time = time.time()
    
    final_stats = cache.get_stats()
    print(f"Processed {len(repeated_files)} files (50 unique, 20x repeated)")
    print(f"Time: {end_time - start_time:.3f} seconds")
    print(f"Cache hit rate: {final_stats['hit_rate']:.1f}%")
    print(f"Cache hits: {final_stats['hit_count']}")
    print(f"Cache misses: {final_stats['miss_count']}")
    print(f"Cache size: {final_stats['cache_size']} entries")
    
    print("\nPattern optimization test completed!")


if __name__ == "__main__":
    main() 