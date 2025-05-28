import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.resolve()))
import os
import time
import json
import argparse
import traceback
from pathlib import Path
from scanner import FileSystemScanner
from mapping import MappingGenerator
from concurrent.futures import ThreadPoolExecutor
import pprint

def test_mapping_performance(input_path, file_limit=None):
    """Test the mapping performance with optimized settings
    
    Args:
        input_path: Path to test
        file_limit: Maximum number of files to process (None for unlimited)
    """
    print(f"[TEST] Testing mapping performance on: {input_path}", file=sys.stderr)
    print(f"[TEST] File limit: {file_limit if file_limit else 'Unlimited'}", file=sys.stderr)
    
    # Initialize scanner
    scanner = FileSystemScanner()
    
    # Start timer
    start_time = time.time()
    
    # Scan directory
    print(f"[TEST] Scanning directory: {input_path}", file=sys.stderr)
    scan_start = time.time()
    
    # Get all files from the directory manually
    print(f"[TEST] Collecting files...", file=sys.stderr)
    file_list = []
    max_files = file_limit if file_limit else float('inf')  # Use limit if provided
    
    try:
        file_count = 0
        print_interval = 20
        
        for root, dirs, files in os.walk(input_path):
            # Sort files to ensure we get a consistent subset for testing
            for file in sorted(files):
                # Check if we've reached our limit
                if file_count >= max_files:
                    print(f"[TEST] Reached max file limit of {max_files}", file=sys.stderr)
                    break
                    
                # Progress reporting
                if file_count % print_interval == 0:
                    print(f"[TEST] Collected {file_count} files so far...", file=sys.stderr)
                    
                full_path = os.path.join(root, file)
                name, ext = os.path.splitext(file)
                ext = ext.lstrip('.')
                
                # Only include sequence files (typically image files)
                if ext.lower() in ['exr', 'jpg', 'jpeg', 'png', 'tif', 'tiff']:
                    try:
                        size = os.path.getsize(full_path)
                    except Exception as e:
                        print(f"[WARNING] Couldn't get size for {full_path}: {e}", file=sys.stderr)
                        size = 0
                        
                    file_info = {
                        "name": file,
                        "path": full_path,
                        "extension": ext,
                        "type": "file",
                        "size": size
                    }
                    file_list.append(file_info)
                    file_count += 1
                    
                    # Break out if we hit our limit
                    if file_count >= max_files:
                        print(f"[TEST] Reached max file limit of {max_files}", file=sys.stderr)
                        break
            
            # Break out of outer loop too if we hit our limit
            if file_count >= max_files:
                break
        
        scan_end = time.time()
        scan_duration = scan_end - scan_start
        print(f"[TEST] Collected {len(file_list)} files in {scan_duration:.2f} seconds", file=sys.stderr)
        
        # Check if this is a network path
        is_network = any(input_path.startswith(prefix) for prefix in [
            "\\\\", "//", "N:", "Z:", "V:"
        ])
        network_status = "network" if is_network else "local"
        print(f"[TEST] Path type: {network_status}", file=sys.stderr)
        
        # Initialize mapping generator
        mapper = MappingGenerator()
        
        # Load test profile
        profile = {
            "name": "Test Profile",
            "vfxRootPath": "/vfx/projects/test",
            "shotCodeFormat": "{show}_{shot}",
            "shotPattern": "\\w+\\d+",
            "defaultTask": "comp",
            "taskMappings": {
                "comp": "compositing",
                "anim": "animation",
                "fx": "effects"
            }
        }
        
        # Run mapping with performance tracking
        print(f"[TEST] Starting sequence detection...", file=sys.stderr)
        map_start = time.time()
        
        # Test the sequence grouping directly with multithreaded processing
        print(f"[TEST] Running multithreaded sequence grouping on {len(file_list)} files...", file=sys.stderr)
        try:
            # Time the multithreaded operation
            mt_start = time.time()
            sequences, single_files = mapper._group_image_sequences(file_list, batch_id="test_batch")
            mt_end = time.time()
            mt_duration = mt_end - mt_start
            
            print(f"[TEST] Multithreaded processing completed in {mt_duration:.2f} seconds", file=sys.stderr)
            map_end = time.time()
            map_duration = map_end - map_start
            
            # Report performance results
            print(f"[TEST] Sequence grouping completed in {map_duration:.2f} seconds", file=sys.stderr)
            print(f"[TEST] Found {len(sequences)} sequences and {len(single_files)} single files", file=sys.stderr)
            print(f"[TEST] Total time: {(time.time() - start_time):.2f} seconds", file=sys.stderr)
            
            # Print detailed information about the sequences found
            if sequences:
                print(f"\n[TEST] DETAILED SEQUENCE INFORMATION:", file=sys.stderr)
                print(f"==================================================", file=sys.stderr)
                
                # Limit detailed output to avoid overwhelming the console
                display_count = min(len(sequences), 3)
                for i, seq in enumerate(sequences[:display_count]):
                    print(f"\nSEQUENCE #{i+1} of {len(sequences)}:", file=sys.stderr)
                    
                    # Handle both dictionary and list/tuple sequence formats
                    if isinstance(seq, dict):
                        # Extract key sequence information
                        base_name = seq.get('base_name', 'unknown')
                        frame_count = seq.get('frame_count', 0)
                        directory = seq.get('directory', 'unknown')
                        frame_range = seq.get('frame_range', 'unknown')
                        ext = seq.get('suffix', '') or seq.get('extension', '')
                        file_count = len(seq.get('files', []))
                        
                        # Print summary information
                        print(f"  Name: {base_name}", file=sys.stderr)
                        print(f"  Type: {seq.get('type', 'sequence')}", file=sys.stderr)
                        print(f"  Extension: {ext}", file=sys.stderr)
                        print(f"  Directory: {directory}", file=sys.stderr)
                        print(f"  Frame range: {frame_range}", file=sys.stderr)
                        print(f"  Frame count: {frame_count}", file=sys.stderr)
                        print(f"  File count: {file_count}", file=sys.stderr)
                        
                        # Print sample files (first 2 and last 2)
                        if 'files' in seq and seq['files']:
                            files = seq['files']
                            print(f"  Sample files ({min(5, len(files))} of {len(files)}):", file=sys.stderr)
                            for j, f in enumerate(files[:2]):
                                print(f"    - {os.path.basename(f) if isinstance(f, str) else f.get('name', 'unknown')}", file=sys.stderr)
                            if len(files) > 4:
                                print(f"    - [...{len(files)-4} more files...]", file=sys.stderr)
                            for j, f in enumerate(files[-2:]):
                                print(f"    - {os.path.basename(f) if isinstance(f, str) else f.get('name', 'unknown')}", file=sys.stderr)
                    else:
                        # For non-dictionary sequences, just print what we have
                        print(f"  Data: {seq}", file=sys.stderr)
                        
            # Print sample single files
            if single_files:
                print(f"\n[TEST] SAMPLE SINGLE FILES:", file=sys.stderr)
                print(f"==================================================", file=sys.stderr)
                sample_count = min(5, len(single_files))
                for i, f in enumerate(single_files[:sample_count]):
                    if isinstance(f, dict):
                        print(f"  {i+1}. {f.get('name', 'unknown')} ({f.get('extension', 'unknown')})", file=sys.stderr)
                    else:
                        print(f"  {i+1}. {os.path.basename(f) if isinstance(f, str) else f}", file=sys.stderr)
                if len(single_files) > sample_count:
                    print(f"  [...and {len(single_files) - sample_count} more files...]", file=sys.stderr)
            
            print(f"[TEST] SUCCESS: Sequence detection completed without hanging", file=sys.stderr)
            return True
            
        except Exception as e:
            print(f"[TEST] ERROR: Sequence grouping failed: {e}", file=sys.stderr)
            traceback.print_exc(file=sys.stderr)
            map_end = time.time()
            map_duration = map_end - map_start
            print(f"[TEST] Failed after {map_duration:.2f} seconds", file=sys.stderr)
            return False
            
    except Exception as e:
        print(f"[TEST] ERROR during file collection: {e}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        return False

def run_performance_tests(path, limits=[200, 500, 1000]):
    """Run performance tests with different file limits to compare"""
    print(f"\n[PERFORMANCE TEST] Running tests on {path} with multiple file limits\n", file=sys.stderr)
    print(f"=============================================================", file=sys.stderr)
    
    results = []
    for limit in limits:
        print(f"\n[TEST] Running test with {limit} files limit\n", file=sys.stderr)
        start_time = time.time()
        success = test_mapping_performance(path, limit)
        total_time = time.time() - start_time
        results.append({
            "limit": limit,
            "success": success,
            "time": total_time
        })
    
    # Print summary of all tests
    print(f"\n[PERFORMANCE TEST] SUMMARY OF ALL TESTS", file=sys.stderr)
    print(f"=============================================================", file=sys.stderr)
    print(f"{'FILE COUNT':<12} {'STATUS':<10} {'TIME (sec)':<12} {'FILES/SEC':<12}", file=sys.stderr)
    print(f"------------------------------------------------------------", file=sys.stderr)
    
    # Calculate files per second for successful tests
    for result in results:
        status = "SUCCESS" if result["success"] else "FAILED"
        files_per_sec = result["limit"] / result["time"] if result["success"] else 0
        print(f"{result['limit']:<12} {status:<10} {result['time']:.2f}s{' ':<8} {files_per_sec:.1f}", file=sys.stderr)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test mapping performance with optimized settings")
    parser.add_argument("path", help="Path to test mapping on")
    parser.add_argument("--limit", type=int, help="Limit the number of files to process")
    parser.add_argument("--performance", action="store_true", help="Run multiple tests with different file limits")
    parser.add_argument("--limits", type=str, default="200,500,1000", help="Comma-separated list of file limits for performance tests")
    args = parser.parse_args()
    
    # If performance testing is requested, run multiple tests
    if args.performance:
        limits = [int(x) for x in args.limits.split(',')]
        run_performance_tests(args.path, limits)
        sys.exit(0)
    else:
        # Run a single test with the specified limit
        success = test_mapping_performance(args.path, args.limit)
        sys.exit(0 if success else 1)
