import os
import sys
import shutil
import uuid
import json
import time
import threading
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import queue

# Import WebSocket progress functionality
try:
    from .progress_server import send_progress_update, start_progress_server
    WEBSOCKET_AVAILABLE = True
except ImportError:
    try:
        from progress_server import send_progress_update, start_progress_server
        WEBSOCKET_AVAILABLE = True
    except ImportError:
        WEBSOCKET_AVAILABLE = False
        print("[WARNING] WebSocket progress server not available", file=sys.stderr)


class FileOperations:
    """Handles file move/copy operations, conflict detection, and progress tracking."""

    def __init__(self):
        self.progress_dir = os.path.join(os.path.dirname(__file__), "_progress")
        os.makedirs(self.progress_dir, exist_ok=True)
        self.cancelled_operations = set()  # Track cancelled batch IDs
        self.active_threads = {}  # Track active operation threads for force-kill
        
        # Start WebSocket server if available
        if WEBSOCKET_AVAILABLE:
            try:
                start_progress_server()
                print("[INFO] WebSocket progress server started", file=sys.stderr)
            except Exception as e:
                print(f"[WARNING] Failed to start WebSocket server: {e}", file=sys.stderr)

    def _progress_path(self, batch_id: str) -> str:
        return os.path.join(self.progress_dir, f"progress_{batch_id}.json")

    def _atomic_move(self, src: str, dst: str, batch_id: Optional[str] = None) -> None:
        """
        Perform an atomic move operation that works across drives.
        First tries os.rename (fast, atomic), falls back to copy+delete.
        Includes cancellation checks for long operations.
        """
        print(f"[DEBUG] _atomic_move called: {src} -> {dst}", file=sys.stderr)
        print(
            f"[DEBUG] Source exists before move: {os.path.exists(src)}", file=sys.stderr
        )

        # Check for cancellation before starting
        if batch_id and self.is_cancelled(batch_id):
            raise Exception(f"Operation cancelled before moving {src}")

        try:
            # Try atomic rename first (works only on same filesystem)
            print(f"[DEBUG] Attempting os.rename...", file=sys.stderr)
            os.rename(src, dst)
            print(f"[DEBUG] os.rename succeeded for {src}", file=sys.stderr)
            print(
                f"[DEBUG] Source exists after rename: {os.path.exists(src)}",
                file=sys.stderr,
            )
        except OSError as e:
            # Cross-filesystem move: copy then delete
            print(f"[DEBUG] os.rename failed with error: {e}", file=sys.stderr)
            print(
                f"[DEBUG] Cross-filesystem move detected, using copy+delete for {src}",
                file=sys.stderr,
            )

            # Check for cancellation before copy
            if batch_id and self.is_cancelled(batch_id):
                raise Exception(f"Operation cancelled before copying {src}")

            # Ensure destination directory exists
            os.makedirs(os.path.dirname(dst), exist_ok=True)

            # Copy the file with FORCE-KILLABLE copy for immediate cancellation
            print(f"[DEBUG] Copying file with force-kill capability...", file=sys.stderr)
            self._force_kill_copy(src, dst, batch_id)
            print(
                f"[DEBUG] Copy completed, destination exists: {os.path.exists(dst)}",
                file=sys.stderr,
            )

            # Check for cancellation before deleting source
            if batch_id and self.is_cancelled(batch_id):
                # Clean up partial copy if cancelled
                if os.path.exists(dst):
                    os.remove(dst)
                raise Exception(f"Operation cancelled before deleting source {src}")

            # Verify copy was successful before deleting source
            if os.path.exists(dst):
                print(
                    f"[DEBUG] Copy verified, now deleting source: {src}",
                    file=sys.stderr,
                )
                os.remove(src)
                print(f"[DEBUG] Source file deleted: {src}", file=sys.stderr)
                print(
                    f"[DEBUG] Source exists after delete: {os.path.exists(src)}",
                    file=sys.stderr,
                )
            else:
                print(
                    f"[CRITICAL ERROR] Copy failed - destination does not exist: {dst}",
                    file=sys.stderr,
                )
                raise Exception(
                    f"Copy operation failed - destination file not created: {dst}"
                )

        # Final verification
        print(
            f"[DEBUG] Final verification - Source exists: {os.path.exists(src)}, Destination exists: {os.path.exists(dst)}",
            file=sys.stderr,
        )

    def _force_kill_copy(self, src: str, dst: str, batch_id: Optional[str] = None) -> None:
        """
        Copy a file with IMMEDIATE cancellation capability - can be killed mid-write.
        Uses threading.Event for instant cancellation response with micro-chunks.
        """
        import threading
        
        # Check for cancellation before starting
        if batch_id and self.is_cancelled(batch_id):
            raise Exception(f"Operation cancelled before copying {src}")
        
        # Create a cancellation event for this specific operation
        cancel_event = threading.Event()
        
        # Store the cancel event so we can trigger it from cancel_operation()
        if batch_id:
            if batch_id not in self.active_threads:
                self.active_threads[batch_id] = []
            self.active_threads[batch_id].append(cancel_event)
        
        try:
            # Use MICRO chunks for maximum cancellation responsiveness
            chunk_size = 1024  # 1KB chunks - check cancellation every 1KB!
            
            print(f"[FORCE-KILL] Starting copy with 1KB micro-chunks for immediate cancellation", file=sys.stderr)
            
            with open(src, 'rb') as fsrc:
                with open(dst, 'wb') as fdst:
                    bytes_copied = 0
                    chunk_count = 0
                    
                    while True:
                        # IMMEDIATE cancellation check before every single chunk
                        if cancel_event.is_set() or (batch_id and self.is_cancelled(batch_id)):
                            print(f"[FORCE-KILL] CANCELLED during copy at {bytes_copied} bytes ({chunk_count} chunks)", file=sys.stderr)
                            # FORCE KILL - close files immediately and clean up
                            try:
                                fdst.close()
                            except:
                                pass
                            if os.path.exists(dst):
                                try:
                                    os.remove(dst)
                                    print(f"[FORCE-KILL] Cleaned up partial file: {dst}", file=sys.stderr)
                                except:
                                    pass
                            raise Exception(f"Operation FORCE CANCELLED during copy of {src} (copied {bytes_copied} bytes)")
                        
                        chunk = fsrc.read(chunk_size)
                        if not chunk:
                            break
                        
                        # ANOTHER cancellation check before writing
                        if cancel_event.is_set() or (batch_id and self.is_cancelled(batch_id)):
                            print(f"[FORCE-KILL] CANCELLED before write at {bytes_copied} bytes", file=sys.stderr)
                            try:
                                fdst.close()
                            except:
                                pass
                            if os.path.exists(dst):
                                try:
                                    os.remove(dst)
                                except:
                                    pass
                            raise Exception(f"Operation FORCE CANCELLED during copy of {src} (copied {bytes_copied} bytes)")
                        
                        fdst.write(chunk)
                        bytes_copied += len(chunk)
                        chunk_count += 1
                        
                        # Log progress every 1MB for debugging
                        if chunk_count % 1024 == 0:  # Every 1MB
                            print(f"[FORCE-KILL] Copied {bytes_copied // (1024*1024)}MB, checking cancellation...", file=sys.stderr)
                        
                        # THIRD cancellation check after writing (triple safety)
                        if cancel_event.is_set() or (batch_id and self.is_cancelled(batch_id)):
                            print(f"[FORCE-KILL] CANCELLED after write at {bytes_copied} bytes", file=sys.stderr)
                            try:
                                fdst.close()
                            except:
                                pass
                            if os.path.exists(dst):
                                try:
                                    os.remove(dst)
                                except:
                                    pass
                            raise Exception(f"Operation FORCE CANCELLED during copy of {src} (copied {bytes_copied} bytes)")
                        
                        # NO DELAYS - maximum speed and responsiveness
                        
            print(f"[FORCE-KILL] Copy completed successfully: {bytes_copied} bytes", file=sys.stderr)
                        
        finally:
            # Clean up the cancel event
            if batch_id and batch_id in self.active_threads:
                try:
                    self.active_threads[batch_id].remove(cancel_event)
                    if not self.active_threads[batch_id]:  # Remove empty list
                        del self.active_threads[batch_id]
                except (ValueError, KeyError):
                    pass

    def _multithreaded_copy(self, src: str, dst: str, batch_id: Optional[str] = None, max_workers: int = 8) -> None:
        """
        Copy a file using multiple threads for maximum 10G network utilization.
        Splits the file into chunks and copies them in parallel.
        """
        import threading
        
        # Check for cancellation before starting
        if batch_id and self.is_cancelled(batch_id):
            raise Exception(f"Operation cancelled before copying {src}")
        
        # Get file size
        file_size = os.path.getsize(src)
        
        # For small files (< 10MB), use single-threaded copy
        if file_size < 10 * 1024 * 1024:
            return self._force_kill_copy(src, dst, batch_id)
        
        # Calculate optimal chunk size for 10G network
        # Target: 64MB chunks for large files, minimum 1MB
        chunk_size = max(1024 * 1024, min(64 * 1024 * 1024, file_size // max_workers))
        num_chunks = (file_size + chunk_size - 1) // chunk_size
        
        print(f"[MULTITHREAD] Starting multithreaded copy: {file_size} bytes in {num_chunks} chunks of {chunk_size//1024//1024}MB each", file=sys.stderr)
        print(f"[MULTITHREAD] Using {min(max_workers, num_chunks)} worker threads", file=sys.stderr)
        
        # Create cancellation events for all threads
        cancel_events = []
        for _ in range(min(max_workers, num_chunks)):
            cancel_event = threading.Event()
            cancel_events.append(cancel_event)
            if batch_id:
                if batch_id not in self.active_threads:
                    self.active_threads[batch_id] = []
                self.active_threads[batch_id].append(cancel_event)
        
        # Create temporary files for each chunk
        temp_files = []
        chunk_results = queue.Queue()
        
        try:
            # Ensure destination directory exists
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            
            def copy_chunk(chunk_index: int, start_pos: int, chunk_size: int, cancel_event: threading.Event):
                """Copy a specific chunk of the file"""
                temp_file = f"{dst}.chunk_{chunk_index}"
                temp_files.append(temp_file)
                
                try:
                    with open(src, 'rb') as fsrc:
                        with open(temp_file, 'wb') as fdst:
                            fsrc.seek(start_pos)
                            remaining = chunk_size
                            bytes_copied = 0
                            
                            # Use 1MB sub-chunks for cancellation responsiveness
                            sub_chunk_size = 1024 * 1024  # 1MB
                            
                            while remaining > 0 and not cancel_event.is_set():
                                # Check for cancellation
                                if batch_id and self.is_cancelled(batch_id):
                                    print(f"[MULTITHREAD] Chunk {chunk_index} cancelled at {bytes_copied} bytes", file=sys.stderr)
                                    raise Exception(f"Chunk {chunk_index} cancelled")
                                
                                read_size = min(sub_chunk_size, remaining)
                                data = fsrc.read(read_size)
                                if not data:
                                    break
                                
                                fdst.write(data)
                                bytes_copied += len(data)
                                remaining -= len(data)
                            
                            if cancel_event.is_set():
                                raise Exception(f"Chunk {chunk_index} cancelled by event")
                            
                            chunk_results.put((chunk_index, bytes_copied, None))
                            print(f"[MULTITHREAD] Chunk {chunk_index} completed: {bytes_copied} bytes", file=sys.stderr)
                            
                except Exception as e:
                    chunk_results.put((chunk_index, 0, str(e)))
                    print(f"[MULTITHREAD] Chunk {chunk_index} failed: {e}", file=sys.stderr)
                    # Clean up failed chunk file
                    try:
                        if os.path.exists(temp_file):
                            os.remove(temp_file)
                    except:
                        pass
            
            # Start all chunk copy operations in parallel
            with ThreadPoolExecutor(max_workers=min(max_workers, num_chunks)) as executor:
                futures = []
                
                for i in range(num_chunks):
                    start_pos = i * chunk_size
                    actual_chunk_size = min(chunk_size, file_size - start_pos)
                    cancel_event = cancel_events[i % len(cancel_events)]
                    
                    future = executor.submit(copy_chunk, i, start_pos, actual_chunk_size, cancel_event)
                    futures.append(future)
                
                # Wait for all chunks to complete
                completed_chunks = 0
                failed_chunks = 0
                total_bytes_copied = 0
                
                for future in as_completed(futures):
                    try:
                        future.result()  # This will raise any exception from the chunk
                    except Exception as e:
                        print(f"[MULTITHREAD] Chunk operation failed: {e}", file=sys.stderr)
                        failed_chunks += 1
                        # Cancel all other operations
                        for event in cancel_events:
                            event.set()
                        break
                
                # Collect results
                while not chunk_results.empty():
                    chunk_index, bytes_copied, error = chunk_results.get()
                    if error:
                        failed_chunks += 1
                        print(f"[MULTITHREAD] Chunk {chunk_index} error: {error}", file=sys.stderr)
                    else:
                        completed_chunks += 1
                        total_bytes_copied += bytes_copied
                
                # Check if operation was cancelled or failed
                if batch_id and self.is_cancelled(batch_id):
                    raise Exception("Multithreaded copy cancelled")
                
                if failed_chunks > 0:
                    raise Exception(f"Multithreaded copy failed: {failed_chunks} chunks failed")
                
                print(f"[MULTITHREAD] All {completed_chunks} chunks completed, reassembling file...", file=sys.stderr)
                
                # Reassemble the file from chunks
                with open(dst, 'wb') as fdst:
                    for i in range(num_chunks):
                        chunk_file = f"{dst}.chunk_{i}"
                        if os.path.exists(chunk_file):
                            with open(chunk_file, 'rb') as chunk_src:
                                shutil.copyfileobj(chunk_src, fdst)
                        else:
                            raise Exception(f"Missing chunk file: {chunk_file}")
                
                # Verify the final file
                final_size = os.path.getsize(dst)
                if final_size != file_size:
                    raise Exception(f"Size mismatch after reassembly: expected {file_size}, got {final_size}")
                
                print(f"[MULTITHREAD] File reassembled successfully: {final_size} bytes", file=sys.stderr)
        
        finally:
            # Clean up temporary chunk files
            for temp_file in temp_files:
                try:
                    if os.path.exists(temp_file):
                        os.remove(temp_file)
                except:
                    pass
            
            # Clean up cancel events
            if batch_id and batch_id in self.active_threads:
                for event in cancel_events:
                    try:
                        self.active_threads[batch_id].remove(event)
                    except (ValueError, KeyError):
                        pass
                if not self.active_threads[batch_id]:
                    del self.active_threads[batch_id]

    def apply_mappings_multithreaded(
        self,
        mappings: List[Dict[str, Any]],
        operation_type: str = "move",
        validate_sequences: bool = True,
        batch_id: Optional[str] = None,
        max_workers: int = 8,
        file_workers: int = 4
    ) -> Dict[str, Any]:
        """
        Apply file move/copy operations using multithreading for maximum 10G network utilization.
        
        Args:
            mappings: List of file mappings to process
            operation_type: "move" or "copy"
            validate_sequences: Whether to validate sequences
            batch_id: Batch ID for progress tracking
            max_workers: Maximum worker threads for file chunks (default 8)
            file_workers: Maximum concurrent files to process (default 4)
        """
        if batch_id is None:
            batch_id = str(uuid.uuid4())
        
        total = len(mappings)
        completed = 0
        failed = 0
        start_time = time.time()
        
        # Calculate total files for better progress tracking
        total_files = 0
        for m in mappings:
            if m.get("type") == "sequence" and "sequence" in m:
                total_files += len(m["sequence"].get("files", []))
            else:
                total_files += 1
        
        files_processed = 0
        files_lock = threading.Lock()
        
        # Initialize progress
        progress = {
            "batchId": batch_id,
            "totalOperations": total,
            "completedOperations": 0,
            "failedOperations": 0,
            "progressPercentage": 0.0,
            "totalSize": 0,
            "processedSize": 0,
            "etaSeconds": None,
            "status": "running",
            "isPaused": False,
            "isCancelled": False,
            "currentFile": None,
            "totalFiles": total_files,
            "filesProcessed": 0,
        }
        
        # Calculate total size
        for m in mappings:
            node = m.get("node") or m.get("sequence", {})
            if node:
                if m.get("type") == "sequence":
                    progress["totalSize"] += m.get("sequence", {}).get("total_size", 0)
                else:
                    progress["totalSize"] += node.get("size", 0)
        
        self._write_progress(batch_id, progress)
        results = []
        results_lock = threading.Lock()
        
        def update_progress_thread_safe():
            """Thread-safe progress update"""
            with files_lock:
                progress["filesProcessed"] = files_processed
                progress["completedOperations"] = completed
                progress["failedOperations"] = failed
                
                if total_files > 0:
                    progress["progressPercentage"] = (files_processed / total_files) * 100
                else:
                    progress["progressPercentage"] = (completed / total) * 100 if total else 100
                
                elapsed = time.time() - start_time
                if files_processed > 0 and elapsed > 0:
                    files_per_sec = files_processed / elapsed
                    remaining_files = total_files - files_processed
                    progress["etaSeconds"] = (
                        int(remaining_files / files_per_sec) if files_per_sec > 0 else None
                    )
                
                self._write_progress(batch_id, progress)
                
                if WEBSOCKET_AVAILABLE:
                    try:
                        send_progress_update(
                            batch_id=batch_id,
                            files_processed=files_processed,
                            total_files=total_files,
                            current_file=progress.get("currentFile", ""),
                            status=progress.get("status", "running")
                        )
                    except Exception as e:
                        print(f"[WARNING] Failed to send WebSocket update: {e}", file=sys.stderr)
        
        def process_single_file(src_file: str, dst_file: str, file_size: int, file_name: str):
            """Process a single file with multithreaded copy"""
            nonlocal files_processed
            
            try:
                # Check for cancellation
                if self.is_cancelled(batch_id):
                    raise Exception("Operation cancelled")
                
                # Update current file
                with files_lock:
                    progress["currentFile"] = src_file
                
                # Ensure destination directory exists
                os.makedirs(os.path.dirname(dst_file), exist_ok=True)
                
                print(f"[MULTITHREAD] Processing file: {file_name} ({file_size} bytes)", file=sys.stderr)
                
                if operation_type == "copy":
                    # Use multithreaded copy for large files
                    self._multithreaded_copy(src_file, dst_file, batch_id, max_workers)
                    
                    # Verify copy
                    if not os.path.exists(dst_file):
                        raise RuntimeError(f"Copy failed - destination not created: {dst_file}")
                    
                    dst_size = os.path.getsize(dst_file)
                    if dst_size != file_size:
                        raise RuntimeError(f"Copy size mismatch - expected: {file_size}, got: {dst_size}")
                    
                else:  # move
                    # For move operations, use atomic move (which may fall back to copy+delete)
                    self._atomic_move(src_file, dst_file, batch_id)
                    
                    # Verify move
                    if os.path.exists(src_file):
                        raise RuntimeError(f"Move failed - source still exists: {src_file}")
                
                # Update progress
                with files_lock:
                    files_processed += 1
                    progress["processedSize"] += file_size
                
                update_progress_thread_safe()
                print(f"[MULTITHREAD] File completed: {file_name}", file=sys.stderr)
                return True
                
            except Exception as e:
                print(f"[MULTITHREAD] File failed {file_name}: {e}", file=sys.stderr)
                return False
        
        def process_mapping(mapping: Dict[str, Any]):
            """Process a single mapping (which may contain multiple files for sequences)"""
            nonlocal completed, failed
            
            try:
                if self.is_cancelled(batch_id):
                    return {"success": False, "error": "Operation cancelled"}
                
                src = mapping.get("sourcePath")
                dst = mapping.get("targetPath")
                
                if mapping.get("type") == "sequence" and "sequence" in mapping:
                    # Handle sequence - process files in parallel
                    seq_info = mapping["sequence"]
                    actual_files = seq_info.get("files", [])
                    
                    if not actual_files:
                        return {"id": mapping.get("id"), "success": False, "error": "No files found in sequence"}
                    
                    dst_dir = os.path.dirname(dst)
                    frames_processed = 0
                    
                    print(f"[MULTITHREAD] Processing sequence with {len(actual_files)} files", file=sys.stderr)
                    
                    # Process sequence files with limited concurrency to avoid overwhelming the system
                    with ThreadPoolExecutor(max_workers=min(file_workers, len(actual_files))) as seq_executor:
                        seq_futures = []
                        
                        for file_info in actual_files:
                            if self.is_cancelled(batch_id):
                                break
                            
                            src_file = file_info.get("path", "")
                            filename = file_info.get("name", "")
                            file_size = file_info.get("size", 0)
                            
                            if not src_file or not os.path.exists(src_file):
                                continue
                            
                            dst_file = os.path.join(dst_dir, filename)
                            
                            future = seq_executor.submit(process_single_file, src_file, dst_file, file_size, filename)
                            seq_futures.append(future)
                        
                        # Wait for all sequence files to complete
                        for future in as_completed(seq_futures):
                            if future.result():
                                frames_processed += 1
                    
                    # Determine sequence result
                    if frames_processed == 0:
                        return {"id": mapping.get("id"), "success": False, "error": "No files could be processed"}
                    elif frames_processed < len(actual_files):
                        return {"id": mapping.get("id"), "success": True, "warning": f"Partial success: {frames_processed}/{len(actual_files)} files"}
                    else:
                        return {"id": mapping.get("id"), "success": True}
                
                else:
                    # Handle single file
                    if not src or not os.path.exists(src):
                        return {"id": mapping.get("id"), "success": False, "error": f"Source file not found: {src}"}
                    
                    file_size = os.path.getsize(src)
                    filename = os.path.basename(src)
                    
                    if process_single_file(src, dst, file_size, filename):
                        return {"id": mapping.get("id"), "success": True}
                    else:
                        return {"id": mapping.get("id"), "success": False, "error": "File processing failed"}
                        
            except Exception as e:
                return {"id": mapping.get("id"), "success": False, "error": str(e)}
        
        # Process all mappings with limited concurrency
        print(f"[MULTITHREAD] Starting multithreaded processing with {file_workers} concurrent mappings", file=sys.stderr)
        
        with ThreadPoolExecutor(max_workers=file_workers) as executor:
            mapping_futures = []
            
            for mapping in mappings:
                if self.is_cancelled(batch_id):
                    break
                future = executor.submit(process_mapping, mapping)
                mapping_futures.append(future)
            
            # Collect results
            for future in as_completed(mapping_futures):
                if self.is_cancelled(batch_id):
                    break
                
                result = future.result()
                
                with results_lock:
                    results.append(result)
                    if result.get("success"):
                        completed += 1
                    else:
                        failed += 1
                
                update_progress_thread_safe()
        
        # Final status
        if self.is_cancelled(batch_id):
            progress["status"] = "cancelled"
            progress["isCancelled"] = True
            success = False
            message = f"Operation cancelled after {completed} successful operations"
        else:
            progress["status"] = "completed"
            success = True
            message = f"Completed {completed} operations, {failed} failed"
        
        self._write_progress(batch_id, progress)
        
        return {
            "success": success,
            "success_count": completed,
            "error_count": failed,
            "results": results,
            "batch_id": batch_id,
            "operations_count": total,
            "cancelled": self.is_cancelled(batch_id),
            "message": message
        }

    def apply_mappings(
        self,
        mappings: List[Dict[str, Any]],
        operation_type: str = "move",
        validate_sequences: bool = True,
        batch_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Apply file move/copy operations and update progress state for frontend polling.
        """
        if batch_id is None:
            batch_id = str(uuid.uuid4())
        total = len(mappings)
        completed = 0
        failed = 0
        start_time = time.time()
        
        # Calculate total files for better progress tracking
        total_files = 0
        for m in mappings:
            if m.get("type") == "sequence" and "sequence" in m:
                total_files += len(m["sequence"].get("files", []))
            else:
                total_files += 1
        
        files_processed = 0
        
        # Try to load existing progress, or create new if none exists
        try:
            progress = self.get_progress(batch_id)
            if "error" in progress:
                # No existing progress, create new
                progress = {
                    "batchId": batch_id,
                    "totalOperations": total,
                    "completedOperations": 0,
                    "failedOperations": 0,
                    "progressPercentage": 0.0,
                    "totalSize": 0,
                    "processedSize": 0,
                    "etaSeconds": None,
                    "status": "running",
                    "isPaused": False,
                    "isCancelled": False,
                    "currentFile": None,
                    "totalFiles": total_files,
                    "filesProcessed": 0,
                }
                # Calculate total size
                for m in mappings:
                    node = m.get("node") or m.get("sequence", {})
                    if node:
                        if m.get("type") == "sequence":
                            progress["totalSize"] += m.get("sequence", {}).get("total_size", 0)
                        else:
                            progress["totalSize"] += node.get("size", 0)
                self._write_progress(batch_id, progress)
            else:
                # Update existing progress to running status
                progress["status"] = "running"
                self._write_progress(batch_id, progress)
        except Exception:
            # Fallback to creating new progress
            progress = {
                "batchId": batch_id,
                "totalOperations": total,
                "completedOperations": 0,
                "failedOperations": 0,
                "progressPercentage": 0.0,
                "totalSize": 0,
                "processedSize": 0,
                "etaSeconds": None,
                "status": "running",
                "isPaused": False,
                "isCancelled": False,
                "currentFile": None,
                "totalFiles": total_files,
                "filesProcessed": 0,
            }
            # Calculate total size
            for m in mappings:
                node = m.get("node") or m.get("sequence", {})
                if node:
                    if m.get("type") == "sequence":
                        progress["totalSize"] += m.get("sequence", {}).get("total_size", 0)
                    else:
                        progress["totalSize"] += node.get("size", 0)
            self._write_progress(batch_id, progress)
        results = []
        
        def update_progress_with_files():
            """Update progress based on files processed, not just mappings completed"""
            progress["filesProcessed"] = files_processed
            progress["completedOperations"] = completed
            progress["failedOperations"] = failed
            
            # Calculate percentage based on files processed for more granular updates
            if total_files > 0:
                file_percentage = (files_processed / total_files) * 100
                mapping_percentage = (completed / total) * 100 if total > 0 else 0
                # Use the more granular file-based percentage
                progress["progressPercentage"] = file_percentage
            else:
                progress["progressPercentage"] = (completed / total) * 100 if total else 100
            
            elapsed = time.time() - start_time
            if files_processed > 0 and elapsed > 0:
                files_per_sec = files_processed / elapsed
                remaining_files = total_files - files_processed
                progress["etaSeconds"] = (
                    int(remaining_files / files_per_sec) if files_per_sec > 0 else None
                )
            
            # Write to JSON file (for fallback)
            self._write_progress(batch_id, progress)
            
            # Send WebSocket update for real-time progress
            if WEBSOCKET_AVAILABLE:
                try:
                    send_progress_update(
                        batch_id=batch_id,
                        files_processed=files_processed,
                        total_files=total_files,
                        current_file=progress.get("currentFile", ""),
                        status=progress.get("status", "running")
                    )
                except Exception as e:
                    print(f"[WARNING] Failed to send WebSocket update: {e}", file=sys.stderr)
        
        for i, mapping in enumerate(mappings):
            # Check for cancellation before processing each mapping
            if self.is_cancelled(batch_id):
                print(f"[INFO] Operation cancelled by user at mapping {i+1}/{total}", file=sys.stderr)
                progress["status"] = "cancelled"
                progress["isCancelled"] = True
                self._write_progress(batch_id, progress)
                return {
                    "success": False,
                    "success_count": completed,
                    "error_count": failed,
                    "results": results,
                    "batch_id": batch_id,
                    "operations_count": total,
                    "cancelled": True,
                    "message": f"Operation cancelled after {completed} successful operations"
                }
            
            try:
                src = mapping.get("sourcePath")
                dst = mapping.get("targetPath")
                progress["currentFile"] = src
                # Ensure destination directory exists
                if dst:
                    os.makedirs(os.path.dirname(dst), exist_ok=True)
                if mapping.get("type") == "sequence" and "sequence" in mapping:
                    # Handle image sequence: use the actual discovered file list
                    seq_info = mapping["sequence"]
                    actual_files = seq_info.get("files", [])

                    if not actual_files:
                        results.append(
                            {
                                "id": mapping.get("id"),
                                "success": False,
                                "error": "No files found in sequence",
                            }
                        )
                        failed += 1
                        continue

                    dst_dir = os.path.dirname(dst)
                    frames_processed = 0

                    print(
                        f"[DEBUG] Processing sequence with {len(actual_files)} files",
                        file=sys.stderr,
                    )

                    for file_index, file_info in enumerate(actual_files):
                        # Check for cancellation before processing each file in sequence
                        if self.is_cancelled(batch_id):
                            print(f"[INFO] Operation cancelled during sequence processing at file {file_index+1}/{len(actual_files)}", file=sys.stderr)
                            progress["status"] = "cancelled"
                            progress["isCancelled"] = True
                            self._write_progress(batch_id, progress)
                            
                            # Send immediate WebSocket update
                            if WEBSOCKET_AVAILABLE:
                                try:
                                    send_progress_update(
                                        batch_id=batch_id,
                                        files_processed=files_processed,
                                        total_files=total_files,
                                        current_file="",
                                        status="cancelled"
                                    )
                                except Exception as e:
                                    print(f"[WARNING] Failed to send WebSocket cancel update: {e}", file=sys.stderr)
                            
                            return {
                                "success": False,
                                "success_count": completed,
                                "error_count": failed,
                                "results": results,
                                "batch_id": batch_id,
                                "operations_count": total,
                                "cancelled": True,
                                "message": f"Operation cancelled during sequence processing at file {file_index+1}/{len(actual_files)}"
                            }
                        
                        src_file = file_info.get("path", "")
                        filename = file_info.get("name", "")

                        if not src_file or not os.path.exists(src_file):
                            print(
                                f"[DEBUG] Skipping file: source does not exist: {src_file}",
                                file=sys.stderr,
                            )
                            continue

                        # Generate destination path for this specific file
                        dst_file = os.path.join(dst_dir, filename)

                        try:
                            os.makedirs(os.path.dirname(dst_file), exist_ok=True)
                            # Get file size from the file info or actual file
                            file_size = file_info.get("size", 0)
                            if file_size == 0 and os.path.exists(src_file):
                                file_size = os.path.getsize(src_file)

                            # Update progress BEFORE starting file operation
                            progress["currentFile"] = src_file
                            update_progress_with_files()

                            print(
                                f"[DEBUG] Sequence file: {operation_type} from {src_file} to {dst_file}",
                                file=sys.stderr,
                            )

                            # Pre-operation checks
                            if not os.access(src_file, os.R_OK):
                                raise PermissionError(f"No read permission for {src_file}")
                            
                            if os.path.exists(dst_file):
                                print(f"[WARNING] Destination file already exists, will overwrite: {dst_file}", file=sys.stderr)

                            if operation_type == "copy":
                                print(
                                    f"[DEBUG] Performing FORCE-KILLABLE COPY on {filename}",
                                    file=sys.stderr,
                                )
                                self._force_kill_copy(src_file, dst_file, batch_id)
                                
                                # Verify copy was successful
                                if not os.path.exists(dst_file):
                                    raise RuntimeError(f"Copy operation failed - destination file not created: {dst_file}")
                                
                                dst_size = os.path.getsize(dst_file)
                                src_size = os.path.getsize(src_file)
                                if dst_size != src_size:
                                    raise RuntimeError(f"Copy size mismatch - src: {src_size}, dst: {dst_size}")
                                
                                print(f"[DEBUG] Copy verified: {dst_size} bytes", file=sys.stderr)
                                
                            else:  # move
                                print(
                                    f"[DEBUG] Performing MOVE on {filename}",
                                    file=sys.stderr,
                                )
                                self._atomic_move(src_file, dst_file, batch_id)

                                # Verify the move actually happened
                                if os.path.exists(src_file):
                                    print(
                                        f"[CRITICAL ERROR] Source file still exists after move: {src_file}",
                                        file=sys.stderr,
                                    )
                                    print(
                                        f"[CRITICAL ERROR] This indicates the move operation failed!",
                                        file=sys.stderr,
                                    )
                                    raise RuntimeError(f"Move operation failed - source file still exists: {src_file}")
                                else:
                                    print(
                                        f"[DEBUG] Move verified: source file deleted: {src_file}",
                                        file=sys.stderr,
                                    )

                            print(
                                f"[DEBUG] File {filename} operation completed successfully",
                                file=sys.stderr,
                            )
                            progress["processedSize"] += file_size
                            frames_processed += 1
                            files_processed += 1
                            
                            # Update progress AFTER each file (more frequent updates)
                            progress["currentFile"] = src_file
                            update_progress_with_files()
                            
                            # Additional cancellation check every 10 files for responsiveness
                            if file_index % 10 == 0 and self.is_cancelled(batch_id):
                                print(f"[INFO] Operation cancelled during sequence processing (periodic check) at file {file_index+1}/{len(actual_files)}", file=sys.stderr)
                                progress["status"] = "cancelled"
                                progress["isCancelled"] = True
                                self._write_progress(batch_id, progress)
                                
                                # Send immediate WebSocket update
                                if WEBSOCKET_AVAILABLE:
                                    try:
                                        send_progress_update(
                                            batch_id=batch_id,
                                            files_processed=files_processed,
                                            total_files=total_files,
                                            current_file="",
                                            status="cancelled"
                                        )
                                    except Exception as e:
                                        print(f"[WARNING] Failed to send WebSocket cancel update: {e}", file=sys.stderr)
                                
                                return {
                                    "success": False,
                                    "success_count": completed,
                                    "error_count": failed,
                                    "results": results,
                                    "batch_id": batch_id,
                                    "operations_count": total,
                                    "cancelled": True,
                                    "message": f"Operation cancelled during sequence processing at file {file_index+1}/{len(actual_files)}"
                                }
                            
                        except Exception as e:
                            error_msg = f"File {filename}: {e}"
                            print(f"[ERROR] Failed to {operation_type} file {filename}: {e}", file=sys.stderr)
                            print(f"[ERROR] Source: {src_file}", file=sys.stderr)
                            print(f"[ERROR] Destination: {dst_file}", file=sys.stderr)
                            print(f"[ERROR] Source exists: {os.path.exists(src_file)}", file=sys.stderr)
                            print(f"[ERROR] Destination exists: {os.path.exists(dst_file)}", file=sys.stderr)
                            
                            # Don't fail the entire sequence for individual file errors
                            # Instead, track the error but continue processing other files
                            print(f"[WARNING] Continuing with remaining files in sequence", file=sys.stderr)

                    # Check if any files were actually processed
                    print(f"[SUMMARY] Sequence processing complete:", file=sys.stderr)
                    print(f"[SUMMARY]   Total files in sequence: {len(actual_files)}", file=sys.stderr)
                    print(f"[SUMMARY]   Files successfully processed: {frames_processed}", file=sys.stderr)
                    print(f"[SUMMARY]   Success rate: {(frames_processed/len(actual_files)*100):.1f}%", file=sys.stderr)
                    
                    if frames_processed == 0:
                        failed += 1
                        results.append(
                            {
                                "id": mapping.get("id"),
                                "success": False,
                                "error": f"No files could be processed - all {len(actual_files)} source files missing or inaccessible",
                            }
                        )
                        print(f"[SUMMARY] Sequence marked as FAILED - no files processed", file=sys.stderr)
                    elif frames_processed < len(actual_files):
                        # Partial success - some files failed
                        completed += 1
                        results.append({
                            "id": mapping.get("id"), 
                            "success": True,
                            "warning": f"Partial success: {frames_processed}/{len(actual_files)} files processed"
                        })
                        print(f"[SUMMARY] Sequence marked as SUCCESS with WARNING - partial processing", file=sys.stderr)
                    else:
                        # Complete success
                        completed += 1
                        results.append({"id": mapping.get("id"), "success": True})
                        print(f"[SUMMARY] Sequence marked as SUCCESS - all files processed", file=sys.stderr)
                else:
                    # Single file logic
                    print(
                        f"[DEBUG] Single file operation: {operation_type}",
                        file=sys.stderr,
                    )
                    print(f"[DEBUG] Source: {src}", file=sys.stderr)
                    print(f"[DEBUG] Destination: {dst}", file=sys.stderr)

                    # Get file size before operation
                    file_size = os.path.getsize(src) if os.path.exists(src) else 0
                    print(f"[DEBUG] File size: {file_size}", file=sys.stderr)

                    if operation_type == "copy":
                        print(f"[DEBUG] Performing FORCE-KILLABLE COPY operation", file=sys.stderr)
                        self._force_kill_copy(src, dst, batch_id)
                    else:  # move
                        print(f"[DEBUG] Performing MOVE operation", file=sys.stderr)
                        self._atomic_move(src, dst, batch_id)

                        # Verify the move actually happened
                        if os.path.exists(src):
                            print(
                                f"[CRITICAL ERROR] Source file still exists after move: {src}",
                                file=sys.stderr,
                            )
                            print(
                                f"[CRITICAL ERROR] This indicates the move operation failed!",
                                file=sys.stderr,
                            )
                        else:
                            print(
                                f"[DEBUG] Move verified: source file deleted: {src}",
                                file=sys.stderr,
                            )

                    print(f"[DEBUG] Operation completed successfully", file=sys.stderr)
                    completed += 1
                    files_processed += 1
                    progress["processedSize"] += file_size
                    results.append({"id": mapping.get("id"), "success": True})
                
                # Update progress after each mapping
                update_progress_with_files()
                
            except Exception as e:
                failed += 1
                results.append(
                    {"id": mapping.get("id"), "success": False, "error": str(e)}
                )
                update_progress_with_files()
                
        progress["status"] = (
            "completed"
            if failed == 0
            else ("completed_with_errors" if completed > 0 else "failed")
        )
        progress["currentFile"] = None
        self._write_progress(batch_id, progress)
        return {
            "success": failed == 0,
            "success_count": completed,
            "error_count": failed,
            "results": results,
            "batch_id": batch_id,
            "operations_count": total,
        }

    def apply_mappings_async(
        self,
        mappings: List[Dict[str, Any]],
        operation_type: str = "move",
        validate_sequences: bool = True,
        batch_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Start file operations asynchronously and return immediately with batch_id.
        The actual operations run in a background thread.
        """
        if batch_id is None:
            batch_id = str(uuid.uuid4())
        
        total = len(mappings)
        
        # Calculate total files for better progress tracking
        total_files = 0
        for m in mappings:
            if m.get("type") == "sequence" and "sequence" in m:
                total_files += len(m["sequence"].get("files", []))
            else:
                total_files += 1
        
        # Initialize progress state
        progress = {
            "batchId": batch_id,
            "totalOperations": total,
            "completedOperations": 0,
            "failedOperations": 0,
            "progressPercentage": 0.0,
            "totalSize": 0,
            "processedSize": 0,
            "etaSeconds": None,
            "status": "starting",
            "isPaused": False,
            "isCancelled": False,
            "currentFile": None,
            "totalFiles": total_files,
            "filesProcessed": 0,
        }
        
        # Calculate total size
        for m in mappings:
            node = m.get("node") or m.get("sequence", {})
            if node:
                if m.get("type") == "sequence":
                    progress["totalSize"] += m.get("sequence", {}).get("total_size", 0)
                else:
                    progress["totalSize"] += node.get("size", 0)
        
        # Write initial progress
        self._write_progress(batch_id, progress)
        
        # Start background thread for actual operations
        def run_operations():
            try:
                # Update status to running
                progress["status"] = "running"
                self._write_progress(batch_id, progress)
                
                # Run the actual operations (reuse existing logic)
                result = self.apply_mappings(
                    mappings, operation_type, validate_sequences, batch_id
                )
                
                # The apply_mappings method will handle all progress updates
                print(f"[DEBUG] Background operations completed: {result}", file=sys.stderr)
                
            except Exception as e:
                # Handle any errors in background thread
                print(f"[ERROR] Background operations failed: {e}", file=sys.stderr)
                import traceback
                traceback.print_exc(file=sys.stderr)
                progress["status"] = "failed"
                progress["error"] = str(e)
                self._write_progress(batch_id, progress)
        
        # Start the background thread (non-daemon so it doesn't get killed when main process exits)
        thread = threading.Thread(target=run_operations, daemon=False)
        thread.start()
        
        # Give the thread a moment to start and write initial progress
        import time
        time.sleep(0.1)
        
        # Return immediately with batch_id
        return {
            "success": True,
            "batch_id": batch_id,
            "operations_count": total,
            "message": "Operations started in background",
            "async": True
        }

    def _write_progress(self, batch_id: str, progress: Dict[str, Any]):
        try:
            progress_path = self._progress_path(batch_id)
            with open(progress_path, "w", encoding="utf-8") as f:
                json.dump(progress, f)
        except Exception as e:
            print(f"[ERROR] Failed to write progress: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc(file=sys.stderr)

    def get_progress(self, batch_id: str) -> Dict[str, Any]:
        """
        Return the current progress state for the given batch_id.
        """
        try:
            with open(self._progress_path(batch_id), "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            return {"error": f"No progress found for batch_id {batch_id}: {e}"}
    
    def cancel_operation(self, batch_id: str) -> Dict[str, Any]:
        """
        FORCE CANCEL an ongoing operation by batch_id - kills operations immediately.
        """
        try:
            print(f"[FORCE CANCEL] Initiating immediate cancellation for {batch_id}", file=sys.stderr)
            
            # 1. IMMEDIATELY trigger all active copy operations to stop
            if batch_id in self.active_threads:
                cancel_events = self.active_threads[batch_id]
                print(f"[FORCE CANCEL] Triggering {len(cancel_events)} active copy operations to stop", file=sys.stderr)
                for cancel_event in cancel_events:
                    cancel_event.set()  # This will immediately stop any active copy operations
                # Clear the events list
                self.active_threads[batch_id] = []
            
            # 2. Mark the operation as cancelled in memory
            self.cancelled_operations.add(batch_id)
            print(f"[FORCE CANCEL] Marked operation {batch_id} as cancelled", file=sys.stderr)
            
            # 3. Update progress file to reflect cancellation
            progress = self.get_progress(batch_id)
            if "error" not in progress:
                progress["status"] = "cancelled"
                progress["isCancelled"] = True
                progress["currentFile"] = ""  # Clear current file since we're stopping
                self._write_progress(batch_id, progress)
                print(f"[FORCE CANCEL] Updated progress file for {batch_id}", file=sys.stderr)
                
                # 4. Send IMMEDIATE WebSocket update
                if WEBSOCKET_AVAILABLE:
                    try:
                        from .progress_server import send_progress_update
                        send_progress_update(
                            batch_id=batch_id,
                            files_processed=progress.get("filesProcessed", 0),
                            total_files=progress.get("totalFiles", 0),
                            current_file="",
                            status="cancelled"
                        )
                        print(f"[FORCE CANCEL] Sent WebSocket cancellation update for {batch_id}", file=sys.stderr)
                    except Exception as e:
                        print(f"[WARNING] Failed to send WebSocket cancel update: {e}", file=sys.stderr)
                
                return {"success": True, "message": f"Operation {batch_id} FORCE CANCELLED immediately"}
            else:
                return {"success": False, "message": f"Operation {batch_id} not found"}
        except Exception as e:
            print(f"[ERROR] Failed to force cancel operation {batch_id}: {e}", file=sys.stderr)
            return {"success": False, "error": str(e)}
    
    def is_cancelled(self, batch_id: str) -> bool:
        """
        Check if an operation has been cancelled.
        """
        return batch_id in self.cancelled_operations

    # ... (move all FileOperations methods here, unchanged) ...
