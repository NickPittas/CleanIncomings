import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.resolve()))
import pytest
from mapping import MappingGenerator

def test_create_sequence_mapping_handles_missing_codes():
    mg = MappingGenerator(config_path="../src/config/patterns.json")
    dummy_sequence = {
        "files": ["OLNT0010_imags_beauty_LL1804k_ACEScgLin_PREVIZ_v022.2784.exr"],
        "base_name": "OLNT0010_imags_beauty_LL1804k_ACEScgLin_PREVIZ_v022",
        "suffix": ".exr",
        "frame_range": "2784-2784",
        "frame_count": 1,
        "directory": ".",
        "extension": "exr"
    }
    profile = {}
    result = mg._create_sequence_mapping(dummy_sequence, profile)
    # Check that all fields are present and no NameError occurs
    for key in ["shot", "asset", "stage", "task", "version", "resolution"]:
        assert key in result or key in result.get('node', {})
    # Should not raise NameError or KeyError
