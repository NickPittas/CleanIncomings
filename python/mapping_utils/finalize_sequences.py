import sys
import time
from typing import Dict, Any, List, Tuple

def finalize_sequences(file_groups: Dict[str, Any], files: List[Any], single_files: List[Any], batch_id=None) -> Tuple[List[dict], List[Any]]:
    """Finalize the sequences from grouped files, with timeout protection."""
    sequences = []
    progress_interval = 100
    progress_update_interval = 1.0  # 1 second between updates
    last_progress_time = time.time()

    # Report initial status
    print(f"[INFO] Finalizing {len(file_groups)} sequence groups", file=sys.stderr)
    if batch_id:
        pass # Placeholder for removed progress update

    # Process sequences in batches to avoid memory issues
    for i, (seq_key, group_data) in enumerate(file_groups.items()):
        try:
            # Update progress periodically
            current_time = time.time()
            if i % progress_interval == 0 or (current_time - last_progress_time > progress_update_interval):
                if batch_id:
                    pass # Placeholder for removed progress update
                if i % (progress_interval * 10) == 0 or i == 0:
                    print(f"[PROGRESS] Sequence finalization: {i+1}/{len(file_groups)} groups", file=sys.stderr)
                last_progress_time = current_time

            # Skip empty groups
            if not group_data.get("files") or len(group_data["files"]) == 0:
                continue

            # Sequences need at least 2 frames
            if len(group_data["files"]) > 1:
                # If frames are available, sort by frame number
                if "frames" in group_data and len(group_data["frames"]) > 0:
                    frames = group_data["frames"]
                    files_list = group_data["files"]

                    # Create sorted frames and files
                    # Make sure we have valid frame numbers
                    if not all(isinstance(frame, int) for frame in frames):
                        print(f"[WARNING] Invalid frame numbers in sequence, skipping group", file=sys.stderr)
                        single_files.extend(files_list)
                        continue

                    frame_file_pairs = sorted(zip(frames, files_list), key=lambda x: x[0])
                    sorted_frames = [pair[0] for pair in frame_file_pairs]
                    sorted_files = [pair[1] for pair in frame_file_pairs]

                    sequence = {
                        "type": "sequence",
                        "base_name": group_data["base_name"],
                        "suffix": group_data["suffix"],
                        "extension": group_data.get("extension", group_data["suffix"]),
                        "directory": group_data["directory"],
                        "files": sorted_files,
                        "frame_numbers": sorted_frames,
                        "frame_range": f"{min(sorted_frames)}-{max(sorted_frames)}",
                        "frame_count": len(sorted_files),
                        "size": group_data.get("size", 0),
                    }

                    sequences.append(sequence)

                    # Log only occasionally for large sets
                    if len(sequences) % 10 == 0 or len(sequences) < 10:
                        print(
                            f"  Sequence: {group_data['base_name']}.{group_data['suffix']} "
                            f"[{sequence['frame_range']}] ({sequence['frame_count']} frames)",
                            file=sys.stderr,
                        )
                else:
                    # If frames aren't available, just process as single files
                    single_files.extend(group_data["files"])
            else:
                # Groups with only one file go to single files
                if len(group_data["files"]) == 1:
                    single_files.append(group_data["files"][0])
        except Exception as e:
            # If any error happens during finalization, add all files to singles as fallback
            # print(f"[ERROR] Error finalizing sequence group {seq_key}: {e}", file=sys.stderr)
            if "files" in group_data and group_data["files"]:
                single_files.extend(group_data["files"])

    # Final progress update
    if batch_id:
        pass # Placeholder for removed progress update

    print(
        f"[INFO] Final result: {len(sequences)} sequences, {len(single_files)} single files",
        file=sys.stderr,
    )
    return sequences, single_files
