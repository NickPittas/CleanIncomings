import json
import os
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
                    print(f"[DEBUG][ADAPTER] Raising 'status unclear'. final_progress_check: {final_progress_check}, scan_error: {scan_error}", flush=True)
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
        tree = scan_result.get("tree")
        if not tree:
            raise ValueError("Scan completed but no tree structure found in results.")

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

        # Generate mapping proposals
        proposals = self.mapping_generator.generate_mappings(
            tree=tree,
            profile=profile_object_for_generator, # Pass the full profile dictionary
            root_output_dir=destination_root,
            batch_id=batch_id # Pass batch_id for potential internal use by mapping_generator
        )

        # Transform proposals for GUI
        transformed_proposals = []
        for p_idx, p_item in enumerate(proposals):
            # Determine original path and filename
            original_path = p_item.get("source_path", p_item.get("original_path"))
            filename = p_item.get("file_name", p_item.get("name"))
            if not original_path and filename:
                 # If source_path is missing but we have a list of files (for sequences)
                if p_item.get("type") == "sequence" and isinstance(p_item.get("files"), list) and p_item["files"]:
                    original_path = p_item["files"][0] # Take path of first file in sequence
                    # filename might be base_name + frame_range + suffix for sequences
                    if p_item.get("base_name") and p_item.get("frame_range_str") and p_item.get("suffix"):
                        filename = f"{p_item['base_name']}{p_item['frame_range_str']}{p_item['suffix']}"
                    elif p_item.get("base_name") and p_item.get("suffix") : # single frame sequence
                         filename = f"{p_item['base_name']}{p_item['suffix']}"

            if not original_path:
                original_path = f"unknown_path_for_item_{p_idx}"
            if not filename:
                filename = Path(original_path).name if original_path != f"unknown_path_for_item_{p_idx}" else f"unknown_filename_{p_idx}"

            # Extract normalized parts - keys might vary, adjust as per actual proposal structure
            normalized_parts = {
                "shot": p_item.get("shot_name", p_item.get("shot")),
                "task": p_item.get("task_name", p_item.get("task")),
                "version": p_item.get("version_name", p_item.get("version")),
                "asset": p_item.get("asset_name", p_item.get("asset")),
                "stage": p_item.get("stage_name", p_item.get("stage")),
                "resolution": p_item.get("resolution_name", p_item.get("resolution")),
                "description": p_item.get("description")
            }
            
            # Construct matched_tags
            matched_tags = []
            if p_item.get("status"):
                matched_tags.append(p_item.get("status")) # e.g., "auto", "manual"
            if p_item.get("type"):
                matched_tags.append(p_item.get("type")) # e.g., "file", "sequence"
            if p_item.get("matched_rule_name"):
                 matched_tags.append(f"rule:{p_item.get('matched_rule_name')}")
            if p_item.get("error"): # If there was an error processing this item
                matched_tags.append("error")

            transformed_item = {
                "id": p_item.get("id", str(uuid.uuid4())), # Ensure each item has a unique ID
                "original_path": str(original_path),
                "filename": filename,
                "size": p_item.get("size"),
                "type": p_item.get("type", "unknown"),
                "normalized_parts": {k: v for k, v in normalized_parts.items() if v is not None},
                "new_destination_path": p_item.get("target_path"),
                "matched_tags": matched_tags,
                "status": p_item.get("status", "unknown"), # 'auto', 'manual', 'error', 'unmatched'
                "error_message": p_item.get("error")
            }
            transformed_proposals.append(transformed_item)
        
        return transformed_proposals

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

