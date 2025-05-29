import unittest
import os
import sys

# Adjust path to import from the parent 'python' directory
# This assumes 'tests' is a sibling to 'python' and 'src'
# and the script is run from the project root (CleanIncomings)
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
PYTHON_DIR = os.path.join(PROJECT_ROOT, 'python')
if PYTHON_DIR not in sys.path:
    sys.path.insert(0, PYTHON_DIR)

# Ensure the main project root is also in sys.path for potential top-level imports if needed
# This is useful if 'python' is a package and tests are run as modules.
if PROJECT_ROOT not in sys.path: # Add CleanIncomings root
    sys.path.insert(0, PROJECT_ROOT)


from mapping_utils.generate_simple_target_path import generate_simple_target_path, DEFAULT_FOOTAGE_KEYWORDS

class TestGenerateSimpleTargetPath(unittest.TestCase):

    def setUp(self):
        # Rules based on "Simple Project" from profiles.json
        self.sample_profile_rules = [
            {"3D/Renders": [
                "3d", "albedo", "beauty", "bump", "depth", "diffuse", "displacement", "emission", "lighting", "metallic", "normal", "objectid", "occlusion", "position", "refraction", "rgb", "roughness", "specular", "sss", "volume",
                "main_arch", "second_arch", "hero", "background", "vehicle", "character", "prop", "env", "fx", "matte", "crowd", "imags",
                "PREVIZ", "FINAL", "ANIM", "LAYOUT", "BLOCK", "LIGHT", "RENDER", "cryptomatte", "puzzle", "emissive", "velocity"
            ]},
            {"Projects/Nuke": [
                "COMP", "CLEANUP"
            ]},
            {"Video/Footage": [
                "MAIN", "footage", "source", "video", "plate", "plates",
                "DELIVERY"
            ]}
        ]
        self.root_output_dir = "D:\\New_folder"
        self.filename = "test_file_v001.exr"

    def test_simple_task_match(self):
        """Test path generation with a direct task match (case-insensitive)."""
        result = generate_simple_target_path(
            root_output_dir=self.root_output_dir,
            profile_rules=self.sample_profile_rules,
            filename=self.filename,
            parsed_shot="SHOT001",
            parsed_task="Beauty", 
            parsed_asset="MainChar",
            parsed_stage="ANIM",
            parsed_version="v001",
            parsed_resolution="1920x1080"
        )
        expected_base = os.path.join(self.root_output_dir, "3D/Renders") # Updated to match profile key
        expected_path = os.path.join(
            expected_base,
            "shot001",
            "anim",
            "beauty",
            "mainchar",
            "1920x1080",
            "v001",
            self.filename
        )
        self.assertEqual(os.path.normpath(result["target_path"]), os.path.normpath(expected_path))
        self.assertFalse(result["used_default_footage_rule"])
        self.assertFalse(result["ambiguous_match"])

    def test_asset_match_when_task_no_match(self):
        """Test path generation with an asset match when task does not match higher priority rules."""
        # Uses self.sample_profile_rules which is "Simple Project"
        # We expect "Video/Footage" to be matched due to "plateAsset" (containing "plate"),
        # as "UnmatchedTask" should not match "3D/Renders" or "Projects/Nuke".
        filename_to_test = "shot002_UnmatchedTask_plateAsset_v001.exr"
        result = generate_simple_target_path(
            root_output_dir=self.root_output_dir,
            profile_rules=self.sample_profile_rules, # Using the main profile
            filename=filename_to_test,
            parsed_shot="SHOT002",
            parsed_task="UnmatchedTask", 
            parsed_asset="plate", 
            parsed_stage=None,
            parsed_version="v001",
            parsed_resolution=None
        )
        expected_base = os.path.join(self.root_output_dir, "Video/Footage") # Matched due to 'plate' in asset
        expected_path = os.path.join(
            expected_base,
            "shot002",
            "unmatchedtask", # task is still part of the path
            "plate",    # asset is part of the path, now exact match
            "v001",
            filename_to_test
        )
        self.assertEqual(os.path.normpath(result["target_path"]), os.path.normpath(expected_path))
        self.assertFalse(result["used_default_footage_rule"])

    def test_default_to_footage_rule_no_match(self):
        """Test defaulting to footage rule when no task or asset matches."""
        result = generate_simple_target_path(
            root_output_dir=self.root_output_dir,
            profile_rules=self.sample_profile_rules,
            filename="unknown_clip_001.mov",
            parsed_shot="SC003",
            parsed_task="UNKNOWN_TASK",
            parsed_asset="UNKNOWN_ASSET",
            parsed_stage=None,
            parsed_version=None,
            parsed_resolution=None
        )
        # "Video/Footage" rule in "Simple Project" profile contains DEFAULT_FOOTAGE_KEYWORDS
        expected_base = os.path.join(self.root_output_dir, "Video/Footage") 
        expected_path = os.path.join(
            expected_base,
            "sc003",
            "unknown_task",
            "unknown_asset",
            "unknown_clip_001.mov"
        )
        self.assertEqual(os.path.normpath(result["target_path"]), os.path.normpath(expected_path))
        self.assertTrue(result["used_default_footage_rule"])

    def test_path_all_segments_present(self):
        """Test path with all dynamic segments present and correct order/casing."""
        result = generate_simple_target_path(
            root_output_dir=self.root_output_dir,
            profile_rules=self.sample_profile_rules,
            filename=self.filename,
            parsed_shot="SHOT001",
            parsed_task="Beauty",
            parsed_asset="MainChar",
            parsed_stage="ANIM",
            parsed_version="v001",
            parsed_resolution="1920x1080"
        )
        expected_base = os.path.join(self.root_output_dir, "3D/Renders") # Updated to match profile key
        expected_path = os.path.join(
            expected_base,
            "shot001",      
            "anim",         
            "beauty",       
            "mainchar",     
            "1920x1080",    
            "v001",         
            self.filename
        )
        self.assertEqual(os.path.normpath(result["target_path"]), os.path.normpath(expected_path))

    def test_path_some_segments_missing(self):
        """Test path generation when some dynamic segments are None or empty."""
        result = generate_simple_target_path(
            root_output_dir=self.root_output_dir,
            profile_rules=self.sample_profile_rules,
            filename="short_file_v01.exr",
            parsed_shot="SHOT004",
            parsed_task="cryptomatte", 
            parsed_asset=None,    
            parsed_stage="",       
            parsed_version="v01",
            parsed_resolution=None 
        )
        # "cryptomatte" is in "3D/Renders" rule in "Simple Project" profile
        expected_base = os.path.join(self.root_output_dir, "3D/Renders") 
        expected_path = os.path.join(
            expected_base,
            "shot004",
            "cryptomatte", # task is part of the path, now exact match
            "v01",
            "short_file_v01.exr"
        )
        self.assertEqual(os.path.normpath(result["target_path"]), os.path.normpath(expected_path))
        self.assertFalse(result["used_default_footage_rule"])

    def test_no_explicit_footage_rule_fallback(self):
        """Test fallback to 'unmapped_footage' if no explicit footage rule is defined."""
        profile_no_footage_rule = [
            {os.path.join("3D", "Renders", "Beauty"): ["beauty"]}
        ]
        result = generate_simple_target_path(
            root_output_dir=self.root_output_dir,
            profile_rules=profile_no_footage_rule,
            filename="some_video.mp4",
            parsed_shot="SHOT005",
            parsed_task="RANDOM",
            parsed_asset="RANDOM_ASSET",
            parsed_stage=None,
            parsed_version=None,
            parsed_resolution=None
        )
        expected_base = os.path.join(self.root_output_dir, "unmapped_footage")
        expected_path = os.path.join(
            expected_base,
            "shot005",
            "random",
            "random_asset",
            "some_video.mp4"
        )
        self.assertEqual(os.path.normpath(result["target_path"]), os.path.normpath(expected_path))
        self.assertTrue(result["used_default_footage_rule"])

    # --- Tests for Ambiguity --- 

    def test_ambiguous_match_task_multiple_keywords(self):
        """Test ambiguous match when task contains multiple keywords mapping to different paths."""
        ambiguous_profile_rules = [
            {"Renders/Beauty": ["beauty", "rgb"]},
            {"FX/SpecialEffects": ["fx", "particles"]},
            {"Video/Footage": DEFAULT_FOOTAGE_KEYWORDS}
        ]
        result = generate_simple_target_path(
            root_output_dir=self.root_output_dir,
            profile_rules=ambiguous_profile_rules,
            filename="shot01_beauty_fx_pass_v01.exr",
            parsed_shot="SHOT01",
            parsed_task="beauty_fx", # Contains "beauty" and "fx"
            parsed_asset="someAsset",
            parsed_stage=None, parsed_version="v01", parsed_resolution=None
        )
        self.assertTrue(result["ambiguous_match"])
        self.assertIsNone(result["target_path"])
        self.assertFalse(result["used_default_footage_rule"])
        expected_options = sorted([
            {"keyword": "beauty", "path": "Renders/Beauty"},
            {"keyword": "fx", "path": "FX/SpecialEffects"}
        ], key=lambda x: x["keyword"])
        self.assertEqual(result["ambiguous_options"], expected_options)

    def test_ambiguous_match_asset_multiple_keywords(self):
        """Test ambiguous match from asset when task doesn't match or is not ambiguous."""
        ambiguous_profile_rules = [
            {"Props/Models": ["model", "prop"]},
            {"Textures/Surfaces": ["surface", "texture"]},
            {"Video/Footage": DEFAULT_FOOTAGE_KEYWORDS}
        ]
        result = generate_simple_target_path(
            root_output_dir=self.root_output_dir,
            profile_rules=ambiguous_profile_rules,
            filename="asset_model_surface_tex_v01.fbx",
            parsed_shot="ASSET01",
            parsed_task="genericTask", # Does not match any rule directly
            parsed_asset="model_surface", # Contains "model" and "surface"
            parsed_stage=None, parsed_version="v01", parsed_resolution=None
        )
        self.assertTrue(result["ambiguous_match"])
        self.assertIsNone(result["target_path"])
        self.assertFalse(result["used_default_footage_rule"])
        expected_options = sorted([
            {"keyword": "model", "path": "Props/Models"},
            {"keyword": "surface", "path": "Textures/Surfaces"}
        ], key=lambda x: x["keyword"])
        self.assertEqual(result["ambiguous_options"], expected_options)

    def test_no_ambiguity_single_sub_keyword_match_falls_to_default(self):
        """Test that a single sub-keyword match (not a full token match) doesn't cause ambiguity and falls to default footage."""
        # This tests if the logic correctly distinguishes between true ambiguity (multiple paths) 
        # and just one sub-keyword being present in a token that doesn't fully match anything.
        # If 'beauty_pass' doesn't fully match any rule, and only 'beauty' sub-keyword is found, it's not ambiguous by itself.
        profile_rules = [
            {"Renders/Beauty": ["beauty"]}, # Only 'beauty' defined
            {"Video/Footage": DEFAULT_FOOTAGE_KEYWORDS}
        ]
        result = generate_simple_target_path(
            root_output_dir=self.root_output_dir,
            profile_rules=profile_rules,
            filename="shot02_beauty_pass_v01.exr",
            parsed_shot="SHOT02",
            parsed_task="beauty_pass", # Contains "beauty", but "beauty_pass" is not a keyword itself
            parsed_asset=None, parsed_stage=None, parsed_version="v01", parsed_resolution=None
        )
        self.assertFalse(result["ambiguous_match"], f"Ambiguity options: {result['ambiguous_options']}")
        self.assertTrue(result["used_default_footage_rule"])
        self.assertIsNotNone(result["target_path"])
        expected_base = os.path.join(self.root_output_dir, "Video/Footage")
        expected_path = os.path.join(expected_base, "shot02", "beauty_pass", "v01", "shot02_beauty_pass_v01.exr")
        self.assertEqual(os.path.normpath(result["target_path"]), os.path.normpath(expected_path))
        self.assertEqual(result["ambiguous_options"], [])

    def test_no_ambiguity_exact_full_token_match_overrides_sub_keywords(self):
        """Test that an exact full token match takes precedence and doesn't trigger ambiguity even if sub-keywords exist."""
        profile_rules = [
            {"Renders/BeautyFX": ["beauty_fx"]}, # Exact rule for "beauty_fx"
            {"Renders/Beauty": ["beauty"]},
            {"FX/SpecialEffects": ["fx"]},
            {"Video/Footage": DEFAULT_FOOTAGE_KEYWORDS}
        ]
        result = generate_simple_target_path(
            root_output_dir=self.root_output_dir,
            profile_rules=profile_rules,
            filename="shot03_beauty_fx_specific_v01.exr",
            parsed_shot="SHOT03",
            parsed_task="beauty_fx", # Exact match, also contains "beauty" and "fx"
            parsed_asset=None, parsed_stage=None, parsed_version="v01", parsed_resolution=None
        )
        self.assertFalse(result["ambiguous_match"], f"Ambiguity options: {result['ambiguous_options']}")
        self.assertFalse(result["used_default_footage_rule"])
        self.assertIsNotNone(result["target_path"])
        expected_base = os.path.join(self.root_output_dir, "Renders/BeautyFX")
        expected_path = os.path.join(expected_base, "shot03", "beauty_fx", "v01", "shot03_beauty_fx_specific_v01.exr")
        self.assertEqual(os.path.normpath(result["target_path"]), os.path.normpath(expected_path))
        self.assertEqual(result["ambiguous_options"], [])

    def test_no_ambiguity_no_keywords_present(self):
        """Test that no ambiguity is flagged when task/asset contain no known keywords."""
        profile_rules = [
            {"Renders/Beauty": ["beauty"]},
            {"Video/Footage": DEFAULT_FOOTAGE_KEYWORDS}
        ]
        result = generate_simple_target_path(
            root_output_dir=self.root_output_dir,
            profile_rules=profile_rules,
            filename="shot04_random_stuff_v01.exr",
            parsed_shot="SHOT04",
            parsed_task="random_stuff",
            parsed_asset="other_things",
            parsed_stage=None, parsed_version="v01", parsed_resolution=None
        )
        self.assertFalse(result["ambiguous_match"], f"Ambiguity options: {result['ambiguous_options']}")
        self.assertTrue(result["used_default_footage_rule"])
        self.assertIsNotNone(result["target_path"])
        self.assertEqual(result["ambiguous_options"], [])

    def test_no_explicit_footage_rule_fallback(self):
        """Test fallback to 'unmapped_footage' if no explicit footage rule is defined."""
        profile_no_footage_rule = [
            {os.path.join("3D", "Renders", "Beauty"): ["beauty"]}
        ]
        result = generate_simple_target_path(
            root_output_dir=self.root_output_dir,
            profile_rules=profile_no_footage_rule,
            filename="some_video.mp4",
            parsed_shot="SHOT005",
            parsed_task="RANDOM",
            parsed_asset="RANDOM_ASSET",
            parsed_stage=None,
            parsed_version=None,
            parsed_resolution=None
        )
        expected_base = os.path.join(self.root_output_dir, "unmapped_footage")
        expected_path = os.path.join(
            expected_base,
            "shot005",
            "random",
            "random_asset",
            "some_video.mp4"
        )
        self.assertEqual(os.path.normpath(result["target_path"]), os.path.normpath(expected_path))
        self.assertTrue(result["used_default_footage_rule"])

    def test_profile_rule_order_priority(self):
        """Test that the first matching rule in the profile is used."""
        profile_ordered_rules = [
            {os.path.join("General", "TaskMatch"): ["rend", "render"]}, 
            {os.path.join("Specific", "RenderTask"): ["render"]}     
        ]
        result = generate_simple_target_path(
            root_output_dir=self.root_output_dir,
            profile_rules=profile_ordered_rules,
            filename="test_render_v01.exr",
            parsed_shot="SHOT006",
            parsed_task="RENDER",
            parsed_asset="TestAsset",
            parsed_stage=None, parsed_version="v01", parsed_resolution=None
        )
        expected_base = os.path.join(self.root_output_dir, "General", "TaskMatch")
        expected_path = os.path.join(expected_base, "shot006", "render", "testasset", "v01", "test_render_v01.exr")
        self.assertEqual(os.path.normpath(result["target_path"]), os.path.normpath(expected_path))
        self.assertFalse(result["used_default_footage_rule"])

if __name__ == '__main__':
    unittest.main()
