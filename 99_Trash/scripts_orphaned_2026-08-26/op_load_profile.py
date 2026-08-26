#!/usr/bin/env python3
"""
Profile loader operation for rider/crew customization profiles.

Usage:
    python op_load_profile.py <profile_type> <profile_path>
    python op_load_profile.py rider 02_Modules/01_agent_profiles/profiles/rider_custom.yaml
    python op_load_profile.py crew 02_Modules/01_agent_profiles/profiles/crew_custom.yaml

Returns:
    0 if loaded successfully, 1 if error

Note: Default profiles (rider_default.yaml, crew_default.yaml) do not exist yet.
      Profile schema is still evolving. Provide explicit path to profile file.
"""

import sys
from pathlib import Path

import yaml


def load_profile(profile_type, profile_path):
    """
    Load customization profile for rider or crew.

    Args:
        profile_type: 'rider' or 'crew'
        profile_path: Path to profile file (required, no defaults)

    Returns:
        tuple: (success, profile_dict, errors_list)
    """
    errors = []

    # Validate profile type
    if profile_type not in ['rider', 'crew']:
        return False, None, [f"Invalid profile_type: {profile_type}. Must be 'rider' or 'crew'"]

    profile_path = Path(profile_path)

    # Check if profile exists
    if not profile_path.exists():
        return False, None, [f"Profile file not found: {profile_path}"]

    # Load profile YAML
    try:
        with open(profile_path, 'r') as f:
            profile = yaml.safe_load(f)
    except yaml.YAMLError as e:
        return False, None, [f"Invalid YAML in profile: {e}"]
    except Exception as e:
        return False, None, [f"Error reading profile: {e}"]

    # Validate profile structure
    if not isinstance(profile, dict):
        return False, None, ["Profile must be a YAML dictionary"]

    # Validate profile has expected sections (stub - expand as needed)
    expected_sections = ['profile_metadata', 'preferences']
    for section in expected_sections:
        if section not in profile:
            errors.append(f"Warning: Profile missing recommended section: {section}")

    # Profile-specific validation
    if profile_type == 'rider':
        # Rider profiles should have individual preferences
        if 'preferences' in profile:
            prefs = profile['preferences']
            if 'verbosity' not in prefs:
                errors.append("Warning: Rider profile missing 'verbosity' preference")

    elif profile_type == 'crew':
        # Crew profiles should have multi-agent coordination settings
        if 'coordination' not in profile:
            errors.append("Warning: Crew profile missing 'coordination' section")

    # Return success with any warnings
    return True, profile, errors


def apply_profile(profile, profile_type):
    """
    Apply profile settings to current session (stub).

    Args:
        profile: Loaded profile dictionary
        profile_type: 'rider' or 'crew'

    Returns:
        Applied settings summary
    """
    applied = []

    # Extract key settings (stub - expand as profile schema solidifies)
    if 'preferences' in profile:
        prefs = profile['preferences']
        if 'verbosity' in prefs:
            applied.append(f"Verbosity: {prefs['verbosity']}")
        if 'auto_compress' in prefs:
            applied.append(f"Auto-compress: {prefs['auto_compress']}")

    if profile_type == 'crew' and 'coordination' in profile:
        coord = profile['coordination']
        if 'lock_timeout' in coord:
            applied.append(f"Lock timeout: {coord['lock_timeout']}")

    return applied


def main():
    if len(sys.argv) != 3:
        print("Usage: op_load_profile.py <profile_type> <profile_path>")
        print("Examples:")
        print("  python op_load_profile.py rider 02_Modules/01_agent_profiles/profiles/rider_custom.yaml")
        print("  python op_load_profile.py crew 02_Modules/01_agent_profiles/profiles/crew_custom.yaml")
        sys.exit(1)

    profile_type = sys.argv[1]
    profile_path = sys.argv[2]

    # Load profile
    success, profile, errors = load_profile(profile_type, profile_path)

    if not success:
        print(f"[FAIL] Failed to load {profile_type} profile")
        for error in errors:
            print(f"  - {error}")
        sys.exit(1)

    # Apply profile
    applied = apply_profile(profile, profile_type)

    # Report success
    print(f"[OK] Loaded {profile_type} profile successfully")
    if errors:
        print("\nWarnings:")
        for error in errors:
            print(f"  - {error}")

    if applied:
        print("\nApplied settings:")
        for setting in applied:
            print(f"  - {setting}")

    sys.exit(0)


if __name__ == '__main__':
    main()
