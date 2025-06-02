"""
Optimized Create Simple Mapping

Creates mapping proposals for individual files using cached pattern extraction
for improved performance.
"""

import os
import sys
import uuid
from typing import Dict, Any, List
from .pattern_cache import extract_all_patterns_cached


def create_simple_mapping(
    node: Dict[str, Any], 
    profile_rules: List[Dict[str, List[str]]],
    root_output_dir: str,
    extract_shot_simple=None,
    extract_task_simple=None,
    extract_version_simple=None,
    extract_resolution_simple=None,
    extract_asset_simple=None,
    extract_stage_simple=None,
    p_shot: List[str] = None,
    p_task: Dict[str, List[str]] = None,
    p_version: List[str] = None,
    p_resolution: List[str] = None,
    p_asset: List[str] = None,
    p_stage: List[str] = None
):
    """
    Creates a mapping proposal for an individual file using optimized pattern caching.
    
    Key optimization: All pattern extraction is done in a single cached call
    instead of multiple individual extract_*_simple calls.
    """
    from .generate_simple_target_path import generate_simple_target_path

    try:
        filename = node.get("name", "")
        if not filename:
            return {
                "id": str(uuid.uuid4()),
                "status": "error",
                "error_message": "Missing filename in node"
            }

        # print(f"[OPTIMIZED] Processing individual file: '{filename}'", file=sys.stderr)  # (Silenced for normal use. Re-enable for troubleshooting.)

        # OPTIMIZATION: Extract all patterns at once using cached extraction
        # This single call replaces multiple individual extract_*_simple calls
        if (p_shot is not None and p_task is not None and p_version is not None and 
            p_resolution is not None and p_asset is not None and p_stage is not None):
            
            pattern_results = extract_all_patterns_cached(
                filename,
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
            
            # print(f"[OPTIMIZED] Cached extraction results for '{filename}': shot={shot}, task={task}, version={version}, resolution={resolution}, asset={asset}, stage={stage}", file=sys.stderr)  # (Silenced for normal use. Re-enable for troubleshooting.)
        else:
            # Fallback to individual extraction functions if patterns not provided
            print(f"[FALLBACK] Using individual extraction functions for '{filename}'", file=sys.stderr)
            shot = extract_shot_simple(filename, "", p_shot or []) if extract_shot_simple else None
            task = extract_task_simple(filename, "", p_task or {}) if extract_task_simple else None
            version = extract_version_simple(filename, p_version or []) if extract_version_simple else None
            resolution = extract_resolution_simple(filename, "", p_resolution or []) if extract_resolution_simple else None
            asset = extract_asset_simple(filename, p_asset or []) if extract_asset_simple else None
            stage = extract_stage_simple(filename, p_stage or []) if extract_stage_simple else None

        # Generate the target path using the extracted values
        target_path_result = generate_simple_target_path(
            root_output_dir=root_output_dir,
            profile_rules=profile_rules,
            filename=filename,
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
            target_path = os.path.join(root_output_dir, "unmatched", filename)

        # Create the file proposal
        file_proposal = {
            "id": str(uuid.uuid4()),
            "original_item": {
                "name": filename,
                "path": node.get("path", ""),
                "type": "file",
                "size": node.get("size", 0),
                "extension": node.get("extension", "")
            },
            "targetPath": target_path,
            "type": "file",
            "status": "auto" if target_path and not target_path.endswith("unmatched") else "manual",
            "tags": {
                "shot": shot,
                "task": task,
                "version": version,
                "resolution": resolution,
                "asset": asset,
                "stage": stage
            },
            "matched_rules": [],
            "used_default_footage_rule": False,
            "ambiguous_match": False,
            "ambiguous_options": []
        }

        # print(f"[OPTIMIZED] Created file proposal: {filename} -> {target_path}", file=sys.stderr)  # (Silenced for normal use. Re-enable for troubleshooting.)
        return file_proposal

    except Exception as e:
        print(f"[ERROR] Error in optimized create_simple_mapping for '{node.get('name', 'unknown')}': {e}", file=sys.stderr)
        return {
            "id": str(uuid.uuid4()),
            "original_item": node,
            "status": "error",
            "error_message": f"Error processing file: {e}",
            "targetPath": None,
            "type": "file",
            "tags": {},
            "matched_rules": [],
            "used_default_footage_rule": False,
            "ambiguous_match": False,
            "ambiguous_options": []
        } 