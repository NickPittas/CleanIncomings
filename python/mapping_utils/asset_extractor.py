import re
from typing import Optional, List
import configparser

def extract_asset_simple(filename: str, asset_patterns: List[str]) -> Optional[str]:
    config = configparser.ConfigParser()
    config.read('config.ini')
    asset_regex_pattern = config.get('asset_regex', 'pattern')
    asset_regex_flags = config.get('asset_regex', 'flags')
    asset_regex_flags = [flag.strip() for flag in asset_regex_flags.split(',')]

    for asset in asset_patterns:
        pattern = re.compile(asset_regex_pattern.replace('{{asset}}', re.escape(asset)), flags=[getattr(re, flag) for flag in asset_regex_flags])
        if pattern.search(filename):
            return asset
    return "unmatched"
