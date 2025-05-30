"""
Optimized Create Sequence Mapping

Creates mapping proposals for sequences using cached pattern extraction
for improved performance.
"""

import os
import sys
import re
from pathlib import Path
from typing import Union, Dict, Any, List
from .pattern_cache import extract_all_patterns_cached


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
    override_extracted_values: Dict[str, Any] = None,  # New parameter for batch editing
):
    """
    Creates a mapping proposal for a sequence using optimized pattern caching.
    
    Key optimization: Pattern matching is done once per sequence using the sequence base name
    instead of per individual file, dramatically improving performance.
    """
    import uuid
    from .generate_simple_target_path import generate_simple_target_path

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

        # Use the first file for extraction if base_name is not available
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

        # OPTIMIZATION: Use sequence base name for pattern matching if available
        # This is the key optimization - instead of extracting patterns from individual files,
        # we extract once from the sequence base name or first file
        extraction_filename = base_name if base_name else first_filename
        
        print(f"[OPTIMIZED] Extracting patterns from sequence base: '{extraction_filename}' (vs {len(files_list)} individual files)", file=sys.stderr)

        # Extract all patterns at once using cached extraction
        # This single call replaces multiple individual extract_*_simple calls
        if (p_shot is not None and p_task is not None and p_version is not None and 
            p_resolution is not None and p_asset is not None and p_stage is not None):
            
            pattern_results = extract_all_patterns_cached(
                extraction_filename,
                p_shot,
                p_task,
                p_version,
                p_resolution,
                p_asset,
                p_stage
            )
            
            shot = pattern_results['shot']
            task = pattern_results['task']
            version = pattern_results['version']
            resolution = pattern_results['resolution']
            asset = pattern_results['asset']
            stage = pattern_results['stage']
            
            # Override extracted values if provided (for batch editing)
            if override_extracted_values:
                shot = override_extracted_values.get('shot', shot)
                task = override_extracted_values.get('task', task)
                version = override_extracted_values.get('version', version)
                resolution = override_extracted_values.get('resolution', resolution)
                asset = override_extracted_values.get('asset', asset)
                stage = override_extracted_values.get('stage', stage)
                print(f"[BATCH_EDIT_OVERRIDE] Applied overrides: shot={shot}, task={task}, version={version}, resolution={resolution}, asset={asset}, stage={stage}", file=sys.stderr)
            
            print(f"[OPTIMIZED] Final extraction results: shot={shot}, task={task}, version={version}, resolution={resolution}, asset={asset}, stage={stage}", file=sys.stderr)
        else:
            # Fallback to individual extraction functions if patterns not provided
            print(f"[FALLBACK] Using individual extraction functions", file=sys.stderr)
            shot = extract_shot_simple(extraction_filename, "", p_shot or []) if extract_shot_simple else None
            task = extract_task_simple(extraction_filename, "", p_task or {}) if extract_task_simple else None
            version = extract_version_simple(extraction_filename, p_version or []) if extract_version_simple else None
            resolution = extract_resolution_simple(extraction_filename, "", p_resolution or []) if extract_resolution_simple else None
            asset = extract_asset_simple(extraction_filename, p_asset or []) if extract_asset_simple else None
            stage = extract_stage_simple(extraction_filename, p_stage or []) if extract_stage_simple else None
            
            # Override extracted values if provided (for batch editing)
            if override_extracted_values:
                shot = override_extracted_values.get('shot', shot)
                task = override_extracted_values.get('task', task)
                version = override_extracted_values.get('version', version)
                resolution = override_extracted_values.get('resolution', resolution)
                asset = override_extracted_values.get('asset', asset)
                stage = override_extracted_values.get('stage', stage)
                print(f"[BATCH_EDIT_OVERRIDE] Applied overrides: shot={shot}, task={task}, version={version}, resolution={resolution}, asset={asset}, stage={stage}", file=sys.stderr)

        # Rest of the function remains the same - generate target path and create proposal
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
        
        # Generate the target path using the extracted values
        profile_rules = profile.get("rules", [])
        target_path_result = generate_simple_target_path(
            root_output_dir=root_output_dir,
            profile_rules=profile_rules,
            filename=sequence_pattern,
            parsed_shot=shot,
            parsed_task=task,
            parsed_asset=asset,
            parsed_stage=stage,
            parsed_version=version,
            parsed_resolution=resolution
        )

        # Extract the actual path from the result
        target_path = target_path_result.get("target_path")
        if not target_path:
            target_path = os.path.join(root_output_dir, "unmatched", sequence_pattern)

        # Create the sequence proposal
        sequence_proposal = {
            "id": str(uuid.uuid4()),
            "original_item": {
                "name": sequence_pattern,
                "path": source_pattern,
                "type": "sequence",
                "size": sum(f.get("size", 0) if isinstance(f, dict) else 0 for f in files_list),
            "frame_count": frame_count,
                "frame_range": frame_range
            },
            "targetPath": target_path,
            "type": "sequence",
            "status": "auto" if target_path and not target_path.endswith("unmatched") else "manual",
            "tags": {
            "shot": shot,
            "task": task,
            "version": version,
                "resolution": resolution,
                "asset": asset,
            "stage": stage
            },
            "sequence_info": {
                "base_name": base_name,
                "suffix": suffix,
                "files": files_list,
                "frame_numbers": frame_numbers,
                "frame_range": frame_range,
                "frame_count": frame_count,
                "directory": directory
            },
            "matched_rules": [],
            "used_default_footage_rule": False,
            "ambiguous_match": False,
            "ambiguous_options": []
        }

        print(f"[OPTIMIZED] Created sequence proposal: {sequence_pattern} -> {target_path}", file=sys.stderr)
        return sequence_proposal

    except Exception as e:
        print(f"[ERROR] Error in optimized create_sequence_mapping: {e}", file=sys.stderr)
        return {
            "source": "unknown",
            "destination": "unknown",
            "reason": f"Error processing sequence: {e}"
        }
