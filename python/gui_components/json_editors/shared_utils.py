"""
Shared utilities for JSON editors
"""

import json
import os
from datetime import datetime
import shutil
from tkinter import messagebox
from typing import Dict, Any


def load_json_file(file_path: str, default_data: Dict[str, Any] = None) -> Dict[str, Any]:
    """Load JSON file with error handling"""
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            return default_data or {}
    except Exception as e:
        messagebox.showerror("Error", f"Failed to load {file_path}: {e}")
        return default_data or {}


def save_json_file(file_path: str, data: Dict[str, Any], create_backup: bool = True) -> bool:
    """Save JSON file with backup and error handling"""
    try:
        # Create backup if requested
        if create_backup and os.path.exists(file_path):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = f"{file_path}.backup_{timestamp}"
            shutil.copy2(file_path, backup_file)
        
        # Save file
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        return True
    except Exception as e:
        messagebox.showerror("Error", f"Failed to save {file_path}: {e}")
        return False


def clean_patterns_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Clean empty patterns from data"""
    clean_data = {}
    for key, value in data.items():
        if isinstance(value, list):
            clean_data[key] = [p for p in value if p.strip()]
        elif isinstance(value, dict):
            clean_dict = {}
            for task_name, patterns in value.items():
                if task_name.strip() and patterns:
                    clean_patterns = [p for p in patterns if p.strip()]
                    if clean_patterns:
                        clean_dict[task_name.strip()] = clean_patterns
            clean_data[key] = clean_dict
        else:
            clean_data[key] = value
    return clean_data


def clean_profiles_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Clean empty profiles from data"""
    clean_data = {}
    for profile_name, rules in data.items():
        if profile_name.strip() and rules:
            clean_rules = []
            for rule in rules:
                for folder_path, patterns in rule.items():
                    if folder_path.strip():
                        clean_patterns = [p for p in patterns if p.strip()]
                        clean_rules.append({folder_path.strip(): clean_patterns})
            if clean_rules:
                clean_data[profile_name.strip()] = clean_rules
    return clean_data 