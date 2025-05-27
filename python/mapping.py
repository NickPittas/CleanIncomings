import os
import sys
import json
import re
import uuid
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple


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

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
                print(f"Loaded patterns config from: {config_path}", file=sys.stderr)
                return config
        except Exception as e:
            print(f"Failed to load config from {config_path}: {e}", file=sys.stderr)
            print("Using fallback patterns", file=sys.stderr)
            return {
                "shotPatterns": ["DEMO\\d{4}", "FULL\\d{4}", "ANOT\\d{4}", "\\d{3,4}"],
                "taskPatterns": {
                    "comp": ["comp", "composite"],
                    "vfx": ["vfx", "effects"],
                    "footage": ["footage", "plates"],
                },
                "resolutionPatterns": ["2k", "4k", "hd", "proxy"],
                "versionPatterns": ["v\\d{3}", "_v\\d{2,3}"],
                "projectTypes": {
                    "sphere": {"vfxFolder": "04_vfx", "compFolder": "05_comp"},
                    "internal": {"footageFolder": "footage", "3dFolder": "3d"},
                },
            }

    def _extract_shot_simple(self, filename: str, path: str) -> Optional[str]:
        print(f"  Extracting shot from filename: {filename}", file=sys.stderr)
        for pattern in self.shot_patterns:
            match = pattern.search(filename)
            if match:
                print(f"    Found shot: {match.group(0)}", file=sys.stderr)
                return match.group(0)
        print(f"    No shot found, returning 'unmatched'", file=sys.stderr)
        return "unmatched"

    def _extract_task_simple(self, filename: str, path: str) -> Optional[str]:
        print(f"  Extracting task from filename: {filename}", file=sys.stderr)
        print(f"  Task patterns: {self.task_patterns}", file=sys.stderr)
        for canonical, patterns in self.task_patterns.items():
            for pattern in patterns:
                if re.search(
                    rf"(?<![a-zA-Z0-9]){re.escape(pattern)}(?![a-zA-Z0-9])",
                    filename,
                    re.IGNORECASE,
                ):
                    print(
                        f"    Found task: {canonical} (matched alias: {pattern})",
                        file=sys.stderr,
                    )
                    return canonical
        print(f"    No task found, returning 'unmatched'", file=sys.stderr)
        return "unmatched"

    def _extract_version_simple(self, filename: str) -> Optional[str]:
        # Use a broad regex for v1, v01, v001, v0001, etc.
        pattern = re.compile(r"[_\.]?v\d{1,6}", re.IGNORECASE)
        matches = [m.group(0).lstrip("_.") for m in pattern.finditer(filename)]
        if matches:
            print(
                f"    Found version(s): {matches}, using last: {matches[-1]}",
                file=sys.stderr,
            )
            return matches[-1]
        else:
            print(f"    No version found, returning 'unmatched'", file=sys.stderr)
            return "unmatched"

    def _extract_resolution_simple(self, filename: str, path: str) -> Optional[str]:
        for resolution in self.resolution_patterns:
            if re.search(re.escape(resolution), filename, re.IGNORECASE):
                print(f"    Found resolution: {resolution}", file=sys.stderr)
                return resolution
        print(f"    No resolution found, returning 'unmatched'", file=sys.stderr)
        return "unmatched"

    def _extract_asset_simple(self, filename: str) -> Optional[str]:
        asset_patterns = self.config.get("assetPatterns", [])
        for asset in asset_patterns:
            if re.search(
                rf"(?<![a-zA-Z0-9]){re.escape(asset)}(?![a-zA-Z0-9])",
                filename,
                re.IGNORECASE,
            ):
                print(f"    Found asset: {asset}", file=sys.stderr)
                return asset
        print(f"    No asset found, returning 'unmatched'", file=sys.stderr)
        return "unmatched"

    def _extract_stage_simple(self, filename: str) -> Optional[str]:
        stage_patterns = self.config.get("stagePatterns", [])
        for stage in stage_patterns:
            if re.search(
                rf"(?<![a-zA-Z0-9]){re.escape(stage)}(?![a-zA-Z0-9])",
                filename,
                re.IGNORECASE,
            ):
                print(f"    Found stage: {stage}", file=sys.stderr)
                return stage
        print(f"    No stage found, returning 'unmatched'", file=sys.stderr)
        return "unmatched"

    def generate_mappings(
        self, tree: Dict[str, Any], profile: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        print(f"=== SIMPLIFIED MAPPING GENERATION ===", file=sys.stderr)
        print(f"Profile: {profile.get('name', 'Unknown')}", file=sys.stderr)
        print(
            f"VFX Root: {profile.get('vfxRootPath', '/vfx/projects/default')}",
            file=sys.stderr,
        )
        print(
            f"Tree: {tree.get('name', 'Unknown')} (type: {tree.get('type', 'unknown')})",
            file=sys.stderr,
        )
        children = tree.get("children", [])
        print(f"Processing {len(children)} items", file=sys.stderr)
        all_files = []

        # Check if tree has _all_files (folders-only mode with file list)
        if "_all_files" in tree and tree["_all_files"]:
            print(f"Using _all_files list from folders-only tree", file=sys.stderr)
            # Convert file paths to file nodes
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
            # Traditional tree traversal for trees with file nodes
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
        sequences, single_files = self._group_image_sequences(all_files)
        print(
            f"Found {len(sequences)} image sequences and {len(single_files)} single files",
            file=sys.stderr,
        )
        mappings = []
        for sequence in sequences:
            mapping = self._create_sequence_mapping(sequence, profile)
            mappings.append(mapping)
        for file_node in single_files:
            mapping = self._create_simple_mapping(file_node, profile)
            mappings.append(mapping)
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

    def _group_image_sequences(self, files: List[Dict[str, Any]]):
        sequence_extensions = {
            ".exr",
            ".dpx",
            ".tiff",
            ".tif",
            ".jpg",
            ".jpeg",
            ".png",
            ".hdr",
        }
        file_groups = {}
        single_files = []

        print(
            f"[DEBUG] Starting sequence grouping with {len(files)} files",
            file=sys.stderr,
        )

        for file_node in files:
            filename = file_node.get("name", "")
            filepath = file_node.get("path", "")
            extension = file_node.get("extension", "").lower()

            print(
                f"[DEBUG] Processing file: {filename} (ext: {extension})",
                file=sys.stderr,
            )

            if extension not in sequence_extensions:
                print(
                    f"[DEBUG] Not a sequence extension, adding to single files: {filename}",
                    file=sys.stderr,
                )
                single_files.append(file_node)
                continue

            directory = str(Path(filepath).parent)
            sequence_info = self._extract_sequence_info(filename)

            if sequence_info:
                base_name = sequence_info["base_name"]
                frame_number = sequence_info["frame_number"]
                suffix = sequence_info["suffix"]
                group_key = f"{directory}|{base_name}|{suffix}|{extension}"

                print(f"[DEBUG] Sequence info extracted:", file=sys.stderr)
                print(f"  File: {filename}", file=sys.stderr)
                print(f"  Directory: {directory}", file=sys.stderr)
                print(f"  Base name: {base_name}", file=sys.stderr)
                print(f"  Frame number: {frame_number}", file=sys.stderr)
                print(f"  Suffix: {suffix}", file=sys.stderr)
                print(f"  Group key: {group_key}", file=sys.stderr)

                if group_key not in file_groups:
                    file_groups[group_key] = {
                        "directory": directory,
                        "base_name": base_name,
                        "suffix": suffix,
                        "extension": extension,
                        "files": [],
                        "frame_numbers": [],
                    }
                    print(f"[DEBUG] Created new group: {group_key}", file=sys.stderr)
                else:
                    print(
                        f"[DEBUG] Adding to existing group: {group_key}",
                        file=sys.stderr,
                    )

                file_groups[group_key]["files"].append(file_node)
                file_groups[group_key]["frame_numbers"].append(frame_number)
            else:
                print(
                    f"[DEBUG] No sequence info extracted, adding to single files: {filename}",
                    file=sys.stderr,
                )
                single_files.append(file_node)

        print(f"[DEBUG] Found {len(file_groups)} file groups", file=sys.stderr)
        for group_key, group_data in file_groups.items():
            print(
                f"[DEBUG] Group {group_key}: {len(group_data['files'])} files, frames {group_data['frame_numbers']}",
                file=sys.stderr,
            )

        sequences = []
        for group_key, group_data in file_groups.items():
            if len(group_data["files"]) > 1:
                sorted_files = sorted(
                    zip(group_data["files"], group_data["frame_numbers"]),
                    key=lambda x: x[1],
                )
                sequence = {
                    "type": "sequence",
                    "base_name": group_data["base_name"],
                    "suffix": group_data["suffix"],
                    "extension": group_data["extension"],
                    "directory": group_data["directory"],
                    "files": [f[0] for f in sorted_files],
                    "frame_numbers": [f[1] for f in sorted_files],
                    "frame_range": f"{min(group_data['frame_numbers'])}-{max(group_data['frame_numbers'])}",
                    "frame_count": len(group_data["files"]),
                }
                sequences.append(sequence)
                print(
                    f"  Sequence: {group_data['base_name']}{group_data['suffix']}{group_data['extension']} "
                    f"[{sequence['frame_range']}] ({sequence['frame_count']} frames)",
                    file=sys.stderr,
                )
            else:
                print(
                    f"[DEBUG] Group {group_key} has only 1 file, treating as single file",
                    file=sys.stderr,
                )
                single_files.extend(group_data["files"])

        print(
            f"[DEBUG] Final result: {len(sequences)} sequences, {len(single_files)} single files",
            file=sys.stderr,
        )
        return sequences, single_files

    def _extract_sequence_info(self, filename: str) -> Optional[Dict[str, Any]]:
        patterns = [
            r"^(.+)[._](\d{3,6})(\..+)$",
            r"^(.+[._]v\d{2,3})[._](\d{3,6})(\..+)$",
            r"^(.+)_(\d{3,6})(_[^.]*)?(\..+)$",
        ]
        for pattern in patterns:
            match = re.match(pattern, filename, re.IGNORECASE)
            if match:
                if len(match.groups()) == 3:
                    base_name, frame_str, suffix = match.groups()
                    return {
                        "base_name": base_name,
                        "frame_number": int(frame_str),
                        "suffix": suffix,
                    }
                elif len(match.groups()) == 4:
                    base_name, frame_str, extra_suffix, extension = match.groups()
                    suffix = (extra_suffix or "") + extension
                    return {
                        "base_name": base_name,
                        "frame_number": int(frame_str),
                        "suffix": suffix,
                    }
        return None

    def _create_sequence_mapping(
        self, sequence: Dict[str, Any], profile: Dict[str, Any]
    ) -> Dict[str, Any]:
        first_file = sequence["files"][0]
        first_filename = first_file.get("name", "")
        print(f"[DEBUG] Sequence mapping for: {first_filename}", file=sys.stderr)
        first_filepath = first_file.get("path", "")
        shot = self._extract_shot_simple(first_filename, first_filepath)
        task = self._extract_task_simple(first_filename, first_filepath)
        print(f"[DEBUG] Extracted task: {task}", file=sys.stderr)
        version = self._extract_version_simple(first_filename)
        resolution = self._extract_resolution_simple(first_filename, first_filepath)
        asset = self._extract_asset_simple(first_filename)
        stage = self._extract_stage_simple(first_filename)
        print(f"[DEBUG] Sequence: {first_filename}", file=sys.stderr)
        print(f"  Extracted asset: {asset}", file=sys.stderr)
        print(f"  Extracted stage: {stage}", file=sys.stderr)
        print(f"  Extracted task: {task}", file=sys.stderr)
        base_name = sequence["base_name"]
        suffix = sequence["suffix"]
        frame_range = sequence["frame_range"]
        frame_count = sequence["frame_count"]
        ext = sequence.get("extension", "")
        if suffix.endswith(ext):
            sequence_filename = (
                f"{base_name}.####{suffix}"
                if "." in suffix
                else f"{base_name}_####{suffix}"
            )
        else:
            sequence_filename = (
                f"{base_name}.####{suffix}{ext}"
                if "." in suffix
                else f"{base_name}_####{suffix}{ext}"
            )
        import os

        if "." in suffix:
            sequence_pattern = f"{base_name}.####{suffix}"
        else:
            sequence_pattern = f"{base_name}_####{suffix}"
        source_pattern = os.path.join(sequence["directory"], sequence_pattern)
        vfx_root = profile.get("vfxRootPath", "/vfx/projects/default")
        target_path = self._generate_simple_target_path(
            vfx_root,
            shot,
            asset,
            stage,
            task,
            version,
            resolution,
            sequence_filename,
            profile,
        )
        print(f"  Target path: {target_path}", file=sys.stderr)
        if shot and task and version:
            status = "auto"
        else:
            status = "manual"
        total_size = 0
        validated_files = []
        for file_node in sequence["files"]:
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
        seq_dict = {
            "base_name": base_name,
            "frame_range": frame_range,
            "frame_count": frame_count,
            "total_size": total_size,
            "files": validated_files,
            "frame_numbers": sequence.get("frame_numbers", []),
        }
        if sequence.get("frame_numbers"):
            seq_dict["start"] = min(sequence["frame_numbers"])
            seq_dict["end"] = max(sequence["frame_numbers"])
        return {
            "id": str(uuid.uuid4()),
            "name": sequence_filename,
            "type": "sequence",
            "sourcePath": source_pattern,
            "targetPath": target_path,
            "status": status,
            "shot": shot,
            "asset": asset,
            "stage": stage,
            "task": task,
            "version": version,
            "resolution": resolution,
            "node": {
                "name": sequence_filename,
                "path": source_pattern,
                "type": "sequence",
                "size": total_size,
                "extension": sequence.get("extension", ""),
                "children": [],
            },
            "sequence": seq_dict,
            "displayName": f"{base_name} [{frame_range}] ({frame_count} frames)",
        }

    def _create_simple_mapping(
        self, node: Dict[str, Any], profile: Dict[str, Any]
    ) -> Dict[str, Any]:
        filename = node.get("name", "")
        print(f"[DEBUG] Simple mapping for: {filename}", file=sys.stderr)
        source_path = node.get("path", "")
        shot = self._extract_shot_simple(filename, source_path)
        task = self._extract_task_simple(filename, source_path)
        print(f"[DEBUG] Extracted task: {task}", file=sys.stderr)
        version = self._extract_version_simple(filename)
        resolution = self._extract_resolution_simple(filename, source_path)
        asset = self._extract_asset_simple(filename)
        stage = self._extract_stage_simple(filename)
        print(f"[DEBUG] File: {filename}", file=sys.stderr)
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
