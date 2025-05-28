import sys

def update_mapping_progress(batch_id, current, total, status="processing", current_file=""):
    percentage = round(current / total * 100 if total > 0 else 0, 1)
    print(f"[PROGRESS] {status}: {current}/{total} ({percentage}%)", file=sys.stderr)
    # WebSocket logic can be added here if needed
