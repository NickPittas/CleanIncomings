import unittest
import tempfile
from unittest.mock import MagicMock, patch, call, PropertyMock, mock_open
import os
import sys
from pathlib import Path
import time
import json

# Adjust the path to import modules from the parent directory
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from python.gui_normalizer_adapter import GuiNormalizerAdapter

class TestGuiNormalizerAdapter(unittest.TestCase):

    def setUp(self):
        """Set up for test methods using manual patching."""


        # Patch MappingGenerator in gui_normalizer_adapter module
        patcher_mapping_generator = patch('python.gui_normalizer_adapter.MappingGenerator')
        self.MockMappingGenerator = patcher_mapping_generator.start()
        self.addCleanup(patcher_mapping_generator.stop)

        # Patch FileSystemScanner in gui_normalizer_adapter module
        patcher_file_system_scanner = patch('python.gui_normalizer_adapter.FileSystemScanner')
        self.MockFileSystemScanner = patcher_file_system_scanner.start()
        self.addCleanup(patcher_file_system_scanner.stop)

        # Create a temporary directory for config_dir_path for the adapter that persists for the test
        self.temp_config_dir_obj = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_config_dir_obj.cleanup)
        self.test_config_dir = Path(self.temp_config_dir_obj.name) # Ensure this is a pathlib.Path object

        # Define expected paths as pathlib.Path objects
        self.patterns_json_path = self.test_config_dir / "patterns.json"
        self.profiles_json_path = self.test_config_dir / "profiles.json"
        # self.rules_json_path is not directly used by GuiNormalizerAdapter.__init__ directly but by MappingGenerator

        # Define content for the temporary JSON files
        profiles_content_for_file = {
            "Test Profile": {
                "name": "Test Profile",
                "rules": [],  # Add empty rules list as per adapter's expectation
                "rules_file": "test_profile_rules.json",
                "vfx_root": "/test/vfx",
                "description": "A test profile written to a temporary file for setUp."
            }
        }
        patterns_content_for_file = {  # Minimal valid patterns.json
            "sequences": [],
            "single_files": []
        }
        rules_content_for_file = {  # Content for test_profile_rules.json
            "rules": [
                {"name": "Sample Rule from File", "pattern": ".*", "task": "SAMPLE_TASK", "fields": {}}
            ]
        }

        # Write the temporary JSON files
        with open(self.profiles_json_path, 'w', encoding='utf-8') as f:
            json.dump(profiles_content_for_file, f, indent=4)
        
        with open(self.patterns_json_path, 'w', encoding='utf-8') as f:
            json.dump(patterns_content_for_file, f, indent=4)

        # Create the rules file referenced in profiles.json
        test_profile_rules_json_path_local = self.test_config_dir / "test_profile_rules.json"
        with open(test_profile_rules_json_path_local, 'w', encoding='utf-8') as f:
            json.dump(rules_content_for_file, f, indent=4)

        self.adapter = GuiNormalizerAdapter(config_dir_path=str(self.test_config_dir))
        
        # Common mock instance setup for scanner
        mock_scanner_instance_for_setup = self.MockFileSystemScanner.return_value
        mock_scanner_instance_for_setup._override_tree_to_produce = None 
        mock_scanner_instance_for_setup._last_batch_id_passed_to_scan = 'default_setup_batch_id'
        mock_scanner_instance_for_setup._default_tree = {'name': 'default_setup_tree', 'type': 'folder', 'children': []}
        # Configure the mock scanner to allow empty root results for tests that expect success with such a tree
        # Use PropertyMock attached to the type of the instance for robust property mocking
        prop_mock_allows_empty = PropertyMock(return_value=True)
        type(mock_scanner_instance_for_setup).allows_empty_root_scan_result = prop_mock_allows_empty

        def actual_scan_dir_side_effect_debug(*args, **kwargs):
            # print(f"DEBUG_SIDE_EFFECT (scan_dir) Instance ID: {id(mock_scanner_instance_for_setup)}")
            # print(f"DEBUG_SIDE_EFFECT (scan_dir) called with ARGS={args}, KWARGS={kwargs}")
            
            if not args:
                raise TypeError("actual_scan_dir_side_effect_debug missing base_path.")
            # base_path_arg = args[0]
            batch_id_from_adapter_arg = kwargs.get('batch_id')
            if batch_id_from_adapter_arg is None:
                raise TypeError("actual_scan_dir_side_effect_debug missing 'batch_id'.")

            # Store the batch_id that was passed in for get_scan_progress to use
            mock_scanner_instance_for_setup._last_batch_id_passed_to_scan = batch_id_from_adapter_arg

            tree_to_return = mock_scanner_instance_for_setup._override_tree_to_produce if mock_scanner_instance_for_setup._override_tree_to_produce is not None else mock_scanner_instance_for_setup._default_tree
            
            # print(f"DEBUG_SIDE_EFFECT (scan_dir) _override_tree_to_produce: {mock_scanner_instance_for_setup._override_tree_to_produce}")
            # print(f"DEBUG_SIDE_EFFECT (scan_dir) Returning tree: {tree_to_return}, batch_id: {batch_id_from_adapter_arg}")
            return batch_id_from_adapter_arg, tree_to_return

        mock_scanner_instance_for_setup.scan_directory_with_progress.side_effect = actual_scan_dir_side_effect_debug
        mock_scanner_instance_for_setup.scan_directory_with_progress.return_value = None # Side effect handles return

        def mock_get_scan_progress_side_effect_debug(*args_get, **kwargs_get):
            # print(f"DEBUG_SIDE_EFFECT (get_scan_progress) Instance ID: {id(mock_scanner_instance_for_setup)}")
            # print(f"DEBUG_SIDE_EFFECT (get_scan_progress) Args received: args_get={args_get}, kwargs_get={kwargs_get}")

            requested_batch_id = None
            if args_get: # Check if there are any positional arguments
                requested_batch_id = args_get[0] # batch_id is passed as the first positional argument by the adapter
            elif kwargs_get.get('batch_id'): # Fallback if it were passed as a keyword (not current adapter behavior)
                # print(f"INFO_SIDE_EFFECT (get_scan_progress): batch_id found in kwargs_get.")
                requested_batch_id = kwargs_get.get('batch_id')
            else:
                # This case should ideally not be reached if adapter always passes batch_id
                # print(f"WARNING_SIDE_EFFECT (get_scan_progress): batch_id not found in args or kwargs, falling back to _last_batch_id_passed_to_scan.")
                requested_batch_id = mock_scanner_instance_for_setup._last_batch_id_passed_to_scan

            current_tree = mock_scanner_instance_for_setup._override_tree_to_produce if mock_scanner_instance_for_setup._override_tree_to_produce is not None else mock_scanner_instance_for_setup._default_tree
            batch_id_to_return = requested_batch_id

            # print(f"DEBUG_SIDE_EFFECT (get_scan_progress) _override_tree_to_produce: {mock_scanner_instance_for_setup._override_tree_to_produce}")
            # print(f"DEBUG_SIDE_EFFECT (get_scan_progress) Batch_id determined to return: {batch_id_to_return}")
            # print(f"DEBUG_SIDE_EFFECT (get_scan_progress) Returning tree for 'result.tree': {current_tree}")
            return {
                'status': 'completed',
                'progress': 100,
                'message': 'Scan complete',
                'batch_id': batch_id_to_return, # batch_id is top-level
                'result': { # Nested result dictionary
                    'tree': current_tree, # Renamed from tree_structure and nested
                    'error': None, # Nested
                    'processed_files': 10, # Nested
                    'total_files': 10 # Nested
                    # Ensure all fields used by adapter from scan_result are here
                }
            }
        mock_scanner_instance_for_setup.get_scan_progress.side_effect = mock_get_scan_progress_side_effect_debug
        mock_scanner_instance_for_setup.get_scan_progress.return_value = None # Side effect handles return

    def test_scan_and_normalize_structure_success_with_status_callback(self):
        """Test successful scan and normalization with status_callback interactions."""
        mock_scanner_instance = self.MockFileSystemScanner.return_value
        # Set the tree this mock scan should "produce" for this test
        mock_scanner_instance._override_tree_to_produce = {'name': 'root', 'type': 'folder', 'children': []}
        # The batch_id will be generated by the adapter and passed to scan_directory_with_progress.
        # Our mock side_effect for scan_directory_with_progress will capture it and make it available
        # to the get_scan_progress side_effect.
        
        mock_mapping_generator_instance = self.MockMappingGenerator.return_value
        mock_mapping_generator_instance.generate_mappings.return_value = [
            {'id': 'proposal1', 'status': 'auto', 'source_path': '/fake/source/file.exr', 'destination_path': '/fake/dest/file.exr'}
        ]

        mock_status_cb = MagicMock()

        proposals = self.adapter.scan_and_normalize_structure(
            base_path='/fake/source',
            profile_name='Test Profile',
            destination_root='/fake/dest',
            status_callback=mock_status_cb
        )

        self.assertEqual(len(proposals), 1)
        self.assertEqual(proposals[0]['id'], 'proposal1')

        # Get the actual profile config used by the scanner call
        print(f"DEBUG_TEST_METHOD: self.adapter.all_profiles_data = {self.adapter.all_profiles_data}")
        expected_profile_config = self.adapter.all_profiles_data.get('Test Profile')
        if expected_profile_config is None:
            self.fail("Test Profile not found in mock profiles data during test_scan_and_normalize_structure_success_with_status_callback setup.")
        expected_rules_file_path = self.test_config_dir / expected_profile_config['rules_file']

        self.MockFileSystemScanner.return_value.scan_directory_with_progress.assert_called_once_with(
            '/fake/source',  # Pass base_path positionally
            batch_id=unittest.mock.ANY
        )
        
        self.MockMappingGenerator.assert_called_once_with(config_path=str(self.patterns_json_path))
        mock_mapping_generator_instance.generate_mappings.assert_called_once()
        args, kwargs = mock_mapping_generator_instance.generate_mappings.call_args
        self.assertEqual(kwargs.get('tree'), {'name': 'root', 'type': 'folder', 'children': []})
        self.assertEqual(kwargs.get('profile')['name'], 'Test Profile') 
        self.assertEqual(kwargs.get('root_output_dir'), '/fake/dest')
        self.assertEqual(kwargs.get('status_callback'), mock_status_cb)
        self.assertIsNotNone(kwargs.get('batch_id'))

        expected_calls = [
            call({'type': 'mapping_generation', 'data': {'status': 'starting', 'message': 'Starting mapping generation...'}}),
            call({'type': 'mapping_generation', 'data': {'status': 'completed', 'message': 'Mapping generation complete. Transforming results...'}}),
            call({'type': 'transformation', 'data': {'status': 'starting', 'message': 'Transforming proposals...'}}),
            call({'type': 'transformation', 'data': {'status': 'completed', 'message': 'Proposals transformed.'}})
        ]
        # Filter out internal mock method calls like __bool__ or __eq__
        actual_direct_calls = [c for c in mock_status_cb.mock_calls if c[0] == '']
        self.assertEqual(actual_direct_calls, expected_calls)
        self.assertGreaterEqual(mock_status_cb.call_count, len(expected_calls))

    def test_scan_and_normalize_structure_scanner_fails(self):
        """Test behavior when scanner raises an exception."""
        mock_scanner_instance = self.MockFileSystemScanner.return_value
        mock_scanner_instance.scan_directory_with_progress.side_effect = Exception("Scanner boom!")
        
        mock_status_cb = MagicMock()

        with self.assertRaisesRegex(Exception, "Scanner boom!"):
            self.adapter.scan_and_normalize_structure(
                base_path='/fake/source',
                profile_name='Test Profile',
                destination_root='/fake/dest',
                status_callback=mock_status_cb
            )
        self.MockMappingGenerator.return_value.generate_mappings.assert_not_called()

    def test_scan_and_normalize_structure_mapping_fails(self):
        """Test behavior when mapping generator raises an exception."""
        mock_scanner_instance = self.MockFileSystemScanner.return_value
        # Set the tree this mock scan should "produce" for this test
        mock_scanner_instance._override_tree_to_produce = {'name': 'root', 'type': 'folder', 'children': []}
        # The batch_id will be generated by the adapter and passed to scan_directory_with_progress.
        # Our mock side_effect for scan_directory_with_progress will capture it and make it available
        # to the get_scan_progress side_effect.
        
        mock_mapping_generator_instance = self.MockMappingGenerator.return_value
        mock_mapping_generator_instance.generate_mappings.side_effect = Exception("Mapping boom!")

        mock_status_cb = MagicMock()

        with self.assertRaisesRegex(Exception, "Mapping boom!"):
            self.adapter.scan_and_normalize_structure(
                base_path='/fake/source',
                profile_name='Test Profile',
                destination_root='/fake/dest',
                status_callback=mock_status_cb
            )
    # mock_status_cb.assert_any_call({'type': 'mapping_generation', 'data': {'status': 'starting', 'message': 'Preparing for mapping generation...'}})

if __name__ == '__main__':
    unittest.main()
