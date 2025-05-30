import time
from pathlib import Path
from typing import List, Dict, Any, Tuple
from threading import Lock

# Set of extensions that can be part of an image sequence
SEQUENCE_EXTENSIONS = set([
    "exr", ".exr", "dpx", ".dpx", "tif", ".tif", "tiff", ".tiff", 
    "jpg", ".jpg", "jpeg", ".jpeg", "png", ".png", "hdr", ".hdr",
    "mov", ".mov", "mp4", ".mp4"
])

def group_image_sequences(files: List[Dict[str, Any]], batch_id=None, extract_sequence_info=None, is_network_path=None) -> Tuple[list, list]:
    """
    Group image files into sequences based on naming patterns.
    Args:
        files: List of file nodes to process
        batch_id: Optional batch ID for progress tracking
        extract_sequence_info: Function to extract sequence info from filename
        is_network_path: Function to check if a path is a network path
    Returns:
        Tuple of (sequences, single_files)
    """
    total_files = len(files)
    file_groups = {}
    single_files = []
    
    # Determine if we're on a network path for progress timing
    is_network = False
    if total_files > 0 and "path" in files[0] and is_network_path:
        is_network = is_network_path(files[0]["path"])
    
    print(f"[SEQUENCE_GROUPING] Processing {total_files} files for sequence detection...")
    
    processed_count = 0
    for file_node in files:
        try:
            file_name = file_node.get("name", "")
            file_ext = file_node.get("extension", "").lower()
            
            # Check if file extension can be part of a sequence
            if file_ext not in SEQUENCE_EXTENSIONS:
                single_files.append(file_node)
                processed_count += 1
                continue
                
            file_path = file_node.get("path", "")
            directory = str(Path(file_path).parent)
            
            if extract_sequence_info is None:
                raise ValueError("extract_sequence_info function must be provided")
                
            # Extract sequence information from filename
            sequence_info = extract_sequence_info(file_name)
            
            if sequence_info and "frame" in sequence_info and sequence_info.get("base_name"):
                base_name = sequence_info["base_name"]
                
                # Create sequence key based on directory, base name, and extension
                seq_key = (directory, base_name, file_ext)
                
                if seq_key not in file_groups:
                    file_groups[seq_key] = []
                    
                # Add file to the appropriate sequence group
                file_groups[seq_key].append(file_node)
            else:
                # If no sequence info found, treat as single file
                single_files.append(file_node)
                
        except Exception as e:
            # If any error occurs, treat as single file
            print(f"[SEQUENCE_GROUPING] Error processing file {file_node.get('name', 'unknown')}: {e}")
            single_files.append(file_node)
            
        processed_count += 1
        
        # Progress reporting for large datasets
        if processed_count % 10000 == 0:
            print(f"[SEQUENCE_GROUPING] Processed {processed_count}/{total_files} files...")
    
    # Convert grouped files into sequence objects
    sequences = []
    sequence_count = 0
    for seq_key, group in file_groups.items():
        # Only consider it a sequence if there are multiple files
        if len(group) > 1:
            directory, base_name, file_ext = seq_key
            
            # Create sequence object
            sequence_obj = {
                "base_name": base_name,
                "suffix": file_ext,
                "files": group,
                "directory": directory,
                "frame_count": len(group),
                "frame_numbers": [extract_sequence_info(f.get("name", "")).get("frame", 0) for f in group if extract_sequence_info(f.get("name", ""))],
                "frame_range": f"1-{len(group)}"  # Simplified frame range
            }
            sequences.append(sequence_obj)
            sequence_count += 1
        else:
            # Single file in group, add to single files
            single_files.extend(group)
    
    print(f"[SEQUENCE_GROUPING] Results: {sequence_count} sequences, {len(single_files)} single files")
    print(f"[SEQUENCE_GROUPING] Sequence optimization: {len(sequences)} sequences vs {sum(seq['frame_count'] for seq in sequences)} individual files")
    
    return sequences, single_files
