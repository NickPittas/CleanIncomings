import os
import sys
import traceback
import uuid # Added for generating IDs for error proposals
import time  # Add time for rate limiting
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed

def generate_mappings(
    tree: Dict[str, Any],
    profile: Dict[str, Any],
    batch_id=None,
    group_image_sequences=None,
    extract_sequence_info=None,
    is_network_path=None,
    create_sequence_mapping=None,
    create_simple_mapping=None,
    finalize_sequences=None,
    status_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
) -> List[Dict[str, Any]]:
    """
    Modularized mapping generation logic with rate limiting for progress updates.
    All dependencies must be passed as arguments.
    """
    # Rate limiting for progress updates
    last_progress_update = 0
    min_progress_interval = 0.5  # Minimum 500ms between progress updates
    
    def safe_progress_update(update_data: Dict[str, Any]):
        """Rate-limited progress update to prevent UI overflow."""
        nonlocal last_progress_update
        current_time = time.time()
        
        # Always allow status transitions (starting, completed, error)
        status = update_data.get("data", {}).get("status", "")
        if status in ["starting", "completed", "error", "warning"]:
            if status_callback:
                status_callback(update_data)
            last_progress_update = current_time
            return
        
        # Rate limit progress updates
        if current_time - last_progress_update >= min_progress_interval:
            if status_callback:
                status_callback(update_data)
            last_progress_update = current_time

    safe_progress_update({"type": "mapping_generation", "data": {"status": "starting", "message": "Initiating mapping generation..."}})

    print(f"=== MAPPING GENERATION STARTED ===", file=sys.stderr)
    print(f"Profile: {profile.get('name', 'Unknown')}", file=sys.stderr)
    # VFX Root and Tree prints can be verbose, consider removing or making conditional if status_callback is primary

    all_files = []
    safe_progress_update({"type": "mapping_generation", "data": {"status": "progress", "message": "Collecting files for mapping..."}})

    if "_all_files" in tree and tree["_all_files"]:
        print(f"Using _all_files list from folders-only tree", file=sys.stderr)
        total_files_to_scan = len(tree['_all_files'])
        safe_progress_update({"type": "mapping_generation", "data": {
            "status": "progress", 
            "message": f"Fast-processing {total_files_to_scan} file paths for sequences..."
        }})

        # OPTIMIZED: Process files in batches without individual stat() calls during collection
        batch_size = min(5000, max(1000, total_files_to_scan // 20))  # Dynamic batch size
        progress_update_frequency = max(1, len(range(0, total_files_to_scan, batch_size)) // 5)  # Reduce to 5 updates max
        
        for batch_idx, i in enumerate(range(0, len(tree["_all_files"]), batch_size)):
            batch = tree["_all_files"][i:i + batch_size]
            
            # Quick batch processing without expensive file operations
            for file_path in batch:
                try:
                    path_obj = Path(file_path)
                    # Use minimal file node - let sequence grouping handle the heavy lifting
                    file_node = {
                        "name": path_obj.name,
                        "path": str(path_obj),
                        "type": "file",
                        "size": 0,  # Will be calculated later only for files we actually need
                        "extension": path_obj.suffix.lower(),
                    }
                    all_files.append(file_node)
                except Exception as e:
                    print(f"Error processing file {file_path}: {e}", file=sys.stderr)
                    continue
            
            # Update progress less frequently for large datasets
            if batch_idx % progress_update_frequency == 0 or i + batch_size >= total_files_to_scan:
                current_count = min(i + batch_size, total_files_to_scan)
                safe_progress_update({"type": "mapping_generation", "data": {
                    "status": "progress", 
                    "message": f"Batch processed {current_count}/{total_files_to_scan} files...",
                    "current_file_count": current_count,
                    "total_files": total_files_to_scan
                }})

        safe_progress_update({"type": "mapping_generation", "data": {
            "status": "progress", 
            "message": f"Collected details for {total_files_to_scan} files. Preparing for mapping..."
        }})
    else:
        # This recursive collect_files is harder to add granular progress to without modifying its signature
        # A single message before/after might be sufficient or refactor collect_files to accept callback
        def collect_files_recursive(node, collected_list):
            node_type = node.get("type", "unknown")
            if node_type == "file":
                collected_list.append(node)
            elif node_type == "folder":
                children_nodes = node.get("children", [])
                for child_node in children_nodes:
                    collect_files_recursive(child_node, collected_list)
        collect_files_recursive(tree, all_files)
    
    print(f"Collected {len(all_files)} total files", file=sys.stderr)
    safe_progress_update({"type": "mapping_generation", "data": {"status": "progress", "message": f"Collected {len(all_files)} files. Grouping sequences..."}})

    sequences, single_files = group_image_sequences(
        all_files, batch_id, extract_sequence_info=extract_sequence_info, is_network_path=is_network_path
    )
    print(f"Found {len(sequences)} image sequences and {len(single_files)} single files", file=sys.stderr)
    safe_progress_update({"type": "mapping_generation", "data": {"status": "progress", "message": f"Found {len(sequences)} sequences, {len(single_files)} single files."}})
    
    mappings = []
    sequence_errors = 0
    if sequences:
        safe_progress_update({"type": "mapping_generation", "data": {"status": "progress", "message": f"Processing {len(sequences)} image sequences..."}})
    
    # Rate limit sequence progress updates
    sequence_update_frequency = max(1, len(sequences) // 10) if sequences else 1  # Max 10 updates for sequences
    
    for idx, sequence_item in enumerate(sequences):
        # Only update progress every N sequences to avoid UI flood
        if idx % sequence_update_frequency == 0 or idx == len(sequences) - 1:
            safe_progress_update({"type": "mapping_generation", "data": {
                "status": "progress", 
                "message": f"Sequence {idx + 1}/{len(sequences)}",
                "current_file_count": idx + 1,
                "total_files": len(sequences)
            }})
        try:
            original_base_name = None
            if isinstance(sequence_item, dict) and "base_name" in sequence_item:
                original_base_name = sequence_item.get("base_name")
            elif isinstance(sequence_item, list) and len(sequence_item) > 0:
                for file_item_detail in sequence_item[:10]: # Renamed file_item to file_item_detail
                    if isinstance(file_item_detail, str) and os.path.basename(file_item_detail):
                        filename = os.path.basename(file_item_detail)
                        seq_info = extract_sequence_info(filename)
                        if seq_info and seq_info.get("base_name"):
                            original_base_name = seq_info.get("base_name")
                            break
                    elif isinstance(file_item_detail, dict) and file_item_detail.get("name"):
                        filename = file_item_detail.get("name")
                        seq_info = extract_sequence_info(filename)
                        if seq_info and seq_info.get("base_name"):
                            original_base_name = seq_info.get("base_name")
                            break
            seq_mapping = create_sequence_mapping(sequence_item, profile, original_base_name)
            if isinstance(seq_mapping, list):
                mappings.extend(seq_mapping)
            elif seq_mapping:
                mappings.append(seq_mapping)
        except Exception as e:
            sequence_errors += 1
            seq_name_str = "unknown_sequence"
            if isinstance(sequence_item, dict):
                seq_name_str = sequence_item.get('base_name', 'unknown_sequence')
            elif isinstance(sequence_item, list) and len(sequence_item) > 0:
                if isinstance(sequence_item[0], dict) and 'name' in sequence_item[0]:
                    seq_name_str = sequence_item[0]['name']
                elif isinstance(sequence_item[0], str):
                    seq_name_str = os.path.basename(sequence_item[0])
            print(f"[ERROR] Exception during mapping for sequence '{seq_name_str}': {type(e).__name__} - {e}\n{traceback.format_exc()}", file=sys.stderr, flush=True)
            safe_progress_update({"type": "mapping_generation", "data": {
                "status": "warning", 
                "message": f"Error processing sequence {seq_name_str}: {e}"
            }})
            
            # Create and append an error proposal for the sequence
            error_directory = "unknown_dir"
            error_files_list = []
            error_base_name_for_proposal = seq_name_str
            error_suffix_for_proposal = ""
            error_frame_range_for_proposal = ""

            if isinstance(sequence_item, dict):
                error_files_list = sequence_item.get("files", [])
                error_base_name_for_proposal = sequence_item.get("base_name", seq_name_str)
                error_suffix_for_proposal = sequence_item.get("suffix", "")
                error_frame_range_for_proposal = sequence_item.get("frame_range", "")
                error_directory = sequence_item.get("directory", "unknown_dir")
                if not error_directory or error_directory == "unknown_dir":
                    if error_files_list and isinstance(error_files_list[0], dict):
                        error_directory = os.path.dirname(error_files_list[0].get('path', ''))
                    elif error_files_list and isinstance(error_files_list[0], str):
                        error_directory = os.path.dirname(error_files_list[0])
            elif isinstance(sequence_item, list):
                error_files_list = sequence_item
                if error_files_list and isinstance(error_files_list[0], str):
                    error_directory = os.path.dirname(error_files_list[0])
                elif error_files_list and isinstance(error_files_list[0], dict):
                    error_directory = os.path.dirname(error_files_list[0].get('path', ''))
            
            sequence_name_for_proposal = f"{error_base_name_for_proposal}_####{error_suffix_for_proposal}" if error_base_name_for_proposal and error_suffix_for_proposal else seq_name_str

            error_proposal = {
                "id": str(uuid.uuid4()),
                "name": sequence_name_for_proposal,
                "source_directory": error_directory,
                "files": error_files_list, 
                "total_size_bytes": 0, 
                "status": "error",
                "type": "sequence",
                "shot": None, "asset": None, "stage": None, "task": None, "version": None, "resolution": None,
                "frame_range": error_frame_range_for_proposal,
                "frame_count": len(error_files_list),
                "suffix": error_suffix_for_proposal,
                "base_name": error_base_name_for_proposal,
                "targetPath": None,
                "error_message": f"{type(e).__name__}: {e}",
                "used_default_footage_rule": False,
                "ambiguous_match": False,
                "ambiguous_options": []
            }
            mappings.append(error_proposal)
    
    if sequence_errors > 0:
        print(f"[WARNING] Failed to process {sequence_errors} sequences", file=sys.stderr)
        safe_progress_update({"type": "mapping_generation", "data": {"status": "warning", "message": f"Completed sequence processing with {sequence_errors} errors."}})

    file_errors = 0
    if single_files:
        safe_progress_update({"type": "mapping_generation", "data": {"status": "progress", "message": f"Processing {len(single_files)} single files..."}})
    
    max_workers = min(16, os.cpu_count() * 2) # Ensure os.cpu_count() is not None
    print(f"[INFO] Using {max_workers if max_workers else 'default'} parallel workers for file processing", file=sys.stderr)
    
    # Rate limit single file progress updates
    file_update_frequency = max(1, len(single_files) // 10) if single_files else 1  # Max 10 updates for files
    
    if single_files: # Only run ThreadPoolExecutor if there are files to process
        try:
            # concurrent.futures is imported at the top
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_file = {executor.submit(create_simple_mapping, file_node, profile): file_node for file_node in single_files}
                for i, future in enumerate(as_completed(future_to_file)):
                    # Only update progress every N files to avoid UI flood
                    if i % file_update_frequency == 0 or i == len(single_files) - 1:
                        safe_progress_update({"type": "mapping_generation", "data": {
                            "status": "progress", 
                            "message": f"Single file {i + 1}/{len(single_files)}",
                            "current_file_count": i + 1,
                            "total_files": len(single_files)
                        }})
                    try:
                        mapping = future.result(timeout=30) # Increased timeout
                        if mapping: # Ensure mapping is not None before appending
                            mappings.append(mapping)
                    except Exception as e:
                        file_errors += 1
                        file_name_str = future_to_file[future].get('name', 'unknown_file')
                        print(f"[ERROR] Exception during mapping for file '{file_name_str}': {type(e).__name__} - {e}\n{traceback.format_exc()}", file=sys.stderr, flush=True)
                        # Only show errors occasionally to avoid UI flood
                        if file_errors <= 10:  # Only show first 10 errors
                            safe_progress_update({"type": "mapping_generation", "data": {
                                "status": "warning", 
                                "message": f"Error mapping file {file_name_str}: {e}"
                            }})
                        # Create and append an error proposal for the file
                        file_node_for_error = future_to_file[future]
                        error_proposal = {
                            "id": str(uuid.uuid4()),
                            "name": file_node_for_error.get('name', 'unknown_file'),
                            "sourcePath": file_node_for_error.get('path', 'unknown_path'),
                            "targetPath": None,
                            "status": "error",
                            "type": "file",
                            "shot": None, "asset": None, "stage": None, "task": None, "version": None, "resolution": None,
                            "node": file_node_for_error, # Keep the original node data
                            "error_message": f"{type(e).__name__}: {e}",
                            "used_default_footage_rule": False,
                            "ambiguous_match": False,
                            "ambiguous_options": []
                        }
                        mappings.append(error_proposal)
            if file_errors > 0:
                print(f"[WARNING] Failed to process {file_errors} files", file=sys.stderr)
                safe_progress_update({"type": "mapping_generation", "data": {"status": "warning", "message": f"Completed single file processing with {file_errors} errors."}})
        except Exception as e: # Catch broader ThreadPoolExecutor issues
            print(f"[ERROR] Major error during threaded file processing: {e}\n{traceback.format_exc()}", file=sys.stderr, flush=True)
            safe_progress_update({"type": "mapping_generation", "data": {"status": "error", "message": f"Error during threaded file processing: {e}"}})

    # Mapping summary prints
    auto_mapped = len([m for m in mappings if m and m.get("status") == "auto"]) # Added check for m not None
    manual_mapped = len([m for m in mappings if m and m.get("status") == "manual"])
    sequence_count_summary = len([m for m in mappings if m and m.get("type") == "sequence"])
    print(f"=== MAPPING SUMMARY ===", file=sys.stderr)
    print(f"Total mappings: {len(mappings)}", file=sys.stderr)
    print(f"Image sequences: {sequence_count_summary}", file=sys.stderr)
    print(f"Single files: {len(mappings) - sequence_count_summary}", file=sys.stderr)
    print(f"Auto-mapped: {auto_mapped}", file=sys.stderr)
    print(f"Manual required: {manual_mapped}", file=sys.stderr)

    safe_progress_update({"type": "mapping_generation", "data": {"status": "completed", "message": f"Mapping generation finished. {len(mappings)} total proposals."}})
    
    return mappings
