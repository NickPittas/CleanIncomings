import unittest
import json
import os
from unittest.mock import patch, mock_open

from config_loader import load_profile_from_file, ProfileNotFoundError, ProfilesFileNotFoundError

class TestConfigLoader(unittest.TestCase):

    def test_load_profile_successfully(self):
        mock_profiles_data = {
            "simple": {
                "name": "Simple Test Profile",
                "description": "A simple test profile with new structure.",
                "path_rules": {
                    "generic_render_path": [
                        "3d",
                        "Renders",
                        { "use_pattern": "shot" },
                        { "use_pattern": "task" }
                    ],
                    "generic_footage_path": [
                        "Videos",
                        "Footage"
                    ]
                },
                "task_path_mapping": {
                    "beauty": "generic_render_path",
                    "footage": "generic_footage_path"
                }
            },
            "advanced": {
                "name": "Advanced Test Profile",
                "description": "An advanced test profile with new structure.",
                "path_rules": {
                    "adv_vfx_path": [
                        "01_VFX",
                        { "use_pattern": "shot" },
                        { "use_pattern": "stage" }
                    ]
                },
                "task_path_mapping": {
                    "comp": "adv_vfx_path"
                }
            }
        }
        mock_json_string = json.dumps(mock_profiles_data)

        with patch('builtins.open', mock_open(read_data=mock_json_string)) as mocked_file, \
             patch('os.path.exists', return_value=True):
            profile = load_profile_from_file("simple")
            self.assertEqual(profile['name'], "Simple Test Profile") # Name from within the profile data
            self.assertIn('path_rules', profile)
            self.assertIn('generic_render_path', profile['path_rules'])
            self.assertIn('task_path_mapping', profile)
            self.assertEqual(profile['task_path_mapping']['beauty'], 'generic_render_path')
            
            # Verify the path used to open profiles.json is correct
            config_loader_actual_dir = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
            expected_open_argument = os.path.join(config_loader_actual_dir, '..', 'src', 'config', 'profiles.json')
            mocked_file.assert_called_once_with(expected_open_argument, 'r')

    def test_load_profile_not_found(self):
        mock_profiles_data = {
            "simple": {"name": "simple"}
        }
        mock_json_string = json.dumps(mock_profiles_data)
        with patch('builtins.open', mock_open(read_data=mock_json_string)), \
             patch('os.path.exists', return_value=True):
            with self.assertRaises(ProfileNotFoundError) as context:
                load_profile_from_file("non_existent_profile")
            self.assertIn("Profile 'non_existent_profile' not found", str(context.exception))

    def test_profiles_file_not_found(self):
        with patch('os.path.exists', return_value=False):
            with self.assertRaises(ProfilesFileNotFoundError) as context:
                load_profile_from_file("any_profile")
            # config_loader.py now uses os.path.normpath() in its error string.
            # PROFILES_PATH in config_loader.py is 'g:\My Drive\python\CleanIncomings\python\..\src\config\profiles.json'
            # os.path.normpath of that is 'g:\My Drive\python\CleanIncomings\src\config\profiles.json'
            # Construct this normalized path from the test file's location:
            # os.path.dirname(os.path.abspath(__file__)) is 'g:\My Drive\python\CleanIncomings\python\tests'
            # We need to go up two levels to 'g:\My Drive\python\CleanIncomings', then 'src\config\profiles.json'
            expected_normalized_path_in_error_msg = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'src', 'config', 'profiles.json'))
            self.assertIn(f"Profiles configuration file not found at: {expected_normalized_path_in_error_msg}", str(context.exception))

    def test_invalid_json_in_profiles_file(self):
        invalid_json_string = "this is not json"
        with patch('builtins.open', mock_open(read_data=invalid_json_string)), \
             patch('os.path.exists', return_value=True):
            with self.assertRaises(ValueError): # Changed from json.JSONDecodeError
                load_profile_from_file("any_profile")

if __name__ == '__main__':
    unittest.main()
