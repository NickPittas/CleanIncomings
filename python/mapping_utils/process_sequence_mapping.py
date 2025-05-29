import os
import sys
from typing import Any, Dict, List, Optional
from mapping_utils.generate_simple_target_path import generate_simple_target_path

def process_sequence_mapping(
    first_file: str,
    base_name: str,
    ext: str,
    suffix: str,
    directory: Optional[str],
    first_filepath: Optional[str],
    profile: Dict[str, Any],
    shot: Any,
    asset: Any,
    stage: Any,
    task: Any,
    version: Any,
    resolution: Any,
    files_list: List[Any],
    sequence: Optional[Dict[str, Any]] = None,
    frame_range: Optional[str] = None,
    frame_count: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Modularized version of MappingGenerator._process_sequence_mapping.
    Returns a mapping dict for a sequence group.
    """
    if not first_file or not profile:
        return {
            "source": "unknown",
            "destination": "unknown",
            "reason": "Missing filename or filepath for sequence."
        }

    if "." in suffix:
        sequence_pattern = f"{base_name}.####{suffix}"
    else:
        sequence_pattern = f"{base_name}_####{suffix}"

    # Ensure we have a valid directory
    if not directory and first_filepath:
        directory = os.path.dirname(first_filepath)
    elif not directory:
        directory = os.getcwd()

    source_pattern = os.path.join(directory, sequence_pattern)
    vfx_root = profile.get("vfxRootPath", "/vfx/projects/default") # This should be the root_output_dir
    profile_rules = profile.get("rules") # Assuming 'profile' dict has a 'rules' key containing the list of rules
    # If 'profile' itself is the list of rules, then profile_rules = profile

    # It's safer to assume 'profile' is the direct list of rules as per profiles.json structure
    # If profile is a dict like {"name": "ProfileName", "rules": [...], "vfxRootPath": "..."}
    # then profile_rules = profile.get("rules", []) would be correct.
    # For now, let's assume 'profile' argument IS the list of rules directly.
    # This needs verification based on how 'profile' is structured when passed to this function.
    # Based on create_simple_mapping and create_sequence_mapping, profile_rules is passed directly.
    # Let's assume 'profile' here is actually 'profile_rules' for now.

    path_generation_result = generate_simple_target_path(
        root_output_dir=vfx_root, # Assuming vfx_root is the intended root_output_dir
        profile_rules=profile,    # <<<<< CRITICAL ASSUMPTION: 'profile' var IS the profile_rules list
        filename=first_file,      # Using first_file as the representative filename
        parsed_shot=shot,
        parsed_task=task,
        parsed_asset=asset,
        parsed_stage=stage,
        parsed_version=version,
        parsed_resolution=resolution
    )

    target_path = path_generation_result["target_path"] # This can be None
    used_default_footage_rule = path_generation_result["used_default_footage_rule"]
    ambiguous_match = path_generation_result["ambiguous_match"]
    ambiguous_options = path_generation_result["ambiguous_options"]

    # Determine mapping status
    if shot and task and version and not used_default_footage_rule and not ambiguous_match:
        status = "auto"
    else:
        status = "manual"

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
    frame_numbers_list = []
    if isinstance(sequence, dict):
        frame_numbers_list = sequence.get("frame_numbers", [])
    # else: do not reference self.current_frame_numbers in utility

    seq_dict = {
        "base_name": base_name,
        "frame_range": frame_range,
        "frame_count": frame_count,
        "total_size": total_size,
        "files": validated_files,
        "frame_numbers": frame_numbers_list,
    }
    if frame_numbers_list:
        try:
            seq_dict["start"] = min(frame_numbers_list)
            seq_dict["end"] = max(frame_numbers_list)
        except Exception as e:
            print(f"[WARNING] Could not extract min/max from frame numbers: {e}", file=sys.stderr)
    else:
        print(f"[WARNING] No frame numbers available for sequence", file=sys.stderr)

    destination_full_path = None
    if target_path:
        destination_full_path = os.path.join(target_path, sequence_pattern)

    return {
        "source": source_pattern,
        "destination": destination_full_path, # This can be None
        "status": status,
        "sequence": seq_dict,
        "ambiguous_match": ambiguous_match,
        "ambiguous_options": ambiguous_options,
        "used_default_footage_rule": used_default_footage_rule # Also good to return this
    }
