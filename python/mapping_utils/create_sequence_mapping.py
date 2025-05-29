import os
import sys
from typing import Dict, Any, List, Union

def create_sequence_mapping(
    sequence: Union[Dict[str, Any], List[Any]],
    profile: Dict[str, Any],  # This is now the full profile dictionary
    root_output_dir: str, # The user-selected root output directory
    original_base_name: str = None,
    extract_shot_simple=None,
    extract_task_simple=None,
    extract_version_simple=None,
    extract_resolution_simple=None,
    extract_asset_simple=None,
    extract_stage_simple=None,
    generate_simple_target_path=None, # This is the actual function reference
    extract_sequence_info=None,
    current_frame_numbers=None,
    p_shot: List[str] = None,
    p_task: Dict[str, List[str]] = None,
    p_version: List[str] = None,
    p_resolution: List[str] = None,
    p_asset: List[str] = None,
    p_stage: List[str] = None,
):
    """
    Modularized version of MappingGenerator._create_sequence_mapping.
    # All dependencies must be passed in as arguments.
    """
    # Extract the list of rules from the full profile dictionary
    # The generate_simple_target_path function and others expect just the list of rules.
    actual_profile_rules = profile.get('rules', [])
    profile_name_for_logging = profile.get('name', 'Unknown Profile') # For logging/debugging

    # Example of using profile name for logging, which might have caused NameError before
    print(f"[DEBUG] create_sequence_mapping invoked for profile: '{profile_name_for_logging}'", file=sys.stderr)

    try:
        # Handle both dict and list sequence representations
        if isinstance(sequence, dict):
            files_list = sequence.get("files", [])
            base_name = sequence.get("base_name", "")
            suffix = sequence.get("suffix", "")
            directory = sequence.get("directory", "")
            frame_range = sequence.get("frame_range", "")
            frame_count = sequence.get("frame_count", 0)
            frame_numbers = sequence.get("frame_numbers", [])
        elif isinstance(sequence, list):
            files_list = sequence
            base_name = original_base_name or ""
            suffix = ""
            directory = ""
            frame_range = ""
            frame_count = len(sequence)
            frame_numbers = []
        else:
            return {
                "source": "unknown",
                "destination": "unknown",
                "reason": "Invalid sequence input."
            }

        # Use the first file for extraction
        first_file = files_list[0] if files_list else None
        if not first_file:
            return {
                "source": "unknown",
                "destination": "unknown",
                "reason": "Empty sequence."
            }

        if isinstance(first_file, str):
            first_filename = os.path.basename(first_file)
            first_filepath = first_file
        else:
            first_filename = first_file.get("name", "")
            first_filepath = first_file.get("path", "")

        # Extract shot, asset, stage, task, version, resolution
        # Patterns are now passed as direct arguments from MappingGenerator's global patterns
        shot_patterns = p_shot if p_shot is not None else []
        version_patterns = p_version if p_version is not None else []
        resolution_patterns = p_resolution if p_resolution is not None else []
        asset_patterns = p_asset if p_asset is not None else []
        stage_patterns = p_stage if p_stage is not None else []
        task_patterns = p_task if p_task is not None else {}
        
        print(f"[DEBUG] Using global resolution patterns: {resolution_patterns}", file=sys.stderr)
        
        # Debug: print what will be checked for resolution (FILENAME ONLY, per IMPORTANT.md)
        print(f"[DEBUG] Checking resolution for FILENAME ONLY: {first_filename}", file=sys.stderr)
        
        # Extract resolution using filename only (no path)
        if extract_resolution_simple:
            # This call uses 'resolution_patterns' which is now sourced from p_resolution
            resolution_result = extract_resolution_simple(first_filename, "", resolution_patterns) 
            print(f"[DEBUG] Resolution extraction result: {resolution_result}", file=sys.stderr)
        else:
            resolution_result = None
            print(f"[DEBUG] extract_resolution_simple not provided", file=sys.stderr)

        # Instrumentation for asset_patterns (now sourced from p_asset)
        for idx, pattern_value in enumerate(asset_patterns):
            color = '\033[93;1m'
            reset = '\033[0m'
            icon = '[NICK]'
            print(f"{color}{icon} [CREATE_SEQ_MAP] Asset pattern {idx}: type={type(pattern_value)}, value={pattern_value}{reset}", flush=True)

        # IMPORTANT: Only search filename, never path (per IMPORTANT.md)
        shot = extract_shot_simple(first_filename, "", shot_patterns)
        asset_regex_pattern = profile.get("assetRegexPattern", r"(?<![a-zA-Z0-9]){{asset}}(?![a-zA-Z0-9])")
        asset_regex_flags = profile.get("assetRegexFlags", "IGNORECASE")
        # Convert string flags to re flags
        import re
        flag_value = 0
        for flag in asset_regex_flags.split(',') if isinstance(asset_regex_flags, str) else []:
            flag = flag.strip().upper()
            if hasattr(re, flag):
                flag_value |= getattr(re, flag)
        if not flag_value:
            flag_value = re.IGNORECASE
        # asset_patterns is guaranteed to be a list of strings (not compiled regex)
        if not isinstance(asset_regex_pattern, str):
            print(f"[ASSET_EXTRACTOR ERROR] asset_regex_pattern is not a string: {asset_regex_pattern} (type={type(asset_regex_pattern)})", flush=True)
            assert isinstance(asset_regex_pattern, str), f"asset_regex_pattern must be a string, got {type(asset_regex_pattern)}"
        # Debug print before asset extraction
        print(f"[NICK] [DEBUG] About to call extract_asset_simple:")
        print(f"    asset_patterns types: {[type(a) for a in asset_patterns]}")
        print(f"    asset_regex_pattern type: {type(asset_regex_pattern)}, value: {asset_regex_pattern}")
        print(f"    asset_regex_flags type: {type(flag_value)}, value: {flag_value}")
        # IMPORTANT: Only search filename, never path (per IMPORTANT.md)
        asset = extract_asset_simple(first_filename, asset_patterns)
        stage = extract_stage_simple(first_filename, stage_patterns)
        task = extract_task_simple(first_filename, "", task_patterns)
        # IMPORTANT: Only search filename (already compliant with IMPORTANT.md)
        version = extract_version_simple(first_filename, version_patterns)
        # IMPORTANT: Only search filename, never path (per IMPORTANT.md)
        resolution = extract_resolution_simple(first_filename, "", resolution_patterns) if extract_resolution_simple else None

        # Fallback for base_name and suffix if not present
        if not base_name or not suffix:
            seq_info = extract_sequence_info(first_filename) if extract_sequence_info else None
            if seq_info:
                base_name = seq_info.get("base_name", base_name)
                suffix = seq_info.get("suffix", suffix)

        # Compose sequence filename
        sequence_filename = f"{base_name}_####{suffix}" if base_name and suffix else first_filename

        # Compose directory if missing
        if not directory and first_filepath:
            directory = os.path.dirname(first_filepath)
        elif not directory:
            directory = os.getcwd()

        # Call the updated generate_simple_target_path
        path_generation_result = generate_simple_target_path(
            root_output_dir=root_output_dir,
            profile_rules=actual_profile_rules, # Use the extracted list of rules
            filename=sequence_filename, # Use the representative sequence filename
            parsed_shot=shot,
            parsed_task=task,
            parsed_asset=asset,
            parsed_stage=stage,
            parsed_version=version,
            parsed_resolution=resolution
        )

        target_path = path_generation_result["target_path"] # This can be None if ambiguous
        used_default_footage_rule = path_generation_result["used_default_footage_rule"]
        ambiguous_match = path_generation_result["ambiguous_match"]
        ambiguous_options = path_generation_result["ambiguous_options"]

        # Now, determine destination_full_path based on the resolved target_path
        destination_full_path = None
        if target_path: # Only construct if a non-ambiguous path was determined
            destination_full_path = os.path.join(target_path, sequence_filename)
        # If target_path is None (due to ambiguity), destination_full_path remains None

        # Determine mapping status
        if shot and task and version and not used_default_footage_rule and not ambiguous_match:
            status = "auto"
        else:
            status = "manual"

        # Validate files and calculate total size
        total_size = 0
        validated_files = []
        for file_node in files_list:
            if isinstance(file_node, str):
                file_path = file_node
                file_name = os.path.basename(file_path)
                file_size = 0
                try:
                    if os.path.exists(file_path):
                        file_size = os.path.getsize(file_path)
                except Exception as e:
                    print(f"[WARNING] Could not get file size for {file_path}: {e}", file=sys.stderr)
                _, file_ext = os.path.splitext(file_name)
                file_ext = file_ext.lstrip('.')
                validated_file = {
                    "name": file_name,
                    "path": file_path,
                    "type": "file",
                    "size": file_size,
                    "extension": file_ext,
                }
            else:
                validated_file = {
                    "name": file_node.get("name", "unknown_file"),
                    "path": file_node.get("path", ""),
                    "type": file_node.get("type", "file"),
                    "size": file_node.get("size", 0),
                    "extension": file_node.get("extension", ""),
                }
            validated_files.append(validated_file)
            total_size += validated_file["size"]

        # Add start/end to sequence dict for backend compatibility
        frame_numbers_list = frame_numbers if frame_numbers else (current_frame_numbers if current_frame_numbers is not None else [])
        seq_dict = {
            "base_name": base_name,
            "frame_range": frame_range,
            "frame_count": frame_count,
            "total_size": total_size,
            "files": validated_files,
            "frame_numbers": frame_numbers_list,
            "used_default_footage_rule": used_default_footage_rule,
            "ambiguous_match": ambiguous_match
        }
        if frame_numbers_list:
            try:
                seq_dict["start"] = min(frame_numbers_list)
                seq_dict["end"] = max(frame_numbers_list)
            except Exception as e:
                print(f"[WARNING] Could not extract min/max from frame numbers: {e}", file=sys.stderr)
        else:
            print(f"[WARNING] No frame numbers available for sequence", file=sys.stderr)

        mapping = {
            "source": os.path.join(directory, sequence_filename),
            "destination": destination_full_path,
            "status": status,
            "reason": "",
            "ambiguous_match": ambiguous_match,
            "ambiguous_options": ambiguous_options,
            "sequence": seq_dict,
        }
        return mapping
    except Exception as e:
        print(f"[ERROR] Exception in create_sequence_mapping: {e}", file=sys.stderr)
        return {
            "source": "unknown",
            "destination": "unknown",
            "reason": f"Exception: {e}"
        }
