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
            config_path = script_dir / "src" / "config" / "patterns.json"
        self.config = load_config(config_path)
        self.shot_patterns = [
            pattern
            for pattern in self.config.get("shotPatterns", [])
        ]
        self.task_patterns = self.config.get("taskPatterns", {})
        self.resolution_patterns = self.config.get("resolutionPatterns", [])
        self.version_patterns = [
            pattern
            for pattern in self.config.get("versionPatterns", [])
        ]
        self.max_depth = 10
        self.current_frame_numbers = []  # Initialize frame numbers storage

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
        asset_patterns = self.config.get("assetPatterns", [])
        return extract_asset_simple(filename, asset_patterns)

    def _extract_stage_simple(self, filename: str) -> str:
        # IMPORTANT: Only use patterns from patterns.json, only search filename
        stage_patterns = self.config.get("stagePatterns", [])
        return extract_stage_simple(filename, stage_patterns)


    def _create_sequence_mapping(self, sequence, full_profile_data: Dict[str, Any], root_output_dir: str, original_base_name=None):
        # 'full_profile_data' is the complete profile dictionary, e.g., {"name": ..., "rules": ...}
        # Fetch asset and stage patterns from self.config as they are not direct attributes
        asset_patterns = self.config.get("assetPatterns", [])
        stage_patterns = self.config.get("stagePatterns", [])

        # The underlying mapping_utils.create_sequence_mapping function will be updated
        # to expect the full profile dictionary as 'profile'.
        return create_sequence_mapping(
            sequence=sequence,
            profile=full_profile_data, # Pass the full profile dictionary
            root_output_dir=root_output_dir,
            original_base_name=original_base_name,
            extract_shot_simple=extract_shot_simple, # These are function references
            extract_task_simple=extract_task_simple,
            extract_version_simple=extract_version_simple,
            extract_resolution_simple=extract_resolution_simple,
            extract_asset_simple=extract_asset_simple,
            extract_stage_simple=extract_stage_simple,
            generate_simple_target_path=generate_simple_target_path,
            extract_sequence_info=extract_sequence_info,
            current_frame_numbers=self.current_frame_numbers,
            # Pass the MappingGenerator's global patterns
            p_shot=self.shot_patterns,
            p_task=self.task_patterns,
            p_version=self.version_patterns,
            p_resolution=self.resolution_patterns,
            p_asset=asset_patterns, # Pass the fetched asset_patterns
            p_stage=stage_patterns  # Pass the fetched stage_patterns
        )

    def _create_simple_mapping(self, node, profile, root_output_dir: str):
        # Fetch asset and stage patterns from self.config as they are not direct attributes
        asset_patterns = self.config.get("assetPatterns", [])
        stage_patterns = self.config.get("stagePatterns", [])

        return create_simple_mapping(
            node=node,
            profile_rules=profile, # 'profile' here is the list of rules
            root_output_dir=root_output_dir,
            extract_shot_simple=extract_shot_simple,
            extract_task_simple=extract_task_simple,
            extract_version_simple=extract_version_simple,
            extract_resolution_simple=extract_resolution_simple,
            extract_asset_simple=extract_asset_simple,
            extract_stage_simple=extract_stage_simple,
            # Pass MappingGenerator's global patterns
            p_shot=self.shot_patterns,
            p_task=self.task_patterns,
            p_version=self.version_patterns,
            p_resolution=self.resolution_patterns,
            p_asset=asset_patterns,
            p_stage=stage_patterns
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
        # 'profile' is now expected to be a dictionary, e.g., {"name": "ProfileName", "rules": [...list_of_rules...]}
        
        # The core mapping_utils.generate_mappings function expects the full profile dictionary
        # to access things like profile name for logging, etc.
        
        # However, the internal _create_simple_mapping and _create_sequence_mapping methods
        # (and their callees like create_simple_mapping.py) expect just the list of rules.
        # So, we extract profile['rules'] for the lambdas.
        
        rules_list = profile.get('rules', [])
        if not isinstance(rules_list, list):
            # This should ideally be caught earlier (e.g., in GuiNormalizerAdapter),
            # but as a safeguard to prevent unexpected errors deep in the call stack.
            raise ValueError(
                f"Profile dictionary passed to MappingGenerator.generate_mappings is missing a 'rules' key, "
                f"or 'rules' is not a list. Profile keys: {list(profile.keys())}"
            )

        # Ensure status_callback from kwargs is prioritized if explicitly passed,
        # otherwise use the one from the signature.
        actual_status_callback = kwargs.pop('status_callback', status_callback)

        return generate_mappings(
        tree=tree,
        profile=profile,  # Pass the full profile dictionary here
        batch_id=batch_id,
        group_image_sequences=self._group_image_sequences,
        extract_sequence_info=self._extract_sequence_info,
        is_network_path=is_network_path,
        # Lambdas now receive the full profile dict as 'prof_dict'.
        # _create_sequence_mapping will receive the full prof_dict.
        # _create_simple_mapping still expects only the rules list for now.
        create_sequence_mapping=lambda seq, prof_dict, orig_base_name: self._create_sequence_mapping(seq, prof_dict, root_output_dir, orig_base_name),
        create_simple_mapping=lambda node, prof_dict: self._create_simple_mapping(node, prof_dict['rules'], root_output_dir),
        finalize_sequences=self._finalize_sequences,
        status_callback=actual_status_callback, # Pass it here
        **kwargs # Pass remaining kwargs
    )

    def _init_patterns_from_profile(self, profile):
        return init_patterns_from_profile(self, profile)
