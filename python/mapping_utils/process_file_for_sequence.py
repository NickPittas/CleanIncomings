def process_file_for_sequence(file_node, file_groups, single_files, sequence_extensions, extract_sequence_info):
    """
    Process a single file for sequence grouping.
    Modularized from MappingGenerator._process_file_for_sequence.
    """
    try:
        file_name = file_node.get("name", "")
        file_ext = file_node.get("extension", "").lower()
        if file_ext not in sequence_extensions:
            single_files.append(file_node)
            return
        file_path = file_node.get("path", "")
        from pathlib import Path
        directory = str(Path(file_path).parent)
        sequence_info = extract_sequence_info(file_name)
        if sequence_info and "frame" in sequence_info:
            base_name = sequence_info["base_name"]
            if (base_name, file_ext) not in file_groups:
                file_groups[(base_name, file_ext)] = {
                    "base_name": base_name,
                    "suffix": file_ext,
                    "frames": [],
                    "files": [],
                    "type": "sequence",
                    "size": 0,
                    "file_count": 0,
                    "directory": directory,
                }
            file_groups[(base_name, file_ext)]["frames"].append(sequence_info["frame"])
            file_groups[(base_name, file_ext)]["files"].append(file_path)
            file_groups[(base_name, file_ext)]["size"] += file_node.get("size", 0)
            file_groups[(base_name, file_ext)]["file_count"] += 1
        else:
            single_files.append(file_node)
    except Exception as e:
        # print(f"[ERROR] Error in process_file_for_sequence for {file_node.get('name', 'unknown')}: {e}")
        single_files.append(file_node)  # Add to single files as fallback
