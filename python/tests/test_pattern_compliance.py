"""
Test for compliance with IMPORTANT.md patterns requirements.

This test ensures that:
1. All extraction functions fail gracefully if required patterns are missing from patterns.json
2. No path components are used in pattern searches (only filenames)
3. All pattern loading comes exclusively from patterns.json
"""

import os
import sys
import unittest
import json
from unittest.mock import patch, MagicMock

# Add parent directory to path to import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from mapping_utils.shot_extractor import extract_shot_simple
from mapping_utils.task_extractor import extract_task_simple
from mapping_utils.version_extractor import extract_version_simple
from mapping_utils.resolution_extractor import extract_resolution_simple
from mapping_utils.asset_extractor import extract_asset_simple
from mapping_utils.stage_extractor import extract_stage_simple
from mapping_utils.init_patterns_from_profile import init_patterns_from_profile


class TestPatternCompliance(unittest.TestCase):
    """Tests to ensure compliance with IMPORTANT.md pattern requirements."""

    def test_extractors_use_only_filename(self):
        """Test that all extractors only use filename, not path."""
        # Create test data
        filename = "shot_001_v001_2k.exr"
        path = "/path/to/some/folder/with/shot_003/comp/shot_003_v002_4k.exr"

        # Mock patterns
        shot_patterns = [r"shot_\d{3}"]
        task_patterns = {"comp": ["comp"]}
        version_patterns = [r"v\d{3}"]
        resolution_patterns = [r"\d{1,2}k"]
        asset_patterns = ["asset"]
        stage_patterns = ["stage"]

        # Compile regex patterns where needed
        import re
        shot_patterns = [re.compile(p) for p in shot_patterns]
        version_patterns = [re.compile(p) for p in version_patterns]

        # Test each extractor
        # Shot extractor should find shot_001 in filename, not shot_003 in path
        result = extract_shot_simple(filename, path, shot_patterns)
        self.assertEqual(result, "shot_001", 
                        "Shot extractor used path component instead of only filename")

        # Task extractor should return None since "comp" is only in path, not filename
        result = extract_task_simple(filename, path, task_patterns)
        self.assertIsNone(result, 
                         "Task extractor used path component instead of only filename")

        # Version extractor only takes filename, so it should find v001
        result = extract_version_simple(filename, version_patterns)
        self.assertEqual(result, "v001", 
                        "Version extractor didn't correctly extract from filename")

        # Resolution extractor should find 2k in filename, not 4k in path
        result = extract_resolution_simple(filename, path, resolution_patterns)
        self.assertEqual(result, "2k", 
                        "Resolution extractor used path component instead of only filename")

        # Asset and stage extractors should return default values since patterns don't match
        result = extract_asset_simple(filename, asset_patterns)
        self.assertEqual(result, "unmatched", 
                        "Asset extractor didn't return default for non-matching filename")

        result = extract_stage_simple(filename, stage_patterns)
        self.assertEqual(result, "unmatched", 
                        "Stage extractor didn't return default for non-matching filename")

    def test_extractors_fail_gracefully_with_empty_patterns(self):
        """Test that all extractors fail gracefully if patterns are missing."""
        filename = "shot_001_v001_2k.exr"
        path = ""  # Empty path, as per IMPORTANT.md

        # Test with empty patterns
        result = extract_shot_simple(filename, path, [])
        self.assertIsNone(result, "Shot extractor didn't fail gracefully with empty patterns")

        result = extract_task_simple(filename, path, {})
        self.assertIsNone(result, "Task extractor didn't fail gracefully with empty patterns")

        result = extract_version_simple(filename, [])
        self.assertIsNone(result, "Version extractor didn't fail gracefully with empty patterns")

        result = extract_resolution_simple(filename, path, [])
        self.assertIsNone(result, "Resolution extractor didn't fail gracefully with empty patterns")

        result = extract_asset_simple(filename, [])
        self.assertEqual(result, "unmatched", "Asset extractor didn't fail gracefully with empty patterns")

        result = extract_stage_simple(filename, [])
        self.assertEqual(result, "unmatched", "Stage extractor didn't fail gracefully with empty patterns")

    @patch('builtins.open')
    def test_init_patterns_uses_only_config(self, mock_open):
        """Test that init_patterns_from_profile uses only patterns.json, not profile patterns."""
        # Mock configuration from patterns.json
        mock_config = {
            "shotPatterns": ["shot_\\d{3}"],
            "taskPatterns": {"comp": ["comp", "composite"]},
            "resolutionPatterns": ["\\d{1,2}k"],
            "versionPatterns": ["v\\d{3}"]
        }
        
        # Mock profile with conflicting patterns (should be ignored)
        mock_profile = {
            "name": "Test Profile",
            "userPatterns": {
                "shotNames": ["different_shot"],
                "resolutions": ["different_res"],
                "tasks": [{"name": "different_task", "aliases": ["diff"]}]
            }
        }
        
        # Mock mapping generator
        mapping_generator = MagicMock()
        mapping_generator.config = mock_config
        
        # Run init_patterns_from_profile
        init_patterns_from_profile(mapping_generator, mock_profile)
        
        # Verify that only patterns from config (patterns.json) were used
        for call in mapping_generator.mock_calls:
            name, args, kwargs = call
            if name == '__setattr__':
                attr_name, value = args
                if attr_name == 'shot_patterns':
                    # Should contain patterns from mock_config, not mock_profile
                    self.assertTrue(all('shot_\\d{3}' in p.pattern for p in value))
                elif attr_name == 'task_patterns':
                    # Should contain task patterns from mock_config, not mock_profile
                    self.assertEqual(list(value.keys()), ['comp'])
                    self.assertEqual(value['comp'], ['comp', 'composite'])


if __name__ == '__main__':
    unittest.main()
