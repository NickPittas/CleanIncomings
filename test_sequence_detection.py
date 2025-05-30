#!/usr/bin/env python3
"""
Test script to validate improved sequence detection patterns
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'python'))

from python.mapping_utils.extract_sequence_info import extract_sequence_info

def test_sequence_detection():
    """Test various sequence filename patterns"""
    
    test_files = [
        # Standard format (should work)
        "sequence_v001.1001.exr",
        "render_beauty.1234.dpx",
        
        # Embedded frame numbers (new patterns)
        "ASSET_01_v019_ALi_0948.exr",
        "ASSET_01_v019_ALi_1222.exr", 
        "ASSET_01_v019_Main_1170.exr",
        "OLNT0010_main_arch_puz_a_LL1804k_ACEScgLin_PREVIZ_v022.1001.exr",
        "OLNT0010_main_arch_puz_a_LL1804k_ACEScgLin_PREVIZ_v022.1002.exr",
        
        # Should NOT be detected as sequences
        "single_file.exr",
        "no_frame_number.dpx",
        "sequence_invalid.exr",
        
        # Edge cases
        "test_v001_1234_beauty.exr",
        "shot_0010_1000.png"
    ]
    
    print("Testing Sequence Detection Patterns:")
    print("=" * 50)
    
    sequences_detected = 0
    total_tests = len(test_files)
    
    for filename in test_files:
        result = extract_sequence_info(filename)
        if result:
            print(f"✅ {filename}")
            print(f"   Base: {result.get('base_name')}")
            print(f"   Frame: {result.get('frame')}")
            print(f"   Suffix: {result.get('suffix')}")
            sequences_detected += 1
        else:
            print(f"❌ {filename} - No sequence detected")
        print()
    
    print(f"Summary: {sequences_detected}/{total_tests} files detected as sequences")
    
    # Test grouping behavior
    print("\nTesting Sequence Grouping:")
    print("=" * 30)
    
    asset_files = [
        {"name": "ASSET_01_v019_ALi_0948.exr", "extension": ".exr", "path": "/test/ASSET_01_v019_ALi_0948.exr"},
        {"name": "ASSET_01_v019_ALi_0949.exr", "extension": ".exr", "path": "/test/ASSET_01_v019_ALi_0949.exr"},
        {"name": "ASSET_01_v019_ALi_0950.exr", "extension": ".exr", "path": "/test/ASSET_01_v019_ALi_0950.exr"},
        {"name": "ASSET_01_v019_Main_1170.exr", "extension": ".exr", "path": "/test/ASSET_01_v019_Main_1170.exr"},
        {"name": "ASSET_01_v019_Main_1171.exr", "extension": ".exr", "path": "/test/ASSET_01_v019_Main_1171.exr"},
        {"name": "single_file.exr", "extension": ".exr", "path": "/test/single_file.exr"}
    ]
    
    from python.mapping_utils.group_image_sequences import group_image_sequences
    
    sequences, single_files = group_image_sequences(
        asset_files, 
        extract_sequence_info=extract_sequence_info
    )
    
    print(f"Found {len(sequences)} sequences:")
    for seq in sequences:
        print(f"  - {seq['base_name']}: {seq['frame_count']} frames")
    
    print(f"Found {len(single_files)} single files:")
    for file in single_files:
        print(f"  - {file['name']}")

if __name__ == "__main__":
    test_sequence_detection() 