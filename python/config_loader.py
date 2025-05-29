import json
import os
from typing import Dict, Any

PROFILES_PATH = os.path.join(os.path.dirname(__file__), '..', 'src', 'config', 'profiles.json')

class ProfileNotFoundError(Exception):
    """Custom exception for when a profile is not found."""
    pass

class ProfilesFileNotFoundError(Exception):
    """Custom exception for when the profiles.json file is not found."""
    pass

def load_profile_from_file(profile_name: str) -> Dict[str, Any]:
    """
    Loads a specific profile configuration from the profiles.json file.

    Args:
        profile_name: The name of the profile to load (e.g., "simple", "sphere").

    Returns:
        A dictionary containing the profile configuration.

    Raises:
        ProfilesFileNotFoundError: If profiles.json cannot be found.
        ProfileNotFoundError: If the specified profile_name is not found in profiles.json.
        ValueError: If profiles.json is not valid JSON.
    """
    if not os.path.exists(PROFILES_PATH):
        raise ProfilesFileNotFoundError(f"Profiles configuration file not found at: {os.path.normpath(PROFILES_PATH)}")

    try:
        with open(PROFILES_PATH, 'r') as f:
            all_profiles = json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"Error decoding profiles.json: {e}")
    except Exception as e:
        # Catch other potential file reading errors
        raise ProfilesFileNotFoundError(f"Could not read profiles.json: {e}")


    if profile_name in all_profiles:
        profile_config = all_profiles[profile_name]
        # Ensure the 'name' field in the loaded profile matches, or add it if missing
        if 'name' not in profile_config or profile_config['name'] != profile_name:
            profile_config['name'] = profile_name # Ensure consistency
        return profile_config
    else:
        raise ProfileNotFoundError(f"Profile '{profile_name}' not found in {PROFILES_PATH}. Available profiles: {list(all_profiles.keys())}")

if __name__ == '__main__':
    # Example usage and simple test
    try:
        print(f"Attempting to load profiles from: {os.path.abspath(PROFILES_PATH)}")
        if not os.path.exists(PROFILES_PATH):
            print(f"ERROR: {PROFILES_PATH} does not exist!")
        else:
            print(f"{PROFILES_PATH} exists.")
            
        simple_profile = load_profile_from_file("simple")
        print("\nSimple Profile:")
        print(json.dumps(simple_profile, indent=2))

        sphere_profile = load_profile_from_file("sphere")
        print("\nSphere Profile:")
        print(json.dumps(sphere_profile, indent=2))

        # Test non-existent profile
        try:
            load_profile_from_file("non_existent_profile")
        except ProfileNotFoundError as e:
            print(f"\nSuccessfully caught error for non-existent profile: {e}")
            
    except Exception as e:
        print(f"\nAn error occurred during example usage: {e}")
