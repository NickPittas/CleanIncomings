import re
import sys
from typing import Dict, Any

def init_patterns_from_profile(mapping_generator, profile: Dict[str, Any]):
    """
    Initialize mapping patterns exclusively from patterns.json, not from profile.
    
    According to IMPORTANT.md guidelines:
    1. All patterns must come from patterns.json only
    2. Profiles are used strictly for folder structure and root path
    3. No pattern logic should remain in profile definition
    
    Args:
        mapping_generator: The mapping generator instance to update
        profile: Used only for logging, not for pattern extraction
    """
    print(f"Loading patterns from patterns.json for profile: {profile.get('name', 'Unknown')}", file=sys.stderr)
    
    # IMPORTANT: Only use patterns from patterns.json (mapping_generator.config)
    # Do NOT merge with profile patterns or use any hardcoded patterns
    
    # 1. Shot patterns - use ONLY from patterns.json
    shot_patterns_str = mapping_generator.config.get("shotPatterns", [])
    mapping_generator.shot_patterns = shot_patterns_str
    print(f"Using shot patterns from patterns.json: {mapping_generator.shot_patterns}", file=sys.stderr)
    
    # 2. Task patterns - use ONLY from patterns.json
    mapping_generator.task_patterns = mapping_generator.config.get("taskPatterns", {})
    print(f"Using task patterns from patterns.json: {list(mapping_generator.task_patterns.keys())}", file=sys.stderr)
    
    # 3. Resolution patterns - use ONLY from patterns.json
    mapping_generator.resolution_patterns = mapping_generator.config.get("resolutionPatterns", [])
    print(f"Using resolution patterns from patterns.json: {mapping_generator.resolution_patterns}", file=sys.stderr)
    
    # 4. Version patterns - use ONLY from patterns.json
    version_patterns_str = mapping_generator.config.get("versionPatterns", [])
    mapping_generator.version_patterns = version_patterns_str
    print(f"Using version patterns from patterns.json: {mapping_generator.version_patterns}", file=sys.stderr)
