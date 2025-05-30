#!/usr/bin/env python3
"""
Performance test script for file copy operations.
Tests different copy methods and thread counts to find optimal settings.
"""
import os
import sys
import time
import tempfile
import shutil
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from python.file_operations_utils.file_management import copy_item

def create_test_file(size_mb=100):
    """Create a test file of specified size in MB."""
    test_file = tempfile.NamedTemporaryFile(delete=False, suffix='.test')
    
    # Write test data
    chunk_size = 1024 * 1024  # 1MB chunks
    data = b'A' * chunk_size
    
    with open(test_file.name, 'wb') as f:
        for _ in range(size_mb):
            f.write(data)
    
    return test_file.name

def test_shutil_copy(source, dest):
    """Test shutil.copy2 performance."""
    start_time = time.time()
    shutil.copy2(source, dest)
    end_time = time.time()
    return end_time - start_time

def test_custom_copy(source, dest):
    """Test our custom copy implementation."""
    start_time = time.time()
    success, message = copy_item(source, dest, transfer_id="test")
    end_time = time.time()
    return end_time - start_time if success else None

def format_speed(bytes_per_sec):
    """Format speed in human readable format."""
    if bytes_per_sec > 1024 * 1024 * 1024:
        return f"{bytes_per_sec / (1024**3):.2f} GB/s"
    elif bytes_per_sec > 1024 * 1024:
        return f"{bytes_per_sec / (1024**2):.2f} MB/s"
    else:
        return f"{bytes_per_sec / 1024:.2f} KB/s"

def main():
    print("🌐 SMB/NAS File Copy Performance Test")
    print("=" * 55)
    print("🏢 Optimized for Network Attached Storage operations")
    
    # Test different file sizes relevant to SMB operations
    test_sizes = [1, 10, 50, 200]  # MB - smaller range for network testing
    
    for size_mb in test_sizes:
        print(f"\n📁 Testing {size_mb}MB file over SMB/NAS:")
        print("-" * 40)
        
        # Create test file
        source_file = create_test_file(size_mb)
        file_size = os.path.getsize(source_file)
        
        try:
            # Test shutil.copy2
            dest1 = source_file + ".shutil_copy"
            shutil_time = test_shutil_copy(source_file, dest1)
            shutil_speed = file_size / shutil_time
            print(f"📈 shutil.copy2:  {shutil_time:.2f}s ({format_speed(shutil_speed)})")
            
            # Test custom copy
            dest2 = source_file + ".custom_copy"
            custom_time = test_custom_copy(source_file, dest2)
            if custom_time:
                custom_speed = file_size / custom_time
                print(f"🔧 Custom copy:   {custom_time:.2f}s ({format_speed(custom_speed)})")
                
                # Performance comparison
                speedup = custom_time / shutil_time
                if speedup > 1.1:
                    print(f"⚠️  Custom is {speedup:.1f}x SLOWER than shutil")
                elif speedup < 0.9:
                    print(f"🎉 Custom is {1/speedup:.1f}x FASTER than shutil")
                else:
                    print(f"✅ Performance similar (within 10%)")
            else:
                print("❌ Custom copy failed")
            
        finally:
            # Cleanup
            for f in [source_file, dest1, dest2]:
                try:
                    if os.path.exists(f):
                        os.unlink(f)
                except:
                    pass
    
    print("\n🌐 SMB/NAS Performance Tips:")
    print("• Use 4-16 threads for network operations")
    print("• Larger buffers (4MB+) reduce network round-trips") 
    print("• Fast copy mode (shutil) often best for files >50MB")
    print("• Network latency dominates small file performance")
    print("• Consider SMB3+ features like compression if available")
    print("• Windows Explorer uses kernel-level SMB optimizations")

if __name__ == "__main__":
    main() 