import os
import re

def detect_image_sequence(file_path):
    """
    Given a file path, detect the sequence pattern and enumerate all frames in the sequence.
    Returns (list of files sorted, padding, ext, basename, first_idx, last_idx)
    """
    dirname, fname = os.path.split(file_path)
    match = re.match(r"(.*?)(\\d+)(\\.[^.]+)$", fname)
    if not match:
        return [file_path], None, None, None, None, None
    base, frame_str, ext = match.groups()
    padding = len(frame_str)
    pattern = re.compile(rf"{re.escape(base)}(\\d{{{padding}}}){re.escape(ext)}$")
    files = []
    idxs = []
    for f in os.listdir(dirname):
        m = pattern.match(f)
        if m:
            files.append(os.path.join(dirname, f))
            idxs.append(int(m.group(1)))
    sorted_files = [x for _, x in sorted(zip(idxs, files))]
    if not sorted_files:
        return [file_path], padding, ext, base, None, None
    return sorted_files, padding, ext, base, min(idxs), max(idxs)
