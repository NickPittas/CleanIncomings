import json
import os
import sys
import time
import uuid
from pathlib import Path
import threading # Added for scan threading
from typing import List, Dict, Any, Optional, Callable

from .scanner import FileSystemScanner
from .mapping import MappingGenerator

class GuiNormalizerAdapter:
    def __init__(self, config_dir_path: str):
        self.config_dir_path = Path(config_dir_path)
        self.patterns_json_path = self.config_dir_path / "patterns.json"
        self.profiles_json_path = self.config_dir_path / "profiles.json"

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
            raise ValueError(f"Error decoding {self.profiles_json_path}: {e}")
        except Exception as e:
            raise IOError(f"Could not read {self.profiles_json_path}: {e}")

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
                    scan_progress = final_progress_check
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
            raise ValueError("Scan completed but no tree structure found in results (missing/malformed).")
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
                raise ValueError("Scan completed but no tree structure found in results (empty root not allowed).")
            # If tree is not an empty root, or if it is an empty root and it's allowed, we proceed.

        # Get profile data
        profile_config_entry = self.all_profiles_data.get(profile_name)

        if not profile_config_entry:
            raise ValueError(f"Profile '{profile_name}' not found in profiles.json. Available: {', '.join(self.get_profile_names())}")

        actual_rules_list: Optional[List[Dict[str, Any]]] = None

        if isinstance(profile_config_entry, list):
            # This is assumed to be the List[Dict[str, List[str]]] of rules directly.
            # Each item in the list should be a dictionary representing a rule.
            actual_rules_list = []
            for i, rule_item in enumerate(profile_config_entry):
                if not isinstance(rule_item, dict):
                    raise TypeError(
                        f"Profile '{profile_name}': rule item at index {i} is not a dictionary. "
                        f"Expected format is a list of rule dictionaries. Got type: {type(rule_item)} for item: {rule_item}"
                    )
                actual_rules_list.append(rule_item)

        elif isinstance(profile_config_entry, dict):
            # This is assumed to be a full profile dictionary containing a 'rules' key.
            # The value of 'rules' should be the List[Dict[str, List[str]]].
            if "rules" not in profile_config_entry or not isinstance(profile_config_entry["rules"], list):
                raise ValueError(
                    f"Profile '{profile_name}' (type: dict) is missing a 'rules' key, "
                    f"or 'rules' is not a list. Found keys: {list(profile_config_entry.keys())}. "
                    f"The 'rules' key must point to a list of rule dictionaries."
                )
            actual_rules_list = []
            for i, rule_item in enumerate(profile_config_entry["rules"]):
                if not isinstance(rule_item, dict):
                    raise TypeError(
                        f"Profile '{profile_name}': rule item at index {i} within 'rules' list is not a dictionary. "
                        f"Got type: {type(rule_item)} for item: {rule_item}"
                    )
                actual_rules_list.append(rule_item)
        else:
            raise TypeError(
                f"Entry for profile '{profile_name}' in profiles.json must be a list of rule dictionaries "
                f"(e.g., [{'Path1': ['keyword1']}, {'Path2': ['keyword2']}]) "
                f"or a dictionary containing a 'rules' key with such a list. "
                f"Got type: {type(profile_config_entry)}"
            )
        
        if actual_rules_list is None: # Should be caught by earlier checks, but as a safeguard.
            raise ValueError(f"Could not determine a valid rules list for profile '{profile_name}'. Check profiles.json structure.")

        # Prepare the profile object to be passed to the mapping generator.
        # This object should be a dictionary containing the profile name and its rules.
        # Other metadata could be included if the mapping generator expects it.
        profile_object_for_generator = {
            "name": profile_name,  # The name of the profile being used
            "rules": actual_rules_list,  # The validated list of rule dictionaries
            # Add other profile metadata if needed by MappingGenerator or its callees.
            # For example, if vfx_root or description were globally relevant:
            # "vfx_root": profile_config_entry.get("vfx_root") if isinstance(profile_config_entry, dict) else "/default/vfx_root",
            # "description": profile_config_entry.get("description") if isinstance(profile_config_entry, dict) else "Profile loaded by adapter"
        }

        if status_callback:
            status_callback({'type': 'mapping_generation', 'data': {'status': 'starting', 'message': 'Starting mapping generation...'}})

        # Debug prints for inputs to mapping_generator
        print(f"[ADAPTER_DEBUG] Tree (type: {type(original_scan_tree)}): {list(original_scan_tree.keys()) if isinstance(original_scan_tree, dict) else 'Not a dict or None'}", file=sys.stderr)
        if isinstance(original_scan_tree, dict) and original_scan_tree.get('children') is not None:
            print(f"[ADAPTER_DEBUG] Tree children count: {len(original_scan_tree['children'])}", file=sys.stderr)
        else:
            print(f"[ADAPTER_DEBUG] Tree has no children or is not structured as expected.", file=sys.stderr)
        print(f"[ADAPTER_DEBUG] Profile for generator: {profile_object_for_generator}", file=sys.stderr)

        # Generate mapping proposals
        proposals = self.mapping_generator.generate_mappings(
            tree=original_scan_tree,
            profile=profile_object_for_generator, # Pass the full profile dictionary
            root_output_dir=destination_root,
            batch_id=batch_id, # Pass batch_id for potential internal use by mapping_generator
            status_callback=status_callback # Propagate status_callback
        )
        # Debug print for proposals from mapping_generator
        if proposals and len(proposals) > 0:
            first_raw_proposal = proposals[0]
            raw_tags = first_raw_proposal.get('tags', 'N/A_TAGS_FIELD_MISSING_OR_NONE')
            raw_original_item = first_raw_proposal.get('original_item', {})
            raw_original_item_name = raw_original_item.get('name', 'N/A_ORIGINAL_NAME')
            raw_status = first_raw_proposal.get('status', 'N/A_STATUS')
            raw_target_path = first_raw_proposal.get('targetPath', 'N/A_TARGETPATH')
            print(f"[ADAPTER_DEBUG] First RAW proposal: Name='{raw_original_item_name}', Status='{raw_status}', TargetPath='{raw_target_path}', Tags={raw_tags}", file=sys.stderr)
        elif proposals is not None: # Empty list
            print(f"[ADAPTER_DEBUG] Proposals from mapping_generator: Empty list (len: 0)", file=sys.stderr)
        else: # None
            print(f"[ADAPTER_DEBUG] Proposals from mapping_generator: None", file=sys.stderr)

        # First (redundant) proposal transformation loop removed.

        if status_callback:
            status_callback({'type': 'mapping_generation', 'data': {'status': 'completed', 'message': 'Mapping generation complete. Transforming results...'}})

        if status_callback:
            status_callback({'type': 'transformation', 'data': {'status': 'starting', 'message': 'Transforming proposals...'}})

        # Transform proposals for GUI
        transformed_proposals = []
        if proposals: 
            for p_item in proposals:
                original_item = p_item.get('original_item', {})
                source_path_str = str(original_item.get('path', 'N/A'))

                # ---- CASCADE DEBUG PRINT START ----
                # Check if the original item type is 'sequence' (lowercase, as it's before capitalization for GUI)
                # if original_item.get('type') == 'sequence':
                #     print(f"[ADAPTER_DEBUG] RAW p_item (type: sequence): Name='{original_item.get('name')}', p_item.sequence_info='{p_item.get('sequence_info')}', p_item.keys='{list(p_item.keys())}'", file=sys.stderr)
                # ---- CASCADE DEBUG PRINT END ----
                
                tags_data = p_item.get('tags', {})
                if not isinstance(tags_data, dict):
                    tags_data = {} 

                matched_tags = {k: v for k, v in tags_data.items() if v is not None and v != ''}

                # This 'gui_matched_tags' will be used for the 'Tags' column in GUI and contains everything from p_item's 'tags'
                gui_matched_tags = {k: v for k, v in tags_data.items() if v is not None and v != ''}

                # This 'normalized_parts_dict' is specifically for structured columns like Task, Asset
                # It sources its values from tags_data (which is p_item.get('tags', {}))
                normalized_parts_dict = {
                    'shot': tags_data.get('shot'),
                    'task': tags_data.get('task'),
                    'asset': tags_data.get('asset_name') or tags_data.get('asset') or tags_data.get('asset_type'), # Check for asset_name, asset, or asset_type
                    'version': tags_data.get('version'),
                    'resolution': tags_data.get('resolution'),
                    'stage': tags_data.get('stage')
                }
                # Filter out None values from normalized_parts_dict
                normalized_parts_dict = {k: v for k, v in normalized_parts_dict.items() if v is not None}

                transformed_item = {
                    'id': p_item.get('id', str(uuid.uuid4())),
                    'source_path': source_path_str,
                    'filename': original_item.get('name', 'N/A'),
                    'new_destination_path': p_item.get('targetPath', ''),
                    'new_name': Path(p_item.get('targetPath', '')).name if p_item.get('targetPath') else original_item.get('name', 'N/A'),
                    'type': original_item.get('type', 'file').capitalize(),
                    'size': original_item.get('size', ''),
                    'sequence_info': p_item.get('sequence_info'),
                    'matched_rules': p_item.get('matched_rules', []),
                    'matched_tags': gui_matched_tags, # Use the filtered tags_data for the GUI's 'Tags' column
                    'normalized_parts': normalized_parts_dict, # GUI expects this structure for task, asset etc.
                    'status': p_item.get('status', 'unknown'),
                    'error_message': p_item.get('error_message') or p_item.get('error') # Check both possible error keys
                }
                if not transformed_proposals: # This will be true only for the first item
                    print(f"[ADAPTER_DEBUG] First TRANSFORMED item (inside loop):", file=sys.stderr)
                    print(f"  Original Name: {original_item.get('name', 'N/A')}", file=sys.stderr)
                    print(f"  Normalized Parts: {transformed_item.get('normalized_parts')}", file=sys.stderr)
                    print(f"  Matched Tags: {transformed_item.get('matched_tags')}", file=sys.stderr)
                transformed_proposals.append(transformed_item)
        else: 
             if status_callback:
                status_callback({'type': 'mapping_generation', 'data': {'status': 'warning', 'message': 'No proposals generated.'}})
        
        if status_callback:
            status_callback({'type': 'transformation', 'data': {'status': 'completed', 'message': 'Proposals transformed.'}})

        # Debug print for final transformed_proposals
        # print(f"[ADAPTER_DEBUG] Transformed proposals (len: {len(transformed_proposals)}): {transformed_proposals[:1] if transformed_proposals else 'Empty'}", file=sys.stderr)
        return {
            "original_scan_tree": original_scan_tree,
            "proposals": transformed_proposals
        }

# Example Usage (for testing purposes, typically not run directly)
if __name__ == '__main__':
    # Create dummy config files for testing
    dummy_config_dir = Path(__file__).parent.parent / "tmp_config_for_adapter_test"
    dummy_config_dir.mkdir(exist_ok=True)
    
    dummy_patterns_file = dummy_config_dir / "patterns.json"
    with open(dummy_patterns_file, 'w') as f:
        json.dump({
            "shotPatterns": [{"pattern": "(sh[0-9]+)", "name": "Shot Pattern"}],
            "taskPatterns": {"modeling": ["mod", "mdl"]},
            "resolutionPatterns": [],
            "versionPatterns": [{"pattern": "(v[0-9]+)", "name": "Version Pattern"}],
            "assetPatterns": [],
            "stagePatterns": []
        }, f)

    dummy_profiles_file = dummy_config_dir / "profiles.json"
    with open(dummy_profiles_file, 'w') as f:
        json.dump({
            "TestProfile": {
                "name": "TestProfile",
                "vfx_root": "/projects/test_project",
                "description": "A test profile",
                "rules": [
                    {"3D/Renders": ["rend", "lighting"]}
                ]
            }
        }, f)

    # Create a dummy source directory with a file
    dummy_source_dir = Path(__file__).parent.parent / "tmp_source_for_adapter_test"
    dummy_source_dir.mkdir(exist_ok=True)
    with open(dummy_source_dir / "sh001_mod_v01.txt", 'w') as f:
        f.write("dummy content")

    dummy_dest_dir = Path(__file__).parent.parent / "tmp_dest_for_adapter_test"
    dummy_dest_dir.mkdir(exist_ok=True)

    print(f"Dummy config path: {dummy_config_dir.resolve()}")
    print(f"Dummy source path: {dummy_source_dir.resolve()}")
    print(f"Dummy dest path: {dummy_dest_dir.resolve()}")

    try:
        adapter = GuiNormalizerAdapter(config_dir_path=str(dummy_config_dir))
        print(f"Available profiles: {adapter.get_profile_names()}")
        
        def my_status_callback(progress_info):
            print(f"Status Update: {progress_info['type']} - {progress_info['data'].get('status', 'N/A')} - {progress_info['data'].get('progressPercentage', 0):.2f}%")

        results = adapter.scan_and_normalize_structure(
            base_path=str(dummy_source_dir),
            profile_name="TestProfile",
            destination_root=str(dummy_dest_dir),
            status_callback=my_status_callback
        )
        print("\nNormalization Results:")
        for item in results:
            print(json.dumps(item, indent=2))
    except Exception as e:
        print(f"Error during example usage: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Clean up dummy files and directories
        import shutil
        # shutil.rmtree(dummy_config_dir, ignore_errors=True)
        # shutil.rmtree(dummy_source_dir, ignore_errors=True)
        # shutil.rmtree(dummy_dest_dir, ignore_errors=True)
        print("\nClean up of temp files/dirs skipped for inspection. Manually delete them if needed:")
        print(f"- {dummy_config_dir.resolve()}")
        print(f"- {dummy_source_dir.resolve()}")
        print(f"- {dummy_dest_dir.resolve()}")

