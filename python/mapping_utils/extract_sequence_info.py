import re
from typing import Optional, Dict, Any

def extract_sequence_info(
    sequence,
    profile=None,
    original_base_name=None,
    extract_shot_simple=None,
    extract_asset_simple=None,
    extract_stage_simple=None,
    extract_task_simple=None,
    extract_version_simple=None,
    extract_resolution_simple=None,
    create_sequence_mapping=None,
):
    """
    Ported from MappingGenerator._extract_sequence_info: supports both filename and sequence dict/list, and performs mapping extraction and error handling as in the original.
    """
    import os
    # Handle filename-only input (simple case)
    if isinstance(sequence, str):
        filename = sequence
        if not filename or not isinstance(filename, str):
            return None
        if "sequence_" in filename or filename == "_####" or filename.endswith("_####"):
            return None
            
        # Multiple patterns to detect sequences with different frame number positions
        patterns = [
            # Pattern 1: basename.framenumber.extension (e.g., sequence.1001.exr)
            r"^(.+?)\.(\d{1,10})(\.[^.]+)$",
            # Pattern 2: basename_framenumber.extension (e.g., ASSET_01_v019_ALi_1001.exr) 
            r"^(.+?)_(\d{4,10})(\.[^.]+)$",
            # Pattern 3: basename.framenumber_suffix.extension (e.g., ASSET_01_v019.1001_ALi.exr)
            r"^(.+?)\.(\d{4,10})_(.+?)(\.[^.]+)$",
            # Pattern 4: basename_framenumber_suffix.extension (e.g., ASSET_01_v019_1001_ALi.exr)
            r"^(.+?)_(\d{4,10})_(.+?)(\.[^.]+)$"
        ]
        
        for pattern in patterns:
            try:
                match = re.match(pattern, filename, re.IGNORECASE)
                if match:
                    groups = match.groups()
                    if len(groups) >= 3:
                        if len(groups) == 3:  # Pattern 1 and 2
                            base_name, frame_str, suffix = groups
                        else:  # Pattern 3 and 4
                            base_name, frame_str, middle_part, suffix = groups
                            # Reconstruct base name to include the middle part for consistency
                            base_name = f"{base_name}_{middle_part}" if middle_part else base_name
                            
                        if not base_name or base_name == "_" or "sequence_" in base_name:
                            continue
                            
                        try:
                            frame_num = int(frame_str)
                            # Only consider it a valid frame if it's within reasonable range
                            if 0 <= frame_num <= 999999:  # Reasonable frame number range
                                return {
                                    "base_name": base_name,
                                    "frame": frame_num,
                                    "suffix": suffix
                                }
                        except ValueError:
                            continue
            except Exception:
                continue
                
        return None

    # --- Full advanced logic for dict/list input ---
    # Extract the first file from the sequence
    first_file = None
    first_filename = ""
    first_filepath = ""
    base_name = ""
    extraction_source = ""
    # --- Handle multi-sequence input: list of dicts with base_name ---
    if isinstance(sequence, list) and len(sequence) > 0 and all(isinstance(item, dict) and 'base_name' in item for item in sequence):
        mappings = []
        for i, seq_dict in enumerate(sequence):
            mapping = None
            if create_sequence_mapping:
                mapping = create_sequence_mapping(seq_dict, profile, seq_dict.get('base_name'))
            if isinstance(mapping, list):
                mappings.extend(mapping)
            elif mapping:
                mappings.append(mapping)
        return mappings
    # --- Normal single-sequence logic ---
    if isinstance(sequence, dict):
        base_name = sequence.get("base_name", "")
        if base_name:
            extraction_source = base_name
        elif original_base_name:
            base_name = original_base_name
            extraction_source = base_name
        elif "files" in sequence and sequence["files"]:
            first_file = sequence["files"][0]
            if isinstance(first_file, dict) and 'name' in first_file:
                extraction_source = first_file['name']
            elif isinstance(first_file, str):
                extraction_source = first_file
        else:
            extraction_source = ""
    elif isinstance(sequence, list) and len(sequence) > 0:
        first_file = sequence[0]
        if isinstance(first_file, dict) and 'name' in first_file:
            extraction_source = first_file['name']
        elif isinstance(first_file, str):
            extraction_source = first_file
    else:
        extraction_source = ""

    if not extraction_source:
        extraction_source = ""

    def safe_extract(method, label):
        try:
            if method:
                val = method(extraction_source)
                if val:
                    return val
        except Exception:
            return "unmatched"
        else:
            pass

    shot_code = safe_extract(extract_shot_simple, 'shot_code')
    asset_code = safe_extract(extract_asset_simple, 'asset_code')
    stage_code = safe_extract(extract_stage_simple, 'stage_code')
    task_code = safe_extract(extract_task_simple, 'task_code')
    version_code = safe_extract(extract_version_simple, 'version_code')
    res_code = safe_extract(extract_resolution_simple, 'res_code')

    suffix = ""
    frame_range = ""
    frame_count = 0
    directory = ""
    ext = ""
    files_list = []
    all_filenames = []
    base_name_candidates = {}

    if isinstance(sequence, list) and len(sequence) > 0:
        # See if any of the sequence files have a common pattern
        real_filenames = []
        real_filepaths = []
        for file_item in sequence:
            if file_item:
                if isinstance(file_item, str) and os.path.basename(file_item):
                    filename = os.path.basename(file_item)
                    real_filenames.append(filename)
                    real_filepaths.append(file_item)
                elif isinstance(file_item, dict):
                    found_name = None
                    found_path = None
                    for name_key in ['name', 'filename', 'file', 'basename', 'Name', 'FileName', 'File']:
                        if name_key in file_item and file_item[name_key]:
                            found_name = file_item[name_key]
                elif isinstance(file_item, dict) and file_item.get('name'):
                    filename = file_item.get('name')
                    all_filenames.append(filename)
                    seq_info = extract_sequence_info(filename)
                    if seq_info and seq_info.get("base_name"):
                        base_name_pattern = seq_info.get("base_name")
                        base_name_candidates[base_name_pattern] = base_name_candidates.get(base_name_pattern, 0) + 1
                    if file_item.get('base_name'):
                        explicit_base = file_item.get('base_name')
                        if explicit_base and explicit_base != "_" and "sequence_" not in explicit_base:
                            base_name_candidates[explicit_base] = base_name_candidates.get(explicit_base, 0) + 5
        if base_name_candidates:
            most_common_base = max(base_name_candidates.items(), key=lambda x: x[1])[0]
            if not base_name:
                base_name = most_common_base
        for potential_file in sequence:
            if potential_file:
                if isinstance(potential_file, str) and os.path.basename(potential_file):
                    filename = os.path.basename(potential_file)
                    seq_info = extract_sequence_info(filename)
                    if seq_info and seq_info.get("base_name") == base_name:
                        first_file = potential_file
                        break
                    elif seq_info and seq_info.get("base_name"):
                        first_file = potential_file
                elif isinstance(potential_file, dict) and potential_file.get('name'):
                    filename = potential_file.get('name')
                    seq_info = extract_sequence_info(filename)
                    if seq_info and seq_info.get("base_name") == base_name:
                        first_file = potential_file
                        break
                    elif seq_info and seq_info.get("base_name"):
                        first_file = potential_file
        if first_file:
            if isinstance(first_file, str):
                first_filename = os.path.basename(first_file)
                first_filepath = first_file
                directory = os.path.dirname(first_file)
            elif isinstance(first_file, dict):
                first_filename = first_file.get("name", "")
                first_filepath = first_file.get("path", "")
                if first_filepath:
                    directory = os.path.dirname(first_filepath)
            seq_info = extract_sequence_info(first_filename)
            if seq_info:
                base_name = seq_info.get("base_name", base_name)
                suffix = seq_info.get("suffix", suffix)
            files_list = sequence
            frame_numbers = [f.get("frame") if isinstance(f, dict) and "frame" in f else None for f in files_list]
            frame_numbers = [f for f in frame_numbers if f is not None]
            min_frame = min(frame_numbers) if frame_numbers else None
            max_frame = max(frame_numbers) if frame_numbers else None
            min_frame_file = None
            max_frame_file = None
            for file_item in files_list:
                file_name = ""
                if isinstance(file_item, str):
                    file_name = os.path.basename(file_item)
                    file_path = file_item
                elif isinstance(file_item, dict) and "name" in file_item:
                    file_name = file_item.get("name", "")
                    file_path = file_item.get("path", "")
                if file_name:
                    file_seq_info = extract_sequence_info(file_name)
                    if file_seq_info and "frame" in file_seq_info:
                        if file_seq_info["frame"] == min_frame and not min_frame_file:
                            min_frame_file = file_item
                        if file_seq_info["frame"] == max_frame and not max_frame_file:
                            max_frame_file = file_item
            try:
                if not base_name and min_frame_file:
                    if isinstance(min_frame_file, str):
                        min_filename = os.path.basename(min_frame_file)
                    elif isinstance(min_frame_file, dict) and "name" in min_frame_file:
                        min_filename = min_frame_file.get("name", "")
            except Exception as e:
                return {
                    "source": "unknown",
                    "destination": "unknown",
                    "reason": f"Failed to process sequence: {str(e)}"
                }
        if not first_file or not profile:
            return {
                "source": "unknown",
                "destination": "unknown",
                "reason": "Missing required sequence mapping input."
            }
        if isinstance(first_file, str):
            first_filename = os.path.basename(first_file)
            first_filepath = first_file
        else:
            first_filename = first_file.get("name", "")
            first_filepath = first_file.get("path", "")
        if not first_filename or not first_filepath:
            return {
                "source": "unknown",
                "destination": "unknown",
                "reason": "Missing filename or filepath for first file."
            }
    # You can add more return fields as needed for downstream logic
    return {
        "base_name": base_name,
        "first_filename": first_filename,
        "first_filepath": first_filepath,
        "directory": directory,
        "shot_code": shot_code,
        "asset_code": asset_code,
        "stage_code": stage_code,
        "task_code": task_code,
        "version_code": version_code,
        "res_code": res_code,
        "suffix": suffix,
        "frame_count": frame_count,
        "frame_range": frame_range,
        "files_list": files_list,
        "all_filenames": all_filenames,
    }
