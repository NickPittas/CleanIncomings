def is_network_path(path: str) -> bool:
    """Check if a path is on a network drive"""
    network_prefixes = ('\\\\', '//', 'N:', 'Z:', 'V:')  # Common network drive prefixes
    return any(path.startswith(prefix) for prefix in network_prefixes)
