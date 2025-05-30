#!/usr/bin/env python3
import os

try:
    with open('performance_results.txt', 'r') as f:
        lines = f.readlines()
    
    print("=== PERFORMANCE TEST RESULTS ===")
    
    # Find and print key sections
    in_performance_section = False
    in_cache_section = False
    
    for line in lines:
        line = line.strip()
        
        # Start of performance comparison
        if 'Performance Comparison:' in line:
            in_performance_section = True
            print(line)
            continue
            
        # Start of cache effectiveness test
        if 'Cache Effectiveness Test' in line:
            in_cache_section = True
            in_performance_section = False
            print("\n" + line)
            continue
            
        # End markers
        if 'Pattern optimization test completed' in line:
            print(line)
            break
            
        # Print relevant lines
        if in_performance_section:
            if line.startswith('-') or 'Files' in line or any(c.isdigit() for c in line):
                print(line)
                
        if in_cache_section:
            if 'Processed' in line or 'Time:' in line or 'Cache' in line:
                print(line)

except Exception as e:
    print(f"Error: {e}") 