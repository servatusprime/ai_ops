#!/usr/bin/env python3
"""
Validation operation for customization config inputs.

Usage:
    python op_validate_config.py <config_file>

Returns:
    0 if valid, 1 if invalid with error messages
"""

import sys
from pathlib import Path

import yaml


def validate_config(config_path):
    """
    Validate customization config against expected schema.

    Args:
        config_path: Path to config file (.yaml or .yml)

    Returns:
        tuple: (is_valid, errors_list)
    """
    errors = []

    # Check file exists
    if not Path(config_path).exists():
        return False, [f"Config file not found: {config_path}"]

    # Load YAML
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
    except yaml.YAMLError as e:
        return False, [f"Invalid YAML: {e}"]
    except Exception as e:
        return False, [f"Error reading file: {e}"]

    # Validate version if present
    if 'version' in config:
        if not isinstance(config['version'], (str, float)):
            errors.append("version must be a string or number")

    # Validate customizations section (aligns with aiops_config.template.yaml)
    if 'customizations' in config:
        custom = config['customizations']

        # Validate clarification_limits if present
        if 'clarification_limits' in custom:
            cl = custom['clarification_limits']
            if 'max_followups' in cl and not isinstance(cl['max_followups'], int):
                errors.append("customizations.clarification_limits.max_followups must be an integer")

        # Validate session_limits if present
        if 'session_limits' in custom:
            sl = custom['session_limits']
            is_num = isinstance(sl.get('max_size_kb'), (int, float))
            if 'max_size_kb' in sl and sl['max_size_kb'] is not None and not is_num:
                errors.append("customizations.session_limits.max_size_kb must be a number or null")

        # Validate bootstrap_preferences if present
        if 'bootstrap_preferences' in custom:
            bp = custom['bootstrap_preferences']
            if 'max_read_depth' in bp and not isinstance(bp['max_read_depth'], int):
                errors.append("customizations.bootstrap_preferences.max_read_depth must be an integer")

    return len(errors) == 0, errors


def main():
    if len(sys.argv) != 2:
        print("Usage: op_validate_config.py <config_file>")
        sys.exit(1)

    config_path = sys.argv[1]
    is_valid, errors = validate_config(config_path)

    if is_valid:
        print(f"[OK] Config valid: {config_path}")
        sys.exit(0)
    else:
        print(f"[FAIL] Config invalid: {config_path}")
        for error in errors:
            print(f"  - {error}")
        sys.exit(1)


if __name__ == '__main__':
    main()
