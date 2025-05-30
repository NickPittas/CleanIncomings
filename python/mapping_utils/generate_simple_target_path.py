import os
from typing import Optional, Dict, Any, List, Tuple

# Default keywords that identify a path rule as being for 'footage'
# This helps in implementing the fallback logic (Rule 2.4)
DEFAULT_FOOTAGE_KEYWORDS = ["footage", "video", "source", "plate", "plates"]

def generate_simple_target_path(
    root_output_dir: str,
    profile_rules: List[Dict[str, List[str]]], # The array of rules for the selected profile
    filename: str,
    parsed_shot: Optional[str],
    parsed_task: Optional[str],
    parsed_asset: Optional[str],
    parsed_stage: Optional[str],
    parsed_version: Optional[str],
    parsed_resolution: Optional[str],
) -> Dict[str, Any]:
    """
    Generates a target path based on profile rules and extracted filename patterns.

    Args:
        root_output_dir: The user-selected root output directory.
        profile_rules: The list of path rules for the active profile.
                       Example: [{"3D\\Renders": ["beauty", "rgb"]}, ...]
        filename: The original filename.
        parsed_shot: Extracted shot name.
        parsed_task: Extracted task name.
        parsed_asset: Extracted asset name.
        parsed_stage: Extracted stage name.
        parsed_version: Extracted version name.
        parsed_resolution: Extracted resolution name.

    Returns:
        A dictionary containing:
        - "target_path": The fully constructed target_path string, or None if ambiguous.
        - "used_default_footage_rule": Boolean, True if the default footage rule was used.
        - "ambiguous_match": Boolean, True if an ambiguous match occurred.
        - "ambiguous_options": A list of dicts, each with "keyword" and "path", if ambiguous.
    """
    chosen_base_sub_path: Optional[str] = None
    used_default_footage_rule = False
    ambiguous_match_detected = False
    ambiguous_options: List[Dict[str, str]] = []

    # Normalize extracted task and asset for case-insensitive matching
    normalized_task = parsed_task.lower() if parsed_task else None
    normalized_asset = parsed_asset.lower() if parsed_asset else None

    # --- 1. Match against profile rules (Rule 2.1, 2.2, 2.3) ---
    # Primary driver: Task
    if normalized_task:
        for rule_obj in profile_rules:
            for path_key, keywords_in_rule in rule_obj.items():
                normalized_keywords_list = [kw.lower() for kw in keywords_in_rule]
                if normalized_task in normalized_keywords_list: # Exact match
                    chosen_base_sub_path = path_key
                    break
            if chosen_base_sub_path:
                break
    
    # Secondary driver: Asset (if task didn't match)
    if not chosen_base_sub_path and normalized_asset:
        for rule_obj in profile_rules:
            for path_key, keywords_in_rule in rule_obj.items():
                normalized_keywords_list = [kw.lower() for kw in keywords_in_rule]
                if normalized_asset in normalized_keywords_list: # Exact match
                    chosen_base_sub_path = path_key
                    break
            if chosen_base_sub_path:
                break


    # --- 1.5 Check for Ambiguous Matches if no direct full-token match found ---
    if not chosen_base_sub_path: # Only check for ambiguity if no direct full match was found
        # Collate all unique keywords from profile_rules and their paths
        all_profile_keywords_map: Dict[str, str] = {}
        for rule_obj in profile_rules:
            for path_key, keywords_in_rule in rule_obj.items():
                for kw in keywords_in_rule:
                    # If a keyword could map to multiple paths via different rules, this map takes the last one.
                    # This is generally okay as Rule 2.3 is about one token matching multiple *distinct* keywords
                    # that *each* have their own clear (and different) rule.
                    all_profile_keywords_map[kw.lower()] = path_key

        # Check task for ambiguity first
        if normalized_task:
            task_sub_keywords_details: List[Dict[str, str]] = []
            for pk_keyword, pk_path_key in all_profile_keywords_map.items():
                if pk_keyword in normalized_task:
                    task_sub_keywords_details.append({"keyword": pk_keyword, "path": pk_path_key})
            
            if task_sub_keywords_details:
                distinct_paths_for_task_sub_keywords = set(item["path"] for item in task_sub_keywords_details)
                if len(distinct_paths_for_task_sub_keywords) > 1:
                    ambiguous_match_detected = True
                    ambiguous_options = sorted(task_sub_keywords_details, key=lambda x: x["keyword"])
                    chosen_base_sub_path = None 

        # If task was not ambiguous (or no task), check asset for ambiguity
        if not ambiguous_match_detected and normalized_asset:
            asset_sub_keywords_details: List[Dict[str, str]] = []
            for pk_keyword, pk_path_key in all_profile_keywords_map.items():
                if pk_keyword in normalized_asset:
                    asset_sub_keywords_details.append({"keyword": pk_keyword, "path": pk_path_key})

            if asset_sub_keywords_details:
                distinct_paths_for_asset_sub_keywords = set(item["path"] for item in asset_sub_keywords_details)
                if len(distinct_paths_for_asset_sub_keywords) > 1:
                    ambiguous_match_detected = True
                    ambiguous_options = sorted(asset_sub_keywords_details, key=lambda x: x["keyword"])
                    chosen_base_sub_path = None

    # --- 2. Handle No Match - Default to Footage (Rule 2.4) ---
    if not chosen_base_sub_path and not ambiguous_match_detected:
        used_default_footage_rule = True
        # Find the designated footage path rule
        # Attempt 1: Find a rule that *is* the default footage rule by matching all DEFAULT_FOOTAGE_KEYWORDS
        default_footage_path_candidate = None
        normalized_default_keywords_set = set(kw.lower() for kw in DEFAULT_FOOTAGE_KEYWORDS)

        for rule_obj in profile_rules:
            for path_key, keywords in rule_obj.items():
                normalized_keywords_set = set(kw.lower() for kw in keywords)
                # Check if this rule's keywords are specifically the default footage keywords
                if normalized_keywords_set == normalized_default_keywords_set:
                    chosen_base_sub_path = path_key
                    break
            if chosen_base_sub_path: # Found the specific default footage rule
                break
        
        # Attempt 2: If no exact match via set equality, fall back to finding any rule containing any default footage keyword
        if not chosen_base_sub_path:
            for rule_obj in profile_rules:
                for path_key, keywords in rule_obj.items():
                    normalized_keywords_list = [kw.lower() for kw in keywords] # Keep as list for 'in' check
                    if any(ft_kw in normalized_keywords_list for ft_kw in DEFAULT_FOOTAGE_KEYWORDS):
                        chosen_base_sub_path = path_key
                        break
                if chosen_base_sub_path: # Found a broader match
                    break
        if not chosen_base_sub_path: # Fallback if no explicit footage rule found
            # This case should ideally be handled by ensuring profiles always have a footage rule
            # or by defining a very generic fallback path like "_unmapped_footage"
            chosen_base_sub_path = "unmapped_footage" 

    # --- 3. Construct Dynamic Path Segments (Rule 3.3, 4) ---
    dynamic_segments_ordered = [
        parsed_shot,
        parsed_stage,
        parsed_task, # Using original parsed_task for the path segment, not normalized
        parsed_asset, # Using original parsed_asset for the path segment
        parsed_resolution,
        parsed_version
    ]

    final_dynamic_segments = []
    for i, segment in enumerate(dynamic_segments_ordered):
        if segment is not None and segment.strip() != "":
            # Apply specific case rules based on segment type
            if i == 0:  # parsed_shot - preserve original case
                final_dynamic_segments.append(segment)
            elif i == 4:  # parsed_resolution - convert to uppercase
                final_dynamic_segments.append(segment.upper())
            else:  # parsed_stage, parsed_task, parsed_asset, parsed_version - convert to lowercase
                final_dynamic_segments.append(segment.lower())

    # --- 4. Assemble Final Path (Rule 5) ---
    # Ensure root_output_dir is absolute and normalized
    abs_root_output_dir = os.path.abspath(root_output_dir)

    path_parts = [abs_root_output_dir]
    if chosen_base_sub_path: # Should always be true by now due to fallback
        path_parts.append(chosen_base_sub_path)
    path_parts.extend(final_dynamic_segments)
    path_parts.append(filename)

    # Join and normalize for the current OS
    if ambiguous_match_detected:
        target_path = None
    elif not chosen_base_sub_path: # Should only happen if unmapped_footage is the only option and it's not truly set
        target_path = None # Or handle as an error/specific unmapped path
    else:
        target_path = os.path.normpath(os.path.join(*path_parts))

    # Debugging output (optional, can be removed or made conditional)
    # with open("g:\\My Drive\\python\\CleanIncomings\\debug_gstp_new.txt", "a") as f_debug:
    #     f_debug.write(f"--- New Entry ---\n")
    #     f_debug.write(f"Root Output Dir: {root_output_dir}\n")
    #     f_debug.write(f"Profile Rules Count: {len(profile_rules)}\n")
    #     f_debug.write(f"Filename: {filename}\n")
    #     f_debug.write(f"Parsed Task: {parsed_task}, Parsed Asset: {parsed_asset}\n")
    #     f_debug.write(f"Chosen Base Sub Path: {chosen_base_sub_path}\n")
    #     f_debug.write(f"Used Default Footage Rule: {used_default_footage_rule}\n")
    #     f_debug.write(f"Dynamic Segments (lower): {final_dynamic_segments}\n")
    #     f_debug.write(f"Final Target Path: {target_path}\n")

    return {
        "target_path": target_path,
        "used_default_footage_rule": used_default_footage_rule,
        "ambiguous_match": ambiguous_match_detected,
        "ambiguous_options": ambiguous_options
    }
