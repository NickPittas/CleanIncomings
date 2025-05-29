import os
import sys
import traceback
from pathlib import Path
from typing import List, Dict, Any
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
) -> List[Dict[str, Any]]:
    """
    Modularized mapping generation logic. All dependencies must be passed as arguments.
    """
    print(f"=== MAPPING GENERATION STARTED ===", file=sys.stderr)
    print(f"Profile: {profile.get('name', 'Unknown')}", file=sys.stderr)
    print(f"VFX Root: {profile.get('vfx_root', '/vfx/projects/default')}", file=sys.stderr)
    print(f"Tree: {tree.get('name', 'Unknown')} (type: {tree.get('type', 'unknown')})", file=sys.stderr)
    children = tree.get("children", [])
    print(f"Processing {len(children)} items", file=sys.stderr)
    if batch_id:
        pass # Placeholder for removed progress update
    all_files = []
    if "_all_files" in tree and tree["_all_files"]:
        print(f"Using _all_files list from folders-only tree", file=sys.stderr)
        for file_path in tree["_all_files"]:
            try:
                path_obj = Path(file_path)
                stat_info = path_obj.stat()
                file_node = {
                    "name": path_obj.name,
                    "path": str(path_obj),
                    "type": "file",
                    "size": stat_info.st_size,
                    "extension": path_obj.suffix.lower(),
                }
                all_files.append(file_node)
            except Exception as e:
                print(f"Error processing file {file_path}: {e}", file=sys.stderr)
                continue
    else:
        def collect_files(node):
            node_type = node.get("type", "unknown")
            if node_type == "file":
                all_files.append(node)
            elif node_type == "folder":
                children = node.get("children", [])
                for child in children:
                    collect_files(child)
        collect_files(tree)
    print(f"Collected {len(all_files)} total files", file=sys.stderr)
    if batch_id:
        pass # Placeholder for removed progress update
    sequences, single_files = group_image_sequences(
        all_files, batch_id, extract_sequence_info=extract_sequence_info, is_network_path=is_network_path
    )
    print(f"Found {len(sequences)} image sequences and {len(single_files)} single files", file=sys.stderr)
    mappings = []
    total_items = len(sequences) + len(single_files)
    processed = 0
    print(f"[INFO] Starting to process {len(sequences)} sequences and {len(single_files)} single files", file=sys.stderr)
    sequence_errors = 0
    for idx, sequence in enumerate(sequences):
        try:
            original_base_name = None
            if isinstance(sequence, dict) and "base_name" in sequence:
                original_base_name = sequence.get("base_name")
            elif isinstance(sequence, list) and len(sequence) > 0:
                for file_item in sequence[:10]:
                    if isinstance(file_item, str) and os.path.basename(file_item):
                        filename = os.path.basename(file_item)
                        seq_info = extract_sequence_info(filename)
                        if seq_info and seq_info.get("base_name"):
                            original_base_name = seq_info.get("base_name")
                            break
                        filename = os.path.basename(file_item)
                        seq_info = extract_sequence_info(filename)
                        if seq_info and seq_info.get("base_name"):
                            original_base_name = seq_info.get("base_name")
                            break
                    elif isinstance(file_item, dict) and file_item.get("name"):
                        filename = file_item.get("name")
                        seq_info = extract_sequence_info(filename)
                        if seq_info and seq_info.get("base_name"):
                            original_base_name = seq_info.get("base_name")
                            break
            seq_mapping = create_sequence_mapping(sequence, profile, original_base_name)
            if isinstance(seq_mapping, list):
                mappings.extend(seq_mapping)
                processed += len(seq_mapping)
            elif seq_mapping:
                mappings.append(seq_mapping)
                processed += 1
        except Exception as e:
            sequence_errors += 1
            seq_name = "unknown"
            if isinstance(sequence, dict):
                seq_name = sequence.get('base_name', 'unknown')
            elif isinstance(sequence, list) and len(sequence) > 0:
                if isinstance(sequence[0], dict) and 'name' in sequence[0]:
                    seq_name = sequence[0]['name']
                elif isinstance(sequence[0], str):
                    seq_name = os.path.basename(sequence[0])
            continue
    if sequence_errors > 0:
        print(f"[WARNING] [NICK]Failed to process {sequence_errors} sequences", file=sys.stderr)
    max_workers = min(16, os.cpu_count() * 2)
    print(f"[INFO] [NICK]Using {max_workers} parallel workers for file processing", file=sys.stderr)
    try:
        from concurrent.futures import ThreadPoolExecutor, as_completed
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_file = {executor.submit(create_simple_mapping, file_node, profile): file_node for file_node in single_files}
            file_errors = 0
            for i, future in enumerate(as_completed(future_to_file)):
                try:
                    mapping = future.result(timeout=10)
                    mappings.append(mapping)
                    processed += 1
                except Exception as e:
                    file_errors += 1
                    file_name = future_to_file[future].get('name', 'unknown')
                    print(f"[ERROR] Exception during mapping for file '{file_name}': {type(e).__name__} - {e}\n{traceback.format_exc()}", file=sys.stderr, flush=True)
                if batch_id and i % max(1, min(500, len(single_files) // 20)) == 0:
                    # Progress update removed
                    print(f"[PROGRESS] File mapping: {i+1}/{len(single_files)} ({(i+1)/len(single_files)*100:.1f}%)", file=sys.stderr)
            if file_errors > 0:
                print(f"[WARNING] Failed to process {file_errors} files", file=sys.stderr)
    except Exception as e:
        pass
    auto_mapped = len([m for m in mappings if m.get("status") == "auto"])
    manual_mapped = len([m for m in mappings if m.get("status") == "manual"])
    sequence_count = len([m for m in mappings if m.get("type") == "sequence"])
    print(f"=== MAPPING SUMMARY ===", file=sys.stderr)
    print(f"Total mappings: {len(mappings)}", file=sys.stderr)
    print(f"Image sequences: {sequence_count}", file=sys.stderr)
    print(f"Single files: {len(mappings) - sequence_count}", file=sys.stderr)
    print(f"Auto-mapped: {auto_mapped}", file=sys.stderr)
    print(f"Manual required: {manual_mapped}", file=sys.stderr)
    return mappings
