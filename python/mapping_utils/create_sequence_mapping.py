import os
import sys
from typing import Dict, Any, List, Union

def create_sequence_mapping(
    sequence: Union[Dict[str, Any], List[Any]],
    profile: Dict[str, Any],
    original_base_name: str = None,
    extract_shot_simple=None,
    extract_task_simple=None,
    extract_version_simple=None,
    extract_resolution_simple=None,
    extract_asset_simple=None,
    extract_stage_simple=None,
    generate_simple_target_path=None,
    extract_sequence_info=None,
    current_frame_numbers=None,
):
    """
    Modularized version of MappingGenerator._create_sequence_mapping.
    All dependencies must be passed in as arguments.
    """
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
        shot = extract_shot_simple(first_filename, first_filepath)
        asset = extract_asset_simple(first_filename)
        stage = extract_stage_simple(first_filename)
        task = extract_task_simple(first_filename, first_filepath)
        version = extract_version_simple(first_filename)
        resolution = extract_resolution_simple(first_filename, first_filepath)

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

        source_pattern = os.path.join(directory, sequence_filename)
        vfx_root = profile.get("vfxRootPath", "/vfx/projects/default")
        target_path = generate_simple_target_path(
            vfx_root, shot, asset, stage, task, version, resolution, sequence_filename, profile
        )

        # Determine mapping status
        if shot and task and version:
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
            "source": source_pattern,
            "destination": target_path,
            "status": status,
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
