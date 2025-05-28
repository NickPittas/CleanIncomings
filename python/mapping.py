import os
import sys
import re
import uuid
from typing import Dict, List, Any, Optional
import time
from pathlib import Path

# Import the progress monitoring system
try:
    from progress_server import (
        check_server_health
    )
    WEBSOCKET_AVAILABLE = True

    # Check if server is running
    def is_server_running():
        """Check if server is running"""
        health = check_server_health()
        return health.get('running', False)

except ImportError:
    WEBSOCKET_AVAILABLE = False
    print("[WARNING] WebSocket progress server not available", file=sys.stderr)


class MappingGenerator:
    """Generates file mappings based on configurable VFX patterns."""

    def __init__(self, config_path: str = None):
        if config_path is None:
            script_dir = Path(__file__).parent.parent
            config_path = script_dir / "src" / "config" / "patterns.json"
        self.config = self._load_config(config_path)
        self.shot_patterns = [
            re.compile(pattern, re.IGNORECASE)
            for pattern in self.config.get("shotPatterns", [])
        ]
        self.task_patterns = self.config.get("taskPatterns", {})
        self.resolution_patterns = self.config.get("resolutionPatterns", [])
        self.version_patterns = [
            re.compile(pattern, re.IGNORECASE)
            for pattern in self.config.get("versionPatterns", [])
        ]
        self.project_types = self.config.get("projectTypes", {})
        self.max_depth = 10
        self.current_frame_numbers = []  # Initialize frame numbers storage

    # Import utility functions from mapping_utils
    from mapping_utils.config_loader import load_config
    from mapping_utils.shot_extractor import extract_shot_simple
    from mapping_utils.task_extractor import extract_task_simple
    from mapping_utils.version_extractor import extract_version_simple
    from mapping_utils.resolution_extractor import extract_resolution_simple
    from mapping_utils.asset_extractor import extract_asset_simple
    from mapping_utils.stage_extractor import extract_stage_simple
    from mapping_utils.progress import update_mapping_progress

    # Remove the old method definitions above. Use the imported functions in the
    # MappingGenerator methods as follows:
    # Example usage in __init__ and other methods:
    # self.config = load_config(config_path)
    # shot = self.extract_shot_simple(filename, path, self.shot_patterns)
    # task = self.extract_task_simple(filename, path, self.task_patterns)
    # version = self.extract_version_simple(filename, self.version_patterns)
    # resolution = self.extract_resolution_simple(
    #     filename, path, self.resolution_patterns)
    # asset = self.extract_asset_simple(
    #     filename, self.config.get("assetPatterns", []))
    # stage = self.extract_stage_simple(
    #     filename, self.config.get("stagePatterns", []))
    # self.update_mapping_progress(
    #     batch_id, current, total, status, current_file)

    def generate_mappings(
        self, tree: Dict[str, Any], profile: Dict[str, Any], batch_id=None, websocket_available=None
    ) -> List[Dict[str, Any]]:
        from mapping_utils.generate_mappings import generate_mappings
        from mapping_utils.progress import update_mapping_progress
        from mapping_utils.group_image_sequences import group_image_sequences
        # Import or pass other dependencies as needed
        return generate_mappings(
            tree=tree,
            profile=profile,
            batch_id=batch_id,
            websocket_available=websocket_available,
            update_mapping_progress=update_mapping_progress,
            group_image_sequences=group_image_sequences,
            extract_sequence_info=self._extract_sequence_info,
            is_network_path=self._is_network_path,
            create_sequence_mapping=self._create_sequence_mapping,
            create_simple_mapping=self._create_simple_mapping,
            finalize_sequences=self._finalize_sequences,
        )

    def _init_patterns_from_profile(self, profile: Dict[str, Any]):
        print(
            f"Initializing patterns from profile: {profile.get('name', 'Unknown')}",
            file=sys.stderr,
        )
        user_patterns = profile.get("userPatterns", {})
        shot_names = user_patterns.get("shotNames", [])
        if shot_names:
            shot_patterns = []
            for shot_name in shot_names:
                escaped = re.escape(shot_name)
                shot_patterns.append(escaped)
            shot_patterns.extend(self.config.get("shotPatterns", []))
            self.shot_patterns = [
                re.compile(pattern, re.IGNORECASE) for pattern in shot_patterns
            ]
            print(
                f"Updated shot patterns: {[p.pattern for p in self.shot_patterns]}",
                file=sys.stderr,
            )
        profile_tasks = user_patterns.get("tasks", [])
        if profile_tasks:
            merged_tasks = dict(self.task_patterns)
            for task_info in profile_tasks:
                task_name = task_info.get("name", "")
                aliases = task_info.get("aliases", [])
                if task_name and aliases:
                    merged_tasks[task_name] = aliases
            self.task_patterns = merged_tasks
            print(
                f"Updated task patterns: {list(self.task_patterns.keys())}",
                file=sys.stderr,
            )
        profile_resolutions = user_patterns.get("resolutions", [])
        if profile_resolutions:
            merged_resolutions = list(self.config.get("resolutionPatterns", []))
            for res in profile_resolutions:
                if res not in merged_resolutions:
                    merged_resolutions.append(res)
            self.resolution_patterns = merged_resolutions
            print(
                f"Updated resolution patterns: {self.resolution_patterns}",
                file=sys.stderr,
            )

    def _is_network_path(self, path: str) -> bool:
        """Check if a path is on a network drive"""
        network_prefixes = ('\\\\', '//', 'N:', 'Z:', 'V:')  # Common network drive prefixes
        return any(path.startswith(prefix) for prefix in network_prefixes)
      
    def _finalize_sequences(self, file_groups, files, single_files, batch_id):
        """Finalize the sequences from grouped files, with timeout protection"""
        sequences = []
        progress_interval = 100
        progress_update_interval = 1.0  # 1 second between updates
        last_progress_time = time.time()
      
        # Report initial status
        print(f"[INFO] Finalizing {len(file_groups)} sequence groups", file=sys.stderr)
        if batch_id:
            self.update_mapping_progress(batch_id, 0, len(file_groups), status="finalizing_sequences")
          
        # Process sequences in batches to avoid memory issues
        for i, (seq_key, group_data) in enumerate(file_groups.items()):
            try:
                # Update progress periodically
                current_time = time.time()
                if i % progress_interval == 0 or (current_time - last_progress_time > progress_update_interval):
                    if batch_id:
                        self.update_mapping_progress(
                            batch_id, i, len(file_groups), 
                            status="finalizing_sequences", 
                            current_file=f"Processing group {i+1}/{len(file_groups)}"
                        )
                    if i % (progress_interval * 10) == 0 or i == 0:
                        print(f"[PROGRESS] Sequence finalization: {i+1}/{len(file_groups)} groups", file=sys.stderr)
                    last_progress_time = current_time
              
                # Skip empty groups
                if not group_data.get("files") or len(group_data["files"]) == 0:
                    continue
                  
                # Sequences need at least 2 frames
                if len(group_data["files"]) > 1:
                    # If frames are available, sort by frame number
                    if "frames" in group_data and len(group_data["frames"]) > 0:
                        frames = group_data["frames"]
                        files = group_data["files"]
                      
                        # Create sorted frames and files
                        # Make sure we have valid frame numbers
                        if not all(isinstance(frame, int) for frame in frames):
                            print(f"[WARNING] Invalid frame numbers in sequence, skipping group", file=sys.stderr)
                            single_files.extend(files)
                            continue
                          
                        frame_file_pairs = sorted(zip(frames, files), key=lambda x: x[0])
                        sorted_frames = [pair[0] for pair in frame_file_pairs]
                        sorted_files = [pair[1] for pair in frame_file_pairs]
                      
                        sequence = {
                            "type": "sequence",
                            "base_name": group_data["base_name"],
                            "suffix": group_data["suffix"],
                            "extension": group_data.get("extension", group_data["suffix"]),
                            "directory": group_data["directory"],
                            "files": sorted_files,
                            "frame_numbers": sorted_frames,
                            "frame_range": f"{min(sorted_frames)}-{max(sorted_frames)}",
                            "frame_count": len(sorted_files),
                            "size": group_data.get("size", 0),
                        }
                      
                        sequences.append(sequence)
                      
                        # Log only occasionally for large sets
                        if len(sequences) % 10 == 0 or len(sequences) < 10:
                            print(
                                f"  Sequence: {group_data['base_name']}.{group_data['suffix']} "
                                f"[{sequence['frame_range']}] ({sequence['frame_count']} frames)",
                                file=sys.stderr,
                            )
                    else:
                        # If frames aren't available, just process as single files
                        single_files.extend(group_data["files"])
                else:
                    # Groups with only one file go to single files
                    if len(group_data["files"]) == 1:
                        single_files.append(group_data["files"][0])
            except Exception as e:
                # If any error happens during finalization, add all files to singles as fallback
                # print(f"[ERROR] Error finalizing sequence group {seq_key}: {e}", file=sys.stderr)
                if "files" in group_data and group_data["files"]:
                    single_files.extend(group_data["files"])
      
        # Final progress update
        if batch_id:
            self.update_mapping_progress(batch_id, len(file_groups), len(file_groups), status="sequences_grouped")

        print(
            f"[INFO] Final result: {len(sequences)} sequences, {len(single_files)} single files",
            file=sys.stderr,
        )
        return sequences, single_files


    from mapping_utils.extract_sequence_info import extract_sequence_info

    def _process_sequence_mapping(self, first_file, base_name, ext, suffix, directory, first_filepath, profile, shot, asset, stage, task, version, resolution, files_list):
        # Validate required inputs
        if not first_file or not profile:
            return {
                "source": "unknown",
                "destination": "unknown",
                "reason": "Missing required sequence mapping input."
            }
        # Extract filename and filepath
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
        vfx_root = profile.get("vfxRootPath", "/vfx/projects/default")
        target_path = self._generate_simple_target_path(
            vfx_root, shot, asset, stage, task, version, resolution, sequence_filename, profile
        )

        # Determine mapping status
        if shot and task and version:
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
        elif hasattr(self, 'current_frame_numbers'):
            frame_numbers_list = self.current_frame_numbers

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

        # Final mapping structure
        mapping = {
            "source": source_pattern,
            "destination": target_path,
            "status": status,
            "sequence": seq_dict,
        }
        return mapping

    def _create_simple_mapping(
        self, node: Dict[str, Any], profile: Dict[str, Any]
    ) -> Dict[str, Any]:
        filename = node.get("name", "")
        # print(f"[DEBUG] Simple mapping for: {filename}", file=sys.stderr)
        source_path = node.get("path", "")
        shot = self.extract_shot_simple(filename, source_path)
        task = self.extract_task_simple(filename, source_path)
        # print(f"[DEBUG] Extracted task: {task}", file=sys.stderr)
        version = self.extract_version_simple(filename)
        resolution = self.extract_resolution_simple(filename, source_path)
        asset = self.extract_asset_simple(filename)
        stage = self.extract_stage_simple(filename)
        # print(f"[DEBUG] File: {filename}", file=sys.stderr)
        print(f"  Extracted asset: {asset}", file=sys.stderr)
        print(f"  Extracted stage: {stage}", file=sys.stderr)
        print(f"  Extracted task: {task}", file=sys.stderr)
        vfx_root = profile.get("vfxRootPath", "/vfx/projects/default")
        target_path = self._generate_simple_target_path(
            vfx_root, shot, asset, stage, task, version, resolution, filename, profile
        )
        print(f"  Target path: {target_path}", file=sys.stderr)
        if shot and task and version:
            status = "auto"
        else:
            status = "manual"
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
        }

    def _generate_simple_target_path(
        self,
        vfx_root: str,
        shot: Optional[str],
        asset: Optional[str],
        stage: Optional[str],
        task: Optional[str],
        version: Optional[str],
        resolution: Optional[str],
        filename: str,
        profile: Dict[str, Any],
    ) -> str:
        import os

        profile_name = profile.get("name", "").lower()
        config_types = self.config.get("projectTypes", {})
        is_sphere = "sphere" in profile_name
        vfx_folder = config_types.get("sphere", {}).get("vfxFolder", "04_vfx")
        normal_3d_folder = "3D"
        vfx_parts = []
        if is_sphere:
            vfx_parts.append(vfx_folder)
        else:
            vfx_parts.append(normal_3d_folder)
        vfx_parts.append(shot if shot else "unmapped")
        vfx_parts.append(asset if asset else "unmapped")
        vfx_parts.append(stage if stage else "unmapped")
        vfx_parts.append(task if task else "unmatched")
        vfx_parts.append(version if version else "unmatched")
        vfx_parts.append(resolution if resolution else "unmatched")
        vfx_parts.append(filename)
        vfx_rel_path = os.path.join(*vfx_parts)
        if os.path.isabs(vfx_root):
            target_path = os.path.join(vfx_root, vfx_rel_path)
        else:
            target_path = os.path.join(vfx_root, vfx_rel_path)
        if os.name == "nt":
            target_path = target_path.replace("/", "\\")
        return target_path
