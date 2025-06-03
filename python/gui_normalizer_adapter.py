import json
import os
import sys
import time
import uuid
from pathlib import Path
import threading
import logging  # Added for logging
from typing import List, Dict, Any, Optional, Callable

from .scanner import FileSystemScanner
from .mapping import MappingGenerator

class GuiNormalizerAdapter:
    def __init__(self, config_dir_path: str):
        self.config_dir_path = Path(config_dir_path)
        self.patterns_json_path = self.config_dir_path / "patterns.json"
        self.profiles_json_path = self.config_dir_path / "profiles.json"

        # Initialize logger
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)  # Ensure DEBUG messages are shown
        # Basic configuration for the logger if no other logging is set up
        if not logging.getLogger().hasHandlers():
            logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

        if not self.patterns_json_path.is_file():
            raise FileNotFoundError(f"patterns.json not found at {self.patterns_json_path}")
        if not self.profiles_json_path.is_file():
            raise FileNotFoundError(f"profiles.json not found at {self.profiles_json_path}")

        self.scanner = FileSystemScanner()
        self.mapping_generator = MappingGenerator(config_path=str(self.patterns_json_path))
        
        try:
            with open(self.profiles_json_path, 'r', encoding='utf-8') as f:
                self.all_profiles_data = json.load(f)
        except json.JSONDecodeError as e:
            self.logger.error(f"Error decoding {self.profiles_json_path}: {e}") # Log the error
            raise ValueError(f"Error decoding {self.profiles_json_path}: {e}")
        except Exception as e:
            self.logger.error(f"Could not read {self.profiles_json_path}: {e}") # Log the error
            raise IOError(f"Could not read {self.profiles_json_path}: {e}")

        self.current_profile_name: Optional[str] = None
        self.current_profile_rules: Optional[List[Dict[str, Any]]] = None

    def set_profile(self, profile_name: str) -> bool:
        """
        Sets the active profile for the normalizer and loads its rules.

        Args:
            profile_name: The name of the profile to set.

        Returns:
            True if the profile was successfully set, False otherwise.
        """
        if profile_name not in self.all_profiles_data:
            self.logger.error(f"Profile '{profile_name}' not found. Available: {list(self.all_profiles_data.keys())}")
            self.current_profile_name = None
            self.current_profile_rules = None
            return False

        profile_config_entry = self.all_profiles_data[profile_name]
        actual_rules_list: Optional[List[Dict[str, Any]]] = None

        if isinstance(profile_config_entry, list):
            actual_rules_list = []
            for i, rule_item in enumerate(profile_config_entry):
                if not isinstance(rule_item, dict):
                    self.logger.error(
                        f"Profile '{profile_name}': rule item at index {i} is not a dictionary. "
                        f"Got type: {type(rule_item)} for item: {rule_item}"
                    )
                    self.current_profile_name = None
                    self.current_profile_rules = None
                    return False # Invalid rule structure
                actual_rules_list.append(rule_item)

        elif isinstance(profile_config_entry, dict):
            if "rules" not in profile_config_entry or not isinstance(profile_config_entry["rules"], list):
                self.logger.error(
                    f"Profile '{profile_name}' (type: dict) is missing a 'rules' key, "
                    f"or 'rules' is not a list. Found keys: {list(profile_config_entry.keys())}."
                )
                self.current_profile_name = None
                self.current_profile_rules = None
                return False # Invalid structure
            actual_rules_list = []
            for i, rule_item in enumerate(profile_config_entry["rules"]):
                if not isinstance(rule_item, dict):
                    self.logger.error(
                        f"Profile '{profile_name}': rule item at index {i} within 'rules' list is not a dictionary. "
                        f"Got type: {type(rule_item)} for item: {rule_item}"
                    )
                    self.current_profile_name = None
                    self.current_profile_rules = None
                    return False # Invalid rule structure
                actual_rules_list.append(rule_item)
        else:
            self.logger.error(
                f"Entry for profile '{profile_name}' in profiles.json must be a list of rule dictionaries "
                f"or a dictionary containing a 'rules' key with such a list. "
                f"Got type: {type(profile_config_entry)}"
            )
            self.current_profile_name = None
            self.current_profile_rules = None
            return False # Invalid profile type
        
        if actual_rules_list is None:
            self.logger.error(f"Could not determine a valid rules list for profile '{profile_name}'. Check profiles.json structure.")
            self.current_profile_name = None
            self.current_profile_rules = None
            return False

        self.current_profile_name = profile_name
        self.current_profile_rules = actual_rules_list
        # self.logger.info(  # (Silenced for normal use. Re-enable for troubleshooting.)f"Successfully set active profile to: '{profile_name}' with {len(self.current_profile_rules)} rule sets.")
        return True

    def get_profile_names(self) -> List[str]:
        """Returns a list of available profile names."""
        return list(self.all_profiles_data.keys())

    def scan_and_normalize_structure(
        self,
        base_path: str,
        profile_name: str,
        destination_root: str,
        status_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
        poll_interval: float = 0.5  # seconds
    ) -> List[Dict[str, Any]]:
        """
        Scans a directory, generates normalization proposals based on the selected profile,
        and returns a flat list of file/sequence information dictionaries suitable for the GUI.
        """
        if not self.current_profile_name or not self.current_profile_rules:
            # Try to set the profile if it hasn't been or if it matches the requested one
            if profile_name:
                # self.logger.info(  # (Silenced for normal use. Re-enable for troubleshooting.)f"Current profile not set or rules not loaded. Attempting to set to '{profile_name}'.")
                if not self.set_profile(profile_name):
                    error_msg = f"Failed to set profile '{profile_name}' before scanning. Check profile configuration."
                    self.logger.error(error_msg)
                    if status_callback:
                        status_callback({"type": "scan", "data": {"status": "failed", "error": error_msg, "progress": 0, "total_items": 0}})
                    # Return structure expected by ScanManager on error
                    return {
                        "original_scan_tree": {"name": "root", "type": "directory", "path": base_path, "children": []}, 
                        "proposals": []
                    }
            else:
                error_msg = "No profile name provided for scanning, and no profile is currently active."
                self.logger.error(error_msg)
                if status_callback:
                    status_callback({"type": "scan", "data": {"status": "failed", "error": error_msg, "progress": 0, "total_items": 0}})
                return {
                    "original_scan_tree": {"name": "root", "type": "directory", "path": base_path, "children": []}, 
                    "proposals": []
                }
        elif self.current_profile_name != profile_name:
            self.logger.warning(f"Requested profile '{profile_name}' differs from current active profile '{self.current_profile_name}'. Attempting to switch.")
            if not self.set_profile(profile_name):
                error_msg = f"Failed to switch to profile '{profile_name}' before scanning. Check profile configuration."
                self.logger.error(error_msg)
                if status_callback:
                    status_callback({"type": "scan", "data": {"status": "failed", "error": error_msg, "progress": 0, "total_items": 0}})
                return {
                    "original_scan_tree": {"name": "root", "type": "directory", "path": base_path, "children": []}, 
                    "proposals": []
                }

        batch_id = str(uuid.uuid4())

        # --- Threaded Scanning --- 
        scan_thread_completed = threading.Event()
        scan_error = None

        def _do_scan():
            nonlocal scan_error
            try:
                self.scanner.scan_directory_with_progress(base_path, batch_id=batch_id)
            except Exception as e:
                scan_error = e
            finally:
                scan_thread_completed.set()

        scan_thread = threading.Thread(target=_do_scan)
        scan_thread.start()
        # --- End Threaded Scanning ---

        # Poll for scan completion
        while not scan_thread_completed.is_set() or self.scanner.get_scan_progress(batch_id).get("status") not in ["completed", "failed"]:
            scan_progress = self.scanner.get_scan_progress(batch_id)
            if status_callback:
                status_callback({"type": "scan", "data": scan_progress})
            
            status = scan_progress.get("status")
            if status == "completed":
                break
            elif status == "failed":
                error_info = scan_progress.get("result", {}).get("error", "Unknown scan error")
                # Wait for thread to finish to capture any direct exception from the thread
                scan_thread.join(timeout=poll_interval * 2) 
                if scan_error:
                    raise RuntimeError(f"Scanning thread failed: {scan_error}") from scan_error
                raise RuntimeError(f"Scanning failed as per progress file: {error_info}")
            
            if scan_thread_completed.is_set() and status not in ["completed", "failed"]:
                # If thread finished but status isn't final, check one last time or assume error
                final_progress_check = self.scanner.get_scan_progress(batch_id)
                if final_progress_check.get("status") == "completed":
                    break
                elif final_progress_check.get("status") == "failed":
                    error_info = final_progress_check.get("result", {}).get("error", "Scan thread finished but status indicates failure.")
                    if scan_error:
                         raise RuntimeError(f"Scanning thread failed: {scan_error}") from scan_error
                    raise RuntimeError(f"Scanning failed: {error_info}")
                elif scan_error:
                    raise RuntimeError(f"Scanning thread failed: {scan_error}") from scan_error
                else: # Fallback if thread done but status not updated to completed/failed
                    # Consider logging this specific scenario if it's possible and unexpected
                    raise RuntimeError("Scan thread finished but final status is unclear and no explicit error caught.")

            time.sleep(poll_interval)

        scan_thread.join() # Ensure scan thread is finished before proceeding
        if scan_error:
            raise RuntimeError(f"Scanning thread failed: {scan_error}") from scan_error

        # Re-fetch final progress after thread join, to be absolutely sure
        scan_progress = self.scanner.get_scan_progress(batch_id)
        if scan_progress.get("status") == "failed":
            error_info = scan_progress.get("result", {}).get("error", "Unknown scan error post-join")
            raise RuntimeError(f"Scanning failed: {error_info}")
        if scan_progress.get("status") != "completed":
             raise RuntimeError(f"Scan did not complete successfully. Final status: {scan_progress.get('status', 'unknown')}")

        scan_result = scan_progress.get("result", {})
        original_scan_tree = scan_result.get("tree")
        if not original_scan_tree: # Handles cases where tree is None or an empty dict from scan_result.get('tree')
            self.logger.warning("Scan completed, but the final tree structure is missing or malformed (e.g., None or empty dict from scan result).")
            # Return structure expected by ScanManager on error
            return {
                "original_scan_tree": {"name": "root", "type": "directory", "path": base_path, "children": []}, 
                "proposals": []
            }
        else:
            # Tree exists, now check if it's an empty root and if that's allowed.
            # An empty root is a dict named 'root' with no children (children key missing, None, or empty list).
            is_empty_root = (
                isinstance(original_scan_tree, dict) and
                original_scan_tree.get('name') == 'root' and
                not original_scan_tree.get('children')  # True if 'children' is missing, None, or an empty list
            )

            if is_empty_root and not self.scanner.allows_empty_root_scan_result:
                self.logger.warning("Scan resulted in an empty root, and scanner configuration does not allow this. Treating as no valid tree structure.")
                # Return structure expected by ScanManager on error
                return {
                    "original_scan_tree": {"name": "root", "type": "directory", "path": base_path, "children": []}, 
                    "proposals": []
                }

        profile_object_for_generator = {
            "name": self.current_profile_name, # Use the validated current profile name
            "rules": self.current_profile_rules, # Use the loaded and validated rules
        }

        if status_callback:
            status_callback({'type': 'mapping_generation', 'data': {'status': 'starting', 'message': 'Starting mapping generation...'}})

        proposals = self.mapping_generator.generate_mappings(
            tree=original_scan_tree,
            profile=profile_object_for_generator,
            root_output_dir=destination_root,
            batch_id=batch_id,
            status_callback=status_callback
        )

        if status_callback:
            status_callback({'type': 'mapping_generation', 'data': {'status': 'completed', 'message': 'Mapping generation complete. Transforming results...'}})

        if status_callback:
            status_callback({'type': 'transformation', 'data': {'status': 'starting', 'message': 'Transforming proposals...'}})

        transformed_proposals = []
        if proposals: 
            for p_item in proposals:
                original_item = p_item.get('original_item', {})
                source_path_str = str(original_item.get('path', 'N/A'))
                tags_data = p_item.get('tags', {})
                if not isinstance(tags_data, dict):
                    tags_data = {} 

                matched_tags = {k: v for k, v in tags_data.items() if v is not None and v != ''}
                gui_matched_tags = {k: v for k, v in tags_data.items() if v is not None and v != ''}

                normalized_parts_dict = {
                    'shot': tags_data.get('shot'),
                    'task': tags_data.get('task'),
                    'asset': tags_data.get('asset_name') or tags_data.get('asset') or tags_data.get('asset_type'),
                    'version': tags_data.get('version'),
                    'resolution': tags_data.get('resolution'),
                    'stage': tags_data.get('stage')
                }
                normalized_parts_dict = {k: v for k, v in normalized_parts_dict.items() if v is not None}

                # Determine correct size based on item type
                original_item_type_lower = original_item.get('type', 'file').lower()
                current_item_size = None
                if original_item_type_lower == 'sequence':
                    current_item_size = original_item.get('total_size_bytes')
                    if current_item_size is None:
                        # self.logger.debug(f"Sequence '{original_item.get('name')}' missing 'total_size_bytes', falling back to 'size'.")  # (Silenced for normal use. Re-enable for troubleshooting.)
                        current_item_size = original_item.get('size') 
                else:
                    current_item_size = original_item.get('size')

                # Ensure sequence_info is available for tooltip and other uses
                current_sequence_info = p_item.get('sequence_info')
                if not current_sequence_info and original_item_type_lower == 'sequence':
                    current_sequence_info = original_item

                transformed_item = {
                    'id': p_item.get('id', str(uuid.uuid4())),
                    'source_path': source_path_str,
                    'filename': original_item.get('name', 'N/A'),
                    'new_destination_path': p_item.get('targetPath', ''),
                    'new_name': Path(p_item.get('targetPath', '')).name if p_item.get('targetPath') else original_item.get('name', 'N/A'),
                    'type': original_item.get('type', 'file').capitalize(),
                    'size': current_item_size,
                    'sequence_info': current_sequence_info,
                    'matched_rules': p_item.get('matched_rules', []),
                    'matched_tags': gui_matched_tags,
                    'normalized_parts': normalized_parts_dict,
                    'status': p_item.get('status', 'unknown'),
                    'error_message': p_item.get('error_message') or p_item.get('error')
                }
                transformed_proposals.append(transformed_item)
        else: 
             if status_callback:
                status_callback({'type': 'mapping_generation', 'data': {'status': 'warning', 'message': 'No proposals generated.'}})
        
        if status_callback:
            status_callback({'type': 'transformation', 'data': {'status': 'completed', 'message': 'Proposals transformed.'}})

        return {
            "original_scan_tree": original_scan_tree,
            "proposals": transformed_proposals
        }

    def _format_size_for_display(self, size_bytes: Optional[Any]) -> str:
        """Helper to format size in bytes to a human-readable string."""
        if size_bytes is None or not isinstance(size_bytes, (int, float)):
            return "N/A"
        if size_bytes < 0:
             return "Invalid Size"
        if size_bytes < 1024:
            return str(size_bytes) + " B"
        elif size_bytes < 1024**2:
            return "{:.1f} KB".format(size_bytes/1024)
        elif size_bytes < 1024**3:
            return "{:.1f} MB".format(size_bytes/1024**2)
        else:
            return "{:.1f} GB".format(size_bytes/1024**3)

    def get_item_display_details(self, item_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transforms a normalized item's data into a structure suitable for GUI display,
        including column texts, icon name, and tooltip.

        Args:
            item_data: A dictionary representing a single transformed proposal.
                       This is one of the items from the 'proposals' list which has fields like
                       'filename', 'size' (which should be total_size_bytes for sequences),
                       'type' (e.g., "Sequence", "File"), 'sequence_info', etc.

        Returns:
            A dictionary with 'columns', 'icon_name', and 'tooltip' keys.
        """
        if not item_data:
            self.logger.warning("get_item_display_details called with no item_data.")
            return {
                "columns": {"Filename": "Error: No item data"},
                "icon_name": "error",
                "tooltip": "No data provided to get_item_display_details."
            }

        item_type_capitalized = item_data.get('type', 'File') 
        item_type_lower = item_type_capitalized.lower()

        filename = item_data.get('filename', 'N/A')
        # self.logger.debug(f"ADAPTER_FILENAME_CHECK: item_data has filename='{filename}', type='{item_type_capitalized}'")  # (Silenced for normal use. Re-enable for troubleshooting.)
        
        size_for_display = self._format_size_for_display(item_data.get('size'))

        icon_name = "file_generic" 
        if item_type_lower == 'sequence':
            icon_name = "sequence"
        else: 
            fn_lower = filename.lower()
            if any(fn_lower.endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tif', '.tiff', '.exr', '.dpx', '.tga', '.psd', '.ai']):
                icon_name = "file_image"
            elif any(fn_lower.endswith(ext) for ext in ['.mov', '.mp4', '.avi', '.mkv', '.webm', '.flv', '.wmv', '.r3d']):
                icon_name = "file_video"
            elif any(fn_lower.endswith(ext) for ext in ['.wav', '.mp3', '.aac', '.ogg', '.flac', '.aiff']):
                icon_name = "file_audio"
            elif any(fn_lower.endswith(ext) for ext in ['.zip', '.rar', '.7z', '.tar', '.gz']):
                icon_name = "file_archive" 
            elif any(fn_lower.endswith(ext) for ext in ['.txt', '.md', '.doc', '.docx', '.pdf']):
                icon_name = "file_document"

        status = item_data.get('status', 'unknown')
        error_message = item_data.get('error_message')
        if status == 'error' and error_message:
            icon_name = 'error'

        normalized_parts = item_data.get('normalized_parts', {})
        
        columns = {
            "Filename": filename,
            "Size": size_for_display,
            "Type": item_type_capitalized,
            "Task": normalized_parts.get('task', ''),
            "Asset": normalized_parts.get('asset', ''),
            "Version": normalized_parts.get('version', ''),
            "Resolution": normalized_parts.get('resolution', ''),
            "Destination Path": item_data.get('new_destination_path', '')
        }

        tooltip_parts = []
        tooltip_parts.append("Source: " + item_data.get('source_path', 'N/A'))
        tooltip_parts.append("Proposed Dest: " + item_data.get('new_destination_path', 'N/A'))
        tooltip_parts.append("Status: " + status)

        if error_message:
            tooltip_parts.append("Error: " + error_message)
        
        if item_type_lower == 'sequence':
            seq_info = item_data.get('sequence_info') 
            if seq_info and isinstance(seq_info, dict):
                frame_range_str = seq_info.get('frame_range_str')
                if frame_range_str is None:
                    frame_range_str = str(seq_info.get('name', 'N/A'))
                else:
                    frame_range_str = str(frame_range_str)
                file_count = len(seq_info.get('frames', [])) 
                if 'file_count' in seq_info:
                    file_count = seq_info.get('file_count', 0)
                tooltip_parts.append("Sequence Details: " + frame_range_str + " (" + str(file_count) + " files)")
            else:
                tooltip_parts.append("Sequence Details: N/A (info missing)")

        matched_tags_display = item_data.get('matched_tags', {})
        if matched_tags_display: 
            tags_str_parts = []
            for k,v in matched_tags_display.items():
                if v is not None and v != '': 
                    tags_str_parts.append(str(k) + "=" + str(v))
            if tags_str_parts:
                 tooltip_parts.append("Tags: " + ', '.join(tags_str_parts))

        tooltip = "\\n".join(tooltip_parts)

        return {
            "columns": columns,
            "icon_name": icon_name,
            "tooltip": tooltip
        }

    def get_available_tasks_for_profile(self, profile_name: str) -> List[str]:
        try:
            with open(self.patterns_json_path, 'r', encoding='utf-8') as f:
                patterns_data = json.load(f)
            task_patterns = patterns_data.get('taskPatterns', {})
            if isinstance(task_patterns, dict):
                # Task patterns are expected to be like: {"task_name_for_display": ["keyword1", "keyword2"]}
                # We want to return the keys (task_name_for_display)
                return sorted(list(task_patterns.keys()))
            elif isinstance(task_patterns, list):
                # If list of strings or list of dicts with 'name' or 'pattern', extract those
                if task_patterns and isinstance(task_patterns[0], dict):
                    self.logger.debug("Task patterns are a list of dicts, extracting 'name' or 'pattern' values.")
                    names = []
                    for d in task_patterns:
                        if isinstance(d, dict):
                            if 'name' in d:
                                names.append(d['name'])
                            elif 'pattern' in d:
                                names.append(d['pattern'])
                    return sorted(names)
                else:
                    # List of strings
                    self.logger.debug("Task patterns are a list of strings.")
                    return sorted([str(x) for x in task_patterns])
            else:
                self.logger.warning("Task patterns are neither a dict nor a list, returning empty list.")
                return []
        except Exception as e:
            self.logger.error(f"Error loading or parsing task patterns from {self.patterns_json_path}: {e}")
            return []

    def get_available_assets_for_profile(self, profile_name: str) -> List[str]:
        """
        Retrieves a list of available asset names for the given profile.
        Returns sorted asset names from assetPatterns in patterns.json.
        Handles both dict and list structures for assetPatterns.
        """
        try:
            with open(self.patterns_json_path, 'r', encoding='utf-8') as f:
                patterns_data = json.load(f)
            asset_patterns = patterns_data.get('assetPatterns', {})
            if isinstance(asset_patterns, dict):
                # If assetPatterns is a dict, return its keys
                return sorted(list(asset_patterns.keys()))
            elif isinstance(asset_patterns, list):
                # If assetPatterns is a list, return as strings
                return sorted([str(x) for x in asset_patterns])
            else:
                self.logger.warning("Asset patterns are neither a dict nor a list, returning empty list.")
                return []
        except Exception as e:
            self.logger.error(f"Error loading or parsing asset patterns from {self.patterns_json_path}: {e}")
            return []

    def get_available_resolutions_for_profile(self, profile_name: str) -> List[str]:
        """
        Retrieves a list of available resolution names from patterns.json.
        Robustly handles both dict and list structures for resolutionPatterns.
        """
        try:
            with open(self.patterns_json_path, 'r', encoding='utf-8') as f:
                patterns_data = json.load(f)
            res_patterns = patterns_data.get('resolutionPatterns', {})
            if isinstance(res_patterns, dict):
                return sorted(list(res_patterns.keys()))
            elif isinstance(res_patterns, list):
                return sorted([str(x) for x in res_patterns])
            else:
                return []
        except Exception as e:
            self.logger.error(f"Error loading or parsing resolution patterns from {self.patterns_json_path}: {e}")
            return []

    def get_available_stages_for_profile(self, profile_name: str) -> List[str]:
        """
        Retrieves a list of available stage names from patterns.json.
        Robustly handles both dict and list structures for stagePatterns.
        """
        try:
            with open(self.patterns_json_path, 'r', encoding='utf-8') as f:
                patterns_data = json.load(f)
            stage_patterns = patterns_data.get('stagePatterns', {})
            if isinstance(stage_patterns, dict):
                return sorted(list(stage_patterns.keys()))
            elif isinstance(stage_patterns, list):
                return sorted([str(x) for x in stage_patterns])
            else:
                return []
        except Exception as e:
            self.logger.error(f"Error loading or parsing stage patterns from {self.patterns_json_path}: {e}")
            return []

    def get_path_preview(
        self,
        item_data: Dict[str, Any],
        changed_field: str, # e.g., "task", "asset", "version"
        new_value: Optional[str],
        profile_name: str,
        destination_root: str
    ) -> str:
        """
        Generates a preview of the destination path if a specific field (like task or asset)
        of an item were changed.

        Args:
            item_data: The original data of the item being edited.
            changed_field: The key of the normalized_part that was changed (e.g., "task").
            new_value: The new value for the changed_field. Can be None or empty if clearing a field.
            profile_name: The name of the current profile.
            destination_root: The root directory for destinations.

        Returns:
            A string representing the predicted new destination path.
        """
        # Ensure the correct profile rules are loaded for the preview
        if not self.current_profile_name or self.current_profile_name != profile_name:
            # self.logger.info(  # (Silenced for normal use. Re-enable for troubleshooting.)f"Path preview requested for profile '{profile_name}', but current is '{self.current_profile_name}'. Setting profile for preview.")
            if not self.set_profile(profile_name):
                self.logger.error(f"Failed to set profile '{profile_name}' for path preview.")
                return f"Error: Could not load profile '{profile_name}' for preview."
        
        if not self.current_profile_rules:
            self.logger.error(f"No rules loaded for current profile '{self.current_profile_name}', cannot generate path preview.")
            return "Error: Profile rules not loaded for preview."

        self.logger.debug(
            f"get_path_preview called with: item_data.id={item_data.get('id')}, "
            f"changed_field='{changed_field}', new_value='{new_value}', "
            f"profile='{profile_name}', dest_root='{destination_root}'"
        )

        if not item_data or not profile_name or not destination_root:
            self.logger.warning("get_path_preview: Missing critical input data.")
            return "Error: Missing input data for preview."

        original_item_details = {
            'name': item_data.get('filename'),
            'path': item_data.get('source_path'),
            'type': item_data.get('type', 'file').lower(),
            'size': item_data.get('size')
        }
        if item_data.get('sequence_info'):
            original_item_details['sequence_info'] = item_data.get('sequence_info')

        modified_parts = item_data.get('normalized_parts', {}).copy()
        
        if new_value is None or new_value == '':
            modified_parts.pop(changed_field, None)
        else:
            modified_parts[changed_field] = new_value

        profile_for_preview = {
            "name": self.current_profile_name,
            "rules": self.current_profile_rules
        }

        try:
            if hasattr(self.mapping_generator, 'generate_path_from_proposal_data'):
                temp_proposal_for_path_gen = {
                    'original_item': original_item_details,
                    'tags': modified_parts, 
                    'id': item_data.get('id') 
                }
                predicted_path = self.mapping_generator.generate_path_from_proposal_data(
                    proposal_data=temp_proposal_for_path_gen,
                    profile=profile_for_preview,
                    root_output_dir=destination_root
                )
                self.logger.debug(f"get_path_preview: Predicted path = {predicted_path}")
                return predicted_path
            else:
                self.logger.warning(
                    "MappingGenerator does not have 'generate_path_from_proposal_data'. "
                    "Path preview will be a placeholder."
                )
                parts_for_name = [
                    modified_parts.get('asset', original_item_details.get('name', 'item').split('.')[0]),
                    modified_parts.get('task'),
                    modified_parts.get('version')
                ]
                base_name = "_".join(filter(None, parts_for_name))
                extension = Path(original_item_details.get('name', '')).suffix
                dest_root_path = Path(destination_root)
                return str(dest_root_path / "PREVIEW_PATH_FOR" / f"{base_name}{extension}") + " (Method not fully implemented)"

        except Exception as e:
            self.logger.error(f"Error during path preview generation: {e}", exc_info=True)
            return f"Error generating preview: {e}"

    def get_profile_batch_edit_options(self) -> Dict[str, List[str]]:
        """
        Returns a dictionary of dropdown options for batch edit fields, using patterns.json and the current profile.
        Keys are internal field names (e.g., 'task_name', 'asset_name', etc.).
        Handles both lists of strings and lists of dicts in patterns.json.
        """
        options = {}
        try:
            with open(self.patterns_json_path, 'r', encoding='utf-8') as f:
                patterns_data = json.load(f)
            # Map internal field names to patterns.json keys
            field_to_pattern_key = {
                'shot_name': 'shotPatterns',
                'asset_name': 'assetPatterns',
                'task_name': 'taskPatterns',
                'stage_name': 'stagePatterns',
                'resolution_name': 'resolutionPatterns',
                'version_number': 'versionPatterns',
            }
            for internal_name, pattern_key in field_to_pattern_key.items():
                val = patterns_data.get(pattern_key)
                if val is None:
                    options[internal_name] = []
                elif isinstance(val, dict):
                    # For taskPatterns, use the keys as display names
                    options[internal_name] = list(val.keys())
                elif isinstance(val, list):
                    # If list of dicts with 'name' or 'pattern', extract those
                    if val and isinstance(val[0], dict):
                        names = []
                        for d in val:
                            if isinstance(d, dict):
                                if 'name' in d:
                                    names.append(d['name'])
                                elif 'pattern' in d:
                                    names.append(d['pattern'])
                        options[internal_name] = names
                    else:
                        # List of strings
                        options[internal_name] = [str(x) for x in val]
                else:
                    options[internal_name] = []
        except Exception as e:
            self.logger.error(f"Error loading batch edit options from {self.patterns_json_path}: {e}")
            # Fallback: empty lists for all fields
            for k in ['shot_name', 'asset_name', 'task_name', 'stage_name', 'resolution_name', 'version_number']:
                options[k] = []
        return options

    def get_batch_edit_preview_path(self, item_data: Dict[str, Any], changes: Dict[str, Any], destination_root: str) -> str:
        """
        Returns a preview of the destination path for batch edit dialog, using the same normalization logic as the main app.
        Args:
            item_data: The proposal dictionary for the file/sequence.
            changes: Dict of field overrides (e.g., {"task": "comp"}).
            destination_root: The root output directory to use for preview.
        Returns:
            The predicted destination path as a string.
        """
        if not self.current_profile_name:
            self.logger.warning("get_batch_edit_preview_path: No profile set.")
            return "Error: No profile set."
        modified_parts = item_data.get('normalized_parts', {}).copy()
        for k, v in changes.items():
            if v is None or v == '':
                modified_parts.pop(k, None)
            else:
                modified_parts[k] = v
        profile_for_preview = {
            "name": self.current_profile_name,
            "rules": self.current_profile_rules
        }
        original_item_details = {
            'name': item_data.get('filename'),
            'path': item_data.get('source_path'),
            'type': item_data.get('type', 'file').lower(),
            'size': item_data.get('size')
        }
        if item_data.get('sequence_info'):
            original_item_details['sequence_info'] = item_data.get('sequence_info')
        try:
            if hasattr(self.mapping_generator, 'generate_path_from_proposal_data'):
                temp_proposal_for_path_gen = {
                    'original_item': original_item_details,
                    'tags': modified_parts,
                    'id': item_data.get('id')
                }
                predicted_path = self.mapping_generator.generate_path_from_proposal_data(
                    proposal_data=temp_proposal_for_path_gen,
                    profile=profile_for_preview,
                    root_output_dir=destination_root
                )
                return predicted_path
            else:
                return "Preview not available (mapping_generator missing method)"
        except Exception as e:
            self.logger.error(f"Error during batch edit preview path generation: {e}", exc_info=True)
            return f"Error generating preview: {e}"


        