#!/usr/bin/env python3
import os
import sys
import json

# Add python directory to path
python_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'python')
sys.path.insert(0, python_dir)

print("Simple Pattern Optimization Test")
print("=" * 40)

try:
    print("1. Testing imports...")
    from mapping_utils.pattern_cache import extract_all_patterns_cached, get_global_cache
    print("   OK pattern_cache imported")
    
    from mapping_utils.shot_extractor import extract_shot_simple
    print("   OK shot_extractor imported")
    
    print("\n2. Loading patterns...")
    patterns_path = "config/patterns.json"
    with open(patterns_path, 'r') as f:
        config = json.load(f)
    
    patterns = {
        'shot': config.get('shotPatterns', []),
        'task': config.get('taskPatterns', {}),
        'version': config.get('versionPatterns', []),
        'resolution': config.get('resolutionPatterns', []),
        'asset': config.get('assetPatterns', []),
        'stage': config.get('stagePatterns', [])
    }
    
    print(f"   OK Loaded {len(patterns['shot'])} shot patterns")
    print(f"   OK Loaded {len(patterns['task'])} task categories")
    print(f"   OK Loaded {len(patterns['version'])} version patterns")
    
    print("\n3. Testing extraction...")
    test_filename = "OLNT0010_beauty_v001.1001.exr"
    print(f"   Test file: {test_filename}")
    
    # Test cached extraction
    result = extract_all_patterns_cached(
        test_filename,
        patterns['shot'],
        patterns['task'],
        patterns['version'],
        patterns['resolution'],
        patterns['asset'],
        patterns['stage']
    )
    
    print(f"   OK Cached extraction result: {result}")
    
    # Test cache stats
    cache = get_global_cache()
    stats = cache.get_stats()
    print(f"   OK Cache stats: {stats}")
    
    print("\nSUCCESS: All tests passed!")
    
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc() 