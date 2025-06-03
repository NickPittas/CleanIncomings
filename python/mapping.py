import re
from pathlib import Path
from typing import Dict, Any, Optional, Callable # Added for type hinting
from pathlib import Path
from .mapping_utils.init_patterns_from_profile import init_patterns_from_profile
from .mapping_utils.generate_mappings import generate_mappings
from .mapping_utils.group_image_sequences import group_image_sequences
from .mapping_utils.finalize_sequences import finalize_sequences
from .mapping_utils.is_network_path import is_network_path
from .mapping_utils.create_sequence_mapping import create_sequence_mapping
from .mapping_utils.create_simple_mapping import create_simple_mapping
from .mapping_utils.generate_simple_target_path import generate_simple_target_path
from .mapping_utils.extract_sequence_info import extract_sequence_info
from .mapping_utils.process_file_for_sequence import process_file_for_sequence
from .mapping_utils.config_loader import load_config
from .mapping_utils.shot_extractor import extract_shot_simple
from .mapping_utils.task_extractor import extract_task_simple
from .mapping_utils.version_extractor import extract_version_simple
from .mapping_utils.resolution_extractor import extract_resolution_simple
from .mapping_utils.asset_extractor import extract_asset_simple
from .mapping_utils.stage_extractor import extract_stage_simple


class MappingGenerator:

    def __init__(self, config_path: str = None):
        if config_path is None:
            script_dir = Path(__file__).parent.parent
            config_path = script_dir / "config" / "patterns.json"
        self.config_path = Path(config_path)  # Ensure config_path is a Path object
        self.config = {}
        self.shot_patterns = []
        self.task_patterns = {}
        self.resolution_patterns = []
        self.version_patterns = []
        self.asset_patterns = []
        self.stage_patterns = []
        self.max_depth = 10
        self.current_frame_numbers = []  # Initialize frame numbers storage
        self.reload_patterns()  # Load patterns on initialization

    def reload_patterns(self):
        """Reload patterns from the config file."""
        print(f"Reloading patterns from: {self.config_path}")
        try:
            self.config = load_config(self.config_path)
            self.shot_patterns = self.config.get("shotPatterns", [])
            self.task_patterns = self.config.get("taskPatterns", {})
            self.resolution_patterns = self.config.get("resolutionPatterns", [])
            self.version_patterns = self.config.get("versionPatterns", [])
            self.asset_patterns = self.config.get("assetPatterns", [])
            self.stage_patterns = self.config.get("stagePatterns", [])

            # Ensure patterns that should be lists are lists
            if not isinstance(self.shot_patterns, list):
                self.shot_patterns = []
            if not isinstance(self.resolution_patterns, list):
                self.resolution_patterns = []
            if not isinstance(self.version_patterns, list):
                self.version_patterns = []
            if not isinstance(self.asset_patterns, list):
                self.asset_patterns = []
            if not isinstance(self.stage_patterns, list):
                self.stage_patterns = []
            if not isinstance(self.task_patterns, dict):
                self.task_patterns = {}

            print(
                f"Patterns reloaded: "
                f"{len(self.shot_patterns)} shot, "
                f"{len(self.task_patterns)} task, "
                f"{len(self.version_patterns)} version, "
                f"{len(self.resolution_patterns)} resolution, "
                f"{len(self.asset_patterns)} asset, "
                f"{len(self.stage_patterns)} stage patterns."
            )
            return True
        except FileNotFoundError:
            print(f"ERROR: Config file not found at {self.config_path}. Patterns not loaded.")
            self.config = {}
            self.shot_patterns = []
            self.task_patterns = {}
            self.resolution_patterns = []
            self.version_patterns = []
            self.asset_patterns = []
            self.stage_patterns = []
            return False
        except Exception as e:
            print(f"ERROR: Failed to load or parse config from {self.config_path}: {e}. Patterns not loaded.")
            self.config = {}
            self.shot_patterns = []
            self.task_patterns = {}
            self.resolution_patterns = []
            self.version_patterns = []
            self.asset_patterns = []
            self.stage_patterns = []
            return False

    def _extract_shot_simple(self, filename: str, path: str) -> str:
        # IMPORTANT: Only search filename, never path (per IMPORTANT.md)
        return extract_shot_simple(filename, "", shot_patterns=self.shot_patterns)

    def _extract_task_simple(self, filename: str, path: str) -> str:
        # IMPORTANT: Only search filename, never path (per IMPORTANT.md)
        return extract_task_simple(filename, "", task_patterns=self.task_patterns)

    def _extract_version_simple(self, filename: str) -> str:
        return extract_version_simple(filename, version_patterns=self.version_patterns)

    def _extract_resolution_simple(self, filename: str, path: str) -> str:
        # IMPORTANT: Only search filename, never path (per IMPORTANT.md)
        return extract_resolution_simple(filename, "", resolution_patterns=self.resolution_patterns)

    def _extract_asset_simple(self, filename: str) -> str:
        # IMPORTANT: Only use patterns from patterns.json, only search filename
        return extract_asset_simple(filename, self.asset_patterns)

    def _extract_stage_simple(self, filename: str) -> str:
        # IMPORTANT: Only use patterns from patterns.json, only search filename
        return extract_stage_simple(filename, self.stage_patterns)

    def _create_sequence_mapping(self, sequence, full_profile_data: Dict[str, Any], root_output_dir: str, original_base_name=None):
        return create_sequence_mapping(
            sequence=sequence,
            profile=full_profile_data,
            root_output_dir=root_output_dir,
            original_base_name=original_base_name,
            extract_shot_simple=extract_shot_simple,
            extract_task_simple=extract_task_simple,
            extract_version_simple=extract_version_simple,
            extract_resolution_simple=extract_resolution_simple,
            extract_asset_simple=extract_asset_simple,
            extract_stage_simple=extract_stage_simple,
            generate_simple_target_path=generate_simple_target_path,
            extract_sequence_info=extract_sequence_info,
            current_frame_numbers=self.current_frame_numbers,
            p_shot=self.shot_patterns,
            p_task=self.task_patterns,
            p_version=self.version_patterns,
            p_resolution=self.resolution_patterns,
            p_asset=self.asset_patterns,
            p_stage=self.stage_patterns
        )

    def _create_simple_mapping(self, node, profile_rules, root_output_dir: str):
        return create_simple_mapping(
            node=node,
            profile_rules=profile_rules,
            root_output_dir=root_output_dir,
            extract_shot_simple=extract_shot_simple,
            extract_task_simple=extract_task_simple,
            extract_version_simple=extract_version_simple,
            extract_resolution_simple=extract_resolution_simple,
            extract_asset_simple=extract_asset_simple,
            extract_stage_simple=extract_stage_simple,
            p_shot=self.shot_patterns,
            p_task=self.task_patterns,
            p_version=self.version_patterns,
            p_resolution=self.resolution_patterns,
            p_asset=self.asset_patterns,
            p_stage=self.stage_patterns
        )

    def _group_image_sequences(self, files, batch_id=None, **kwargs):
        return group_image_sequences(files, batch_id=batch_id, **kwargs)

    def _process_file_for_sequence(self, file_node, file_groups, single_files, sequence_extensions):
        return process_file_for_sequence(file_node, file_groups, single_files, sequence_extensions)

    def _finalize_sequences(self, file_groups, files, single_files, batch_id):
        return finalize_sequences(file_groups, files, single_files, batch_id)

    def _extract_sequence_info(self, filename):
        return extract_sequence_info(filename)

    def _init_patterns_from_profile(self, profile):
        return init_patterns_from_profile(self, profile)

    def generate_mappings(self, tree, profile: Dict[str, Any], root_output_dir: str, batch_id=None, status_callback: Optional[Callable[[Dict[str, Any]], None]] = None, **kwargs):
        rules_list = profile.get('rules', [])
        if not isinstance(rules_list, list):
            raise ValueError(
                f"Profile dictionary passed to MappingGenerator.generate_mappings is missing a 'rules' key, "
                f"or 'rules' is not a list. Profile keys: {list(profile.keys())}"
            )

        actual_status_callback = kwargs.pop('status_callback', status_callback)

        return generate_mappings(
            tree=tree,
            profile=profile,
            batch_id=batch_id,
            group_image_sequences=self._group_image_sequences,
            extract_sequence_info=self._extract_sequence_info,
            is_network_path=is_network_path,
            create_sequence_mapping=lambda seq, prof_dict, orig_base_name: self._create_sequence_mapping(seq, prof_dict, root_output_dir, orig_base_name),
            create_simple_mapping=lambda node, prof_dict: self._create_simple_mapping(node, prof_dict['rules'], root_output_dir),
            finalize_sequences=self._finalize_sequences,
            status_callback=actual_status_callback, # Pass it here
            **kwargs # Pass remaining kwargs
        )

    def _init_patterns_from_profile(self, profile):
        return init_patterns_from_profile(self, profile)

    def generate_path_from_proposal_data(
        self,
        proposal_data: Dict[str, Any],
        profile: Dict[str, Any],  # Full profile dict: {"name": "...", "rules": [...]}
        root_output_dir: str
    ) -> str:
        """
        Generates a predicted destination path for an item based on potentially
        modified tags/parts.

        Args:
            proposal_data: Contains 'original_item' details and 'tags' 
                           (the modified parts like shot, task, asset).
                           Example: {
                               'original_item': {'name': 'file.exr', 'path': '/src/file.exr', 'type': 'file'},
                               'tags': {'task': 'lighting', 'asset': 'charA', 'version': 'v002'}
                           }
            profile: The full profile dictionary, including 'name' and 'rules'.
            root_output_dir: The root directory for destination paths.

        Returns:
            The predicted destination path string. Returns an error string or
            a placeholder if path generation fails.
        """
        # Local import to avoid circular dependencies at module load time if mapping_utils imports from mapping
        from .mapping_utils.generate_simple_target_path import generate_simple_target_path

        if not proposal_data or not profile or not root_output_dir:
            # TODO: Consider logging this warning/error as well via self.logger if available
            print("[MappingGenerator] Error: Missing critical data for path preview (proposal_data, profile, or root_output_dir).")
            return "Error: Missing critical data for path preview."

        original_item_details = proposal_data.get('original_item')
        modified_tags = proposal_data.get('tags')

        if not isinstance(original_item_details, dict) or not isinstance(modified_tags, dict):
            print("[MappingGenerator] Error: Invalid proposal_data structure (original_item or tags missing or not dicts).")
            return "Error: Invalid proposal_data structure."

        filename = original_item_details.get('name') # This could be a single filename or a sequence pattern like name.%04d.ext
        item_type = original_item_details.get('type', 'file').lower()
        # sequence_info = original_item_details.get('sequence_info') # Available if needed for more complex sequence logic

        if not filename:
            print("[MappingGenerator] Error: Filename missing in original_item_details for path preview.")
            return "Error: Filename missing for path preview."

        profile_rules = profile.get('rules')
        if not isinstance(profile_rules, list):
            profile_name = profile.get("name", "Unknown Profile")
            print(f"[MappingGenerator] Error: Profile '{profile_name}' is missing 'rules' or rules are not a list.")
            return f"Error: Invalid rules for profile '{profile_name}'."

        parsed_shot = modified_tags.get('shot')
        parsed_task = modified_tags.get('task')
        parsed_asset = modified_tags.get('asset')
        parsed_stage = modified_tags.get('stage')
        parsed_version = modified_tags.get('version')
        parsed_resolution = modified_tags.get('resolution')

        # Common logic for calling generate_simple_target_path
        def _get_generated_path_string(current_filename: str) -> str:
            path_gen_result = generate_simple_target_path(
                root_output_dir=root_output_dir,
                profile_rules=profile_rules,
                filename=current_filename, # The filename to use for path construction (actual or pattern)
                parsed_shot=parsed_shot,
                parsed_task=parsed_task,
                parsed_asset=parsed_asset,
                parsed_stage=parsed_stage,
                parsed_version=parsed_version,
                parsed_resolution=parsed_resolution
            )
            
            target_path = path_gen_result.get("target_path")
            if path_gen_result.get("ambiguous_match"):
                # TODO: GuiNormalizerAdapter could log ambiguous_options from path_gen_result if needed
                return f"Error: Ambiguous path for '{current_filename}'."
            if not target_path:
                return f"Error: Could not determine target path for '{current_filename}'."
            return target_path

        if item_type == 'file':
            try:
                return _get_generated_path_string(filename)
            except Exception as e:
                print(f"[MappingGenerator] Exception during path preview for file '{filename}': {e}")
                # self.logger.error(f"Exception generating path preview for file '{filename}': {e}", exc_info=True) # If logger
                return f"Error: Exception generating path preview for '{filename}'."

        elif item_type == 'sequence':
            # For sequences, the `filename` in `original_item_details` is typically the display name 
            # (e.g., "my_render.[0001-0100].exr") or the sequence pattern ("my_render.%04d.exr").
            # `generate_simple_target_path` expects a filename string that it will append.
            # Using the sequence pattern name (like "my_render.%04d.exr") as the `filename` argument
            # to `_get_generated_path_string` is generally appropriate for a directory preview.
            try:
                # The `filename` for a sequence item should be its pattern (e.g., image.%04d.exr)
                # or its display name if that's what generate_simple_target_path expects to append.
                # The current generate_simple_target_path just appends the filename it receives.
                # So, if `filename` is "render.[1-10].exr", the path will end with that.
                # If `filename` is "render.%04d.exr", path will end with that. This is usually desired for previews.
                generated_seq_path = _get_generated_path_string(filename) 
                if generated_seq_path.startswith("Error:"):
                    return generated_seq_path # Propagate error
                return generated_seq_path  # Return clean path without preview text
            except Exception as e:
                print(f"[MappingGenerator] Exception during path preview for sequence '{filename}': {e}")
                # self.logger.error(f"Exception generating path preview for sequence '{filename}': {e}", exc_info=True) # If logger
                return f"Error: Exception generating path preview for sequence '{filename}'."
        else:
            print(f"[MappingGenerator] Error: Unsupported item type '{item_type}' for path preview.")
            return f"Error: Unsupported item type '{item_type}'."
