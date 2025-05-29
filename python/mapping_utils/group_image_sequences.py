import time
from pathlib import Path
from typing import List, Dict, Any, Tuple
from threading import Lock

# Set of extensions that can be part of an image sequence
SEQUENCE_EXTENSIONS = set([
    "exr", ".exr", "dpx", ".dpx", "tif", ".tif", "tiff", ".tiff", 
    "jpg", ".jpg", "jpeg", ".jpeg", "png", ".png", "hdr", ".hdr",
    "mov", ".mov", "mp4", ".mp4"
])

def group_image_sequences(files: List[Dict[str, Any]], batch_id=None, extract_sequence_info=None, is_network_path=None) -> Tuple[list, list]:
    """
    Group image files into sequences based on naming patterns.
    Args:
        files: List of file nodes to process
        batch_id: Optional batch ID for progress tracking
        extract_sequence_info: Function to extract sequence info from filename
        is_network_path: Function to check if a path is a network path
    Returns:
        Tuple of (sequences, single_files)
    """
    total_files = len(files)
    file_groups = {}
    file_groups_lock = Lock()
    single_files = []
    single_files_lock = Lock()
    progress_interval = 20
    is_network = False
    if total_files > 0 and "path" in files[0] and is_network_path:
        is_network = is_network_path(files[0]["path"])
    progress_update_interval = 0.2 if is_network else 0.5
    def process_file_batch(batch_files, start_idx, progress_lock):
        local_processed = 0
        local_single_files = []
        local_file_groups = {}
        for file_idx, file_node in enumerate(batch_files):
            i = start_idx + file_idx
            try:
                file_name = file_node.get("name", "")
                file_ext = file_node.get("extension", "").lower()
                if file_ext not in SEQUENCE_EXTENSIONS:
                    local_single_files.append(file_node)
                    continue
                file_path = file_node.get("path", "")
                directory = str(Path(file_path).parent)
                if extract_sequence_info is None:
                    raise ValueError("extract_sequence_info function must be provided")
                sequence_info = extract_sequence_info(file_name)
                if sequence_info and "frame" in sequence_info:
                    base_name = sequence_info["base_name"]
                    filename = file_name
                    if filename and filename.strip() != "" and "sequence_" not in filename.lower():
                        info = {
                            "base_name": base_name,
                            "frame": sequence_info["frame"],
                            "suffix": file_ext
                        }
                        sequence_info = info
                    seq_key = (directory, base_name, file_ext)
                    with file_groups_lock:
                        if seq_key not in file_groups:
                            file_groups[seq_key] = []
                        file_groups[seq_key].append(file_node)
                else:
                    local_single_files.append(file_node)
            except Exception:
                local_single_files.append(file_node)
            current_time = time.time()
        with single_files_lock:
            single_files.extend(local_single_files)
        with file_groups_lock:
            for k, v in local_file_groups.items():
                if k not in file_groups:
                    file_groups[k] = []
                file_groups[k].extend(v)
    # For simplicity, process sequentially (can parallelize if needed)
    process_file_batch(files, 0, None)
    sequences = []
    for seq_key, group in file_groups.items():
        if len(group) > 1:
            sequences.append({"base_name": seq_key[1], "suffix": seq_key[2], "files": group, "directory": seq_key[0], "frame_count": len(group)})
        else:
            single_files.extend(group)
    return sequences, single_files
