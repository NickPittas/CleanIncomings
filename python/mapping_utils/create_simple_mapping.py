import os
import uuid
from typing import Dict, Any # For type hinting
from .generate_simple_target_path import generate_simple_target_path

def create_simple_mapping(
    node: Dict[str, Any], 
    profile_rules: list, # This is the list of rule objects from the profile
    root_output_dir: str, # The user-selected root output directory
    extract_shot_simple=None,
    extract_task_simple=None,
    extract_version_simple=None,
    extract_resolution_simple=None,
    extract_asset_simple=None,
    extract_stage_simple=None,
    p_shot: list = None,
    p_task: dict = None,
    p_version: list = None,
    p_resolution: list = None,
    p_asset: list = None,
    p_stage: list = None
) -> Dict[str, Any]:
    filename = node.get("name", "")
    source_path = node.get("path", "")

    # Perform extraction using passed-in functions and patterns
    # IMPORTANT: Only search filename, never path (source_path is kept for compatibility if an extractor needs it, but it should be empty string for now)
    shot = extract_shot_simple(filename, "", p_shot) if extract_shot_simple and p_shot else node.get("shot")
    task = extract_task_simple(filename, "", p_task) if extract_task_simple and p_task else node.get("task")
    version = extract_version_simple(filename, p_version) if extract_version_simple and p_version else node.get("version")
    resolution = extract_resolution_simple(filename, "", p_resolution) if extract_resolution_simple and p_resolution else node.get("resolution")
    asset = extract_asset_simple(filename, p_asset) if extract_asset_simple and p_asset else node.get("asset")
    stage = extract_stage_simple(filename, p_stage) if extract_stage_simple and p_stage else node.get("stage")

    # Call the updated generate_simple_target_path
    path_generation_result = generate_simple_target_path(
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

    target_path = path_generation_result["target_path"] # This can be None if ambiguous
    used_default_footage_rule = path_generation_result["used_default_footage_rule"]
    ambiguous_match = path_generation_result["ambiguous_match"]
    ambiguous_options = path_generation_result["ambiguous_options"]

    status = "auto" if shot and task and version and not used_default_footage_rule and not ambiguous_match else "manual"
    validated_node = {
        "name": node.get("name", "unknown_file"),
        "path": node.get("path", ""),
        "type": node.get("type", "file"),
        "size": node.get("size", 0),
        "extension": node.get("extension", ""),
    }
    return {
        "id": str(uuid.uuid4()),
        "name": filename,
        "sourcePath": source_path,
        "targetPath": target_path,
        "status": status,
        "shot": shot,
        "asset": asset,
        "stage": stage,
        "task": task,
        "version": version,
        "resolution": resolution,
        "node": validated_node,
        "used_default_footage_rule": used_default_footage_rule,
        "ambiguous_match": ambiguous_match,
        "ambiguous_options": ambiguous_options
    }
