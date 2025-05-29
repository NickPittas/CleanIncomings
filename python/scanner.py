import os
import sys
import subprocess
import shutil
import uuid
import json
import time
import concurrent.futures
import threading
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from os import scandir
import re


class FileSystemScanner:
    """Scans file system and builds hierarchical tree structure, with real-time progress tracking."""

    def __init__(self):
        self.supported_extensions = {
            "image": [".exr", ".dpx", ".tiff", ".tif", ".jpg", ".jpeg", ".png", ".hdr"],
            "video": [".mov", ".mp4", ".avi", ".mkv", ".mxf", ".r3d", ".braw"],
            "project": [".nk", ".hip", ".ma", ".mb", ".blend", ".c4d", ".aep"],
            "cache": [".abc", ".bgeo", ".vdb", ".ass", ".usd", ".usda", ".usdc"],
        }
        self.file_count = 0
        self.folder_count = 0
        self.max_depth = 10
        self.tree_max_depth = 10
        self.skip_patterns = [
            r"^\.",
            r"__pycache__",
            r"\.git",
            r"node_modules",
            r"\.tmp",
            r"\.cache",
        ]
        self.progress_dir = os.path.join(os.path.dirname(__file__), "_progress")
        os.makedirs(self.progress_dir, exist_ok=True)
        self._scan_start_time = None
        self._scan_batch_id = None
        
        # Configure timeout and performance settings
        self.network_timeout = 15.0  # Seconds to wait for network operations
        self.network_retry_count = 3  # Number of retries for network operations
        self.network_paths = ('\\\\', '//', 'N:', 'Z:', 'V:')  # Common network drive prefixes
        self.max_workers_local = 8  # Maximum worker threads for local paths
        self.max_workers_network = 4  # Maximum worker threads for network paths

    def _progress_path(self, batch_id: str) -> str:
        return os.path.join(self.progress_dir, f"progress_{batch_id}.json")

    def get_scan_progress(self, batch_id: str) -> Dict[str, Any]:
        """Reads and returns the progress data for a given batch_id from its JSON file."""
        progress_file = self._progress_path(batch_id)
        print(f"[DEBUG][get_scan_progress] Attempting to read: {progress_file}", flush=True)
        try:
            if os.path.exists(progress_file):
                print(f"[DEBUG][get_scan_progress] File exists: {progress_file}", flush=True)
                with open(progress_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    print(f"[DEBUG][get_scan_progress] Loaded data: {data}", flush=True)
                    return data
            else:
                print(f"[DEBUG][get_scan_progress] File NOT found: {progress_file}. Returning 'pending'.", flush=True)
                return {"batchId": batch_id, "status": "pending", "progressPercentage": 0, "result": None}
        except json.JSONDecodeError as e_json:
            print(f"[DEBUG][get_scan_progress] JSONDecodeError for {progress_file}: {e_json}. Returning 'failed'.", flush=True)
            return {"batchId": batch_id, "status": "failed", "result": {"error": f"Malformed progress file: {e_json}"}}
        except Exception as e:
            print(f"[DEBUG][get_scan_progress] Exception for {progress_file}: {e}. Returning 'failed'.", flush=True)
            return {"batchId": batch_id, "status": "failed", "result": {"error": f"Error reading progress file: {e}"}}

    def _write_progress(self, batch_id: str, progress: Dict[str, Any]):
        try:
            with open(self._progress_path(batch_id), "w", encoding="utf-8") as f:
                json.dump(progress, f)
        except Exception as e:
            print(f"Failed to write scan progress: {e}", file=sys.stderr)


    def scan_directory_with_progress(
        self,
        path: str,
        batch_id: Optional[str] = None,
        max_files: int = None,
        use_fast_scan: bool = True,
    ) -> str:
        print("[DEBUG][SCANNER] Entered scan_directory_with_progress", file=sys.stderr)
        sys.stderr.flush()

        if batch_id is None:
            batch_id = str(uuid.uuid4())
            print(f"[DEBUG][SCANNER] scan_directory_with_progress: No batch_id provided, generated new: {batch_id}", file=sys.stderr)
        else:
            print(f"[DEBUG][SCANNER] scan_directory_with_progress: Using provided batch_id: {batch_id}", file=sys.stderr)
        sys.stderr.flush()

        self._scan_start_time = time.time()
        self._scan_batch_id = batch_id
        # Initial progress state
        self.file_count = 0
        self.folder_count = 0
        
        # Check if path is a network path and adjust parameters
        is_network = self._is_network_path(path)
        if is_network:
            print(f"Network path detected: {path}", file=sys.stderr)
            print("Using optimized parameters for network scanning", file=sys.stderr)
        
        # Estimate total files for better progress calculation
        estimated_total = max_files or (5000 if is_network else 10000)  # Lower default for network paths
        
        progress = {
            "batchId": batch_id,
            "totalFilesScanned": 0,
            "totalFoldersScanned": 0,
            "currentFile": None,
            "currentFolder": None,
            "progressPercentage": 0.0,
            "etaSeconds": None,
            "status": "running",
            "startTime": self._scan_start_time,
            "result": None,
            "estimatedTotalFiles": estimated_total
        }
        self._write_progress(batch_id, progress)
        
        try:
            root_path = Path(path)
            if not root_path.exists():
                progress["status"] = "failed"
                progress["result"] = {"error": f"Path does not exist: {path}"}
                self._write_progress(batch_id, progress)
                return batch_id
            if not root_path.is_dir():
                progress["status"] = "failed"
                progress["result"] = {"error": f"Path is not a directory: {path}"}
                self._write_progress(batch_id, progress)
                return batch_id
            
            print(f"Starting scan with progress: {path}", file=sys.stderr)
            self.file_count = 0
            self.folder_count = 0

            def update_progress(current_file=None, current_folder=None):
                elapsed = time.time() - self._scan_start_time
                files_per_sec = self.file_count / elapsed if elapsed > 0 else 0
                eta = None
                if files_per_sec > 0:
                    remaining_files = estimated_total - self.file_count
                    eta = int(remaining_files / files_per_sec) if remaining_files > 0 else 0
                
                # Calculate progress percentage based on estimated total
                progress_percentage = min((self.file_count / estimated_total) * 100, 99.0) if estimated_total > 0 else 0
                
                progress.update(
                    {
                        "totalFilesScanned": self.file_count,
                        "totalFoldersScanned": self.folder_count,
                        "currentFile": current_file,
                        "currentFolder": current_folder,
                        "progressPercentage": progress_percentage,
                        "etaSeconds": eta,
                        "status": "running",
                        "estimatedTotalFiles": estimated_total
                    }
                )
                self._write_progress(batch_id, progress)

            # Always use threaded scan for performance
            file_paths, dir_paths = [], []
            with ThreadPoolExecutor(max_workers=32) as executor:
                futures = [executor.submit(self._list_dir_safe, str(root_path))]
                dir_paths = [str(root_path)]
                last_update_time = time.time()
                
                while futures:
                    completed_futures = []
                    for future in as_completed(futures):
                        entries = future.result()
                        completed_futures.append(future)
                        for entry in entries:
                            try:
                                if entry.is_dir(follow_symlinks=False):
                                    dir_paths.append(entry.path)
                                    futures.append(
                                        executor.submit(self._list_dir_safe, entry.path)
                                    )
                                    self.folder_count += 1
                                    
                                    # Update progress every 100ms for folders to avoid overwhelming
                                    current_time = time.time()
                                    if current_time - last_update_time > 0.1:
                                        update_progress(current_folder=entry.path)
                                        last_update_time = current_time
                                else:
                                    file_paths.append(entry.path)
                                    self.file_count += 1
                                    
                                    # Update progress every 50ms for files for more responsive updates
                                    current_time = time.time()
                                    if current_time - last_update_time > 0.05:
                                        update_progress(current_file=entry.path)
                                        last_update_time = current_time
                            except (OSError, PermissionError):
                                continue
                    for future in completed_futures:
                        futures.remove(future)
            
            # Final update before building tree
            update_progress()
            progress["status"] = "building_tree"
            self._write_progress(batch_id, progress)
            print(
                f"[DEBUG] Scan loop completed. Files: {self.file_count}, Folders: {self.folder_count}",
                file=sys.stderr,
            )
            
            files = [Path(fp) for fp in file_paths]
            print(f"[DEBUG] Building tree from {len(files)} files...", file=sys.stderr)
            tree = self._build_tree_from_files(root_path, files, folders_only=True)
            print(f"[DEBUG] Tree built successfully", file=sys.stderr)
            
            stats = {
                "total_files": self.file_count,
                "total_folders": self.folder_count,
                "scan_limited": False,
                "scan_method": "threaded_scandir",
            }
            
            # Final completion update
            progress["status"] = "completed"
            progress["result"] = {"success": True, "tree": tree, "stats": stats}
            progress["progressPercentage"] = 100.0
            progress["estimatedTotalFiles"] = self.file_count  # Update with actual count
            self._write_progress(batch_id, progress)
            
            print(f"[DEBUG] Progress written to file", file=sys.stderr)
        except Exception as e:
            print(f"Scan failed: {e}", file=sys.stderr)
            progress["status"] = "failed"
            progress["result"] = {"error": str(e)}
            progress["progressPercentage"] = 100.0 # Indicate completion, albeit failed
            self._write_progress(batch_id, progress)
        
        print(
            f"[DEBUG] scan_directory_with_progress: completed, returning batch_id={batch_id}",
            file=sys.stderr,
        )
        return batch_id

    def get_scan_progress(self, batch_id: str) -> Dict[str, Any]:
        try:
            with open(self._progress_path(batch_id), "r", encoding="utf-8") as f:
                progress = json.load(f)
                
                return progress
        except Exception as e:
            return {"error": f"Failed to read scan progress: {e}"}

    def scan_directory(
        self, path: str, max_files: int = None, use_fast_scan: bool = True
    ) -> Dict[str, Any]:
        try:
            root_path = Path(path)
            if not root_path.exists():
                return {"error": f"Path does not exist: {path}"}
            if not root_path.is_dir():
                return {"error": f"Path is not a directory: {path}"}
            print(f"Starting unlimited scan of: {path}", file=sys.stderr)
            print(f"Fast scan mode: {use_fast_scan}", file=sys.stderr)
            self.file_count = 0
            self.folder_count = 0
            if use_fast_scan:
                tree = self._build_tree_threaded(root_path, max_files=max_files)
            else:
                tree = self._build_tree_optimized(root_path, max_files=max_files)
            stats = {
                "total_files": self.file_count,
                "total_folders": self.folder_count,
                "scan_limited": False,
                "scan_method": "threaded_scandir" if use_fast_scan else "standard",
            }
            print(
                f"Scan completed: {self.file_count} files, {self.folder_count} folders",
                file=sys.stderr,
            )
            return {"success": True, "tree": tree, "stats": stats}
        except Exception as e:
            print(f"Scan error: {str(e)}", file=sys.stderr)
            return {"error": f"Failed to scan directory: {str(e)}"}

    def _is_network_path(self, path: str) -> bool:
        """Check if a path is on a network drive"""
        return any(path.startswith(prefix) for prefix in self.network_paths)
    
    def _list_dir_safe(self, path: str) -> List[Any]:
        # Use different timeout settings for network vs local paths
        is_network = self._is_network_path(path)
        timeout = self.network_timeout if is_network else 5.0
        retry_count = self.network_retry_count if is_network else 1
        
        for attempt in range(retry_count):
            try:
                # Start a timer to detect slow operations
                start_time = time.time()
                
                # Use a separate thread with timeout for network operations
                if is_network:
                    def scan_with_timeout():
                        try:
                            return list(scandir(path))
                        except Exception as e:
                            return e
                    
                    # Run scandir in a separate thread with timeout
                    with ThreadPoolExecutor(max_workers=1) as executor:
                        future = executor.submit(scan_with_timeout)
                        try:
                            result = future.result(timeout=timeout)
                            if isinstance(result, Exception):
                                raise result
                            entries = result
                        except (TimeoutError, concurrent.futures.TimeoutError):
                            print(f"Timeout scanning directory {path} after {timeout}s", file=sys.stderr)
                            # Continue to next retry attempt
                            time.sleep(0.5)  # Small delay before retry
                            continue
                else:
                    # For local paths, just do a direct scandir
                    entries = list(scandir(path))
                
                # Log slow operations for diagnostics
                elapsed = time.time() - start_time
                if elapsed > 2.0:  # Log slow directory access
                    print(f"Slow directory access: {path} took {elapsed:.2f}s", file=sys.stderr)
                
                # Filter entries
                return [e for e in entries if not self._should_skip(e.name)]
                
            except (OSError, PermissionError) as e:
                print(f"Cannot access directory {path}: {e}", file=sys.stderr)
                if attempt < retry_count - 1:
                    print(f"Retrying... (attempt {attempt+1}/{retry_count})", file=sys.stderr)
                    time.sleep(0.5)  # Small delay before retry
                    continue
                return []
            except Exception as e:
                print(f"Unexpected error scanning {path}: {e}", file=sys.stderr)
                return []
        
        # If we get here after all retries, return empty list
        return []

    def _crawl_threaded(
        self, root: str, max_files: int = None, max_workers: int = None
    ) -> Tuple[List[str], List[str]]:
        # Determine if root is on a network path
        is_network = self._is_network_path(root)
        
        # Adjust worker count based on path type
        if max_workers is None:
            max_workers = self.max_workers_network if is_network else self.max_workers_local
        
        print(
            f"Starting threaded crawl with {max_workers} workers {'(network path)' if is_network else '(local path)'}",
            file=sys.stderr,
        )
        
        # Create a cancel flag for long-running operations
        cancel_scan = threading.Event()
        start_time = time.time()
        last_progress_time = start_time
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(self._list_dir_safe, root)]
            file_paths = []
            dir_paths = [root]
            active_paths = set()  # Track directories being processed
            
            # Timeout for entire scan operation - 10 minutes for network, 5 minutes for local
            global_timeout = 600 if is_network else 300
            
            while futures and not cancel_scan.is_set():
                # Check if overall timeout has been reached
                if time.time() - start_time > global_timeout:
                    print(f"Scan timeout after {global_timeout}s, cancelling operation", file=sys.stderr)
                    for future in futures:
                        future.cancel()
                    break
                
                # Check progress rate
                current_time = time.time()
                if current_time - last_progress_time > 60:  # No progress for 1 minute
                    print(f"No scan progress for 60 seconds, adjusting scan parameters", file=sys.stderr)
                    # Reduce worker count to reduce load
                    max_workers = max(2, max_workers // 2)
                    print(f"Reducing worker count to {max_workers}", file=sys.stderr)
                    last_progress_time = current_time
                
                completed_futures = []
                for future in as_completed(futures, timeout=5.0):  # Short timeout to check cancel flag periodically
                    try:
                        entries = future.result(timeout=10.0)  # Timeout for individual results
                        completed_futures.append(future)
                        last_progress_time = time.time()  # Update progress time
                        
                        for entry in entries:
                            try:
                                if entry.is_dir(follow_symlinks=False):
                                    dir_path = entry.path
                                    if dir_path not in active_paths:  # Avoid duplicate processing
                                        dir_paths.append(dir_path)
                                        active_paths.add(dir_path)
                                        # Submit with priority handling - deeper paths get lower priority
                                        depth = dir_path.count(os.sep)
                                        # Use a limited queue size to prevent overwhelming the executor
                                        if len(futures) - len(completed_futures) < max_workers * 3:
                                            futures.append(
                                                executor.submit(self._list_dir_safe, dir_path)
                                            )
                                else:
                                    file_paths.append(entry.path)
                                    if len(file_paths) % 1000 == 0:
                                        print(
                                            f"Threaded scan progress: {len(file_paths)} files found...",
                                            file=sys.stderr,
                                        )
                                        last_progress_time = time.time()  # Update progress time
                            except (OSError, PermissionError) as e:
                                print(f"Error accessing {entry.path}: {e}", file=sys.stderr)
                                continue
                            except Exception as e:
                                print(f"Unexpected error with {entry.path}: {e}", file=sys.stderr)
                                continue
                                
                            # Check if we've reached the file limit
                            if max_files and len(file_paths) >= max_files:
                                print(f"Reached file limit of {max_files}", file=sys.stderr)
                                cancel_scan.set()
                                break
                    except (TimeoutError, concurrent.futures.TimeoutError):
                        print(f"Timeout waiting for directory scan results", file=sys.stderr)
                        # Don't mark as completed, will retry
                        continue
                    except Exception as e:
                        print(f"Error in crawl_threaded: {e}", file=sys.stderr)
                        completed_futures.append(future)
                
                # Remove completed futures
                for future in completed_futures:
                    try:
                        futures.remove(future)
                    except ValueError:
                        pass  # Future might have been removed already
                        
                # Progress update
                if len(file_paths) % 5000 == 0 and file_paths:
                    elapsed = time.time() - start_time
                    rate = len(file_paths) / elapsed if elapsed > 0 else 0
                    print(f"Scan stats: {len(file_paths)} files, {len(dir_paths)} dirs, {rate:.1f} files/sec", file=sys.stderr)
        
        print(
            f"Threaded crawl completed: {len(file_paths)} files, {len(dir_paths)} directories",
            file=sys.stderr,
        )
        return file_paths, dir_paths

    def _build_tree_threaded(self, path: Path, max_files: int = None) -> Dict[str, Any]:
        print(
            f"Using threaded scandir for optimal network performance", file=sys.stderr
        )
        try:
            # Check if path is on network drive
            is_network = self._is_network_path(str(path))
            max_workers = self.max_workers_network if is_network else self.max_workers_local
            
            # Log information about the scan
            print(f"Starting scan of {'network' if is_network else 'local'} path: {path}", file=sys.stderr)
            if is_network:
                print(f"Using reduced thread count ({max_workers}) and timeouts for network path", file=sys.stderr)
            
            # Use the improved crawl_threaded method
            file_paths, dir_paths = self._crawl_threaded(
                str(path), max_files=max_files, max_workers=max_workers
            )
            
            # Convert paths to Path objects
            files = [Path(fp) for fp in file_paths]
            dirs = [Path(dp) for dp in dir_paths]
            self.file_count = len(files)
            self.folder_count = len(dir_paths)
            
            # Build tree from collected files
            print(f"Building tree from {len(files)} files, {len(dirs)} directories...", file=sys.stderr)
            return self._build_tree_from_files(path, files, folders_only=True, directories=dirs)
        except Exception as e:
            print(
                f"Threaded scan failed: {e}, falling back to standard scan",
                file=sys.stderr,
            )
            return self._build_tree_optimized(path, max_files=max_files)

    def _has_fast_tools(self) -> bool:
        if shutil.which("fd"):
            return True
        if shutil.which("find"):
            return True
        if os.name == "nt" and shutil.which("powershell"):
            return True
        return False

    def _build_tree_fast(self, path: Path, max_files: int = 10000) -> Dict[str, Any]:
        print(f"Using fast scan with native tools", file=sys.stderr)
        if shutil.which("fd"):
            return self._scan_with_fd(path, max_files)
        elif shutil.which("find"):
            return self._scan_with_find(path, max_files)
        elif os.name == "nt" and shutil.which("powershell"):
            return self._scan_with_powershell(path, max_files)
        else:
            return self._build_tree_optimized(path, max_files=max_files)

    def _scan_with_fd(self, path: Path, max_files: int) -> Dict[str, Any]:
        try:
            print(f"Scanning with fd tool...", file=sys.stderr)
            cmd = ["fd", "--type", "f", "--threads", "0", ".", str(path)]
            proc = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            )
            files = []
            for line in proc.stdout:
                if self.file_count >= max_files:
                    proc.terminate()
                    break
                file_path = line.strip()
                if file_path and not self._should_skip_path(file_path):
                    files.append(Path(file_path))
                    self.file_count += 1
                    if self.file_count % 1000 == 0:
                        print(
                            f"Fast scan progress: {self.file_count} files found...",
                            file=sys.stderr,
                        )
            proc.wait()
            return self._build_tree_from_files(path, files, folders_only=True)
        except Exception as e:
            print(
                f"fd scan failed: {e}, falling back to threaded scan", file=sys.stderr
            )
            return self._build_tree_threaded(path, max_files=max_files)

    def _scan_with_find(self, path: Path, max_files: int) -> Dict[str, Any]:
        try:
            print(f"Scanning with find command...", file=sys.stderr)
            cmd = ["find", str(path), "-type", "f"]
            proc = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            )
            files = []
            for line in proc.stdout:
                if self.file_count >= max_files:
                    proc.terminate()
                    break
                file_path = line.strip()
                if file_path and not self._should_skip_path(file_path):
                    files.append(Path(file_path))
                    self.file_count += 1
                    if self.file_count % 1000 == 0:
                        print(
                            f"Fast scan progress: {self.file_count} files found...",
                            file=sys.stderr,
                        )
            proc.wait()
            return self._build_tree_from_files(path, files, folders_only=True)
        except Exception as e:
            print(
                f"find scan failed: {e}, falling back to threaded scan", file=sys.stderr
            )
            return self._build_tree_threaded(path, max_files=max_files)

    def _scan_with_powershell(self, path: Path, max_files: int) -> Dict[str, Any]:
        try:
            print(f"Scanning with PowerShell...", file=sys.stderr)
            cmd = [
                "powershell",
                "-Command",
                f'Get-ChildItem -Path "{str(path)}" -Recurse -File | ForEach-Object {{ $_.FullName }}',
            ]
            proc = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            )
            files = []
            for line in proc.stdout:
                if self.file_count >= max_files:
                    proc.terminate()
                    break
                file_path = line.strip()
                if file_path and not self._should_skip_path(file_path):
                    files.append(Path(file_path))
                    self.file_count += 1
                    if self.file_count % 1000 == 0:
                        print(
                            f"Fast scan progress: {self.file_count} files found...",
                            file=sys.stderr,
                        )
            proc.wait()
            return self._build_tree_from_files(path, files, folders_only=True)
        except Exception as e:
            print(
                f"PowerShell scan failed: {e}, falling back to threaded scan",
                file=sys.stderr,
            )
            return self._build_tree_threaded(path, max_files=max_files)

    def _should_skip_path(self, file_path: str) -> bool:
        path_parts = file_path.split(os.sep)
        for part in path_parts:
            if self._should_skip(part):
                return True
        return False

    def _build_tree_from_files(
        self, root_path: Path, files: List[Path], folders_only: bool = False, directories: List[Path] = None
    ) -> Dict[str, Any]:
        print(f"Building tree structure from {len(files)} files...", file=sys.stderr)
        tree = {
            "name": root_path.name,
            "path": str(root_path),
            "type": "folder",
            "children": [],
        }
        
        # Always store the complete file list for mapping generation
        tree["_all_files"] = [str(f) for f in files]
        
        # For very large file sets, process in batches to avoid memory issues
        batch_size = 10000
        is_network = self._is_network_path(str(root_path))
        
        dir_structure = {}
        total_files = len(files)
        progress_interval = max(1, min(1000, total_files // 20))  # Report progress at 5% intervals
        
        # Process files in batches
        for i, file_path in enumerate(files):
            # Report progress periodically
            if i % progress_interval == 0:
                print(f"Building tree: processed {i}/{total_files} files ({i/total_files*100:.1f}%)...", file=sys.stderr)
                
            try:
                # Use a try-except with timeout for network paths
                if is_network:
                    try:
                        rel_path = file_path.relative_to(root_path)
                    except Exception as e:
                        print(f"Error getting relative path for {file_path}: {e}", file=sys.stderr)
                        continue
                else:
                    rel_path = file_path.relative_to(root_path)
                    
                parts = rel_path.parts
                current_dict = dir_structure
                
                # Process directory structure
                for i, part in enumerate(parts[:-1]):
                    if part not in current_dict:
                        current_dict[part] = {"files": [], "dirs": {}}
                    current_dict = current_dict[part]["dirs"]
                    
                # Handle file placement
                if len(parts) > 1:
                    parent_dir = parts[-2]
                    if parent_dir not in current_dict:
                        current_dict[parent_dir] = {"files": [], "dirs": {}}
                    current_dict[parent_dir]["files"].append(file_path)
                else:
                    if "root_files" not in dir_structure:
                        dir_structure["root_files"] = []
                    dir_structure["root_files"].append(file_path)
            except Exception as e:
                print(f"Error processing file {file_path}: {e}", file=sys.stderr)
                continue
        
        # Build the final tree structure
        print(f"Converting directory structure to tree...", file=sys.stderr)
        tree["children"] = self._convert_structure_to_tree(
            dir_structure, root_path, self.tree_max_depth, folders_only
        )
        self.folder_count = self._count_folders(tree)
        print(f"Tree structure built successfully with {self.folder_count} folders", file=sys.stderr)
        return tree

    def _convert_structure_to_tree(
        self, structure: Dict, base_path: Path, max_depth: int = 10, folders_only: bool = False
    ) -> List[Dict]:
        children = []
        is_network = self._is_network_path(str(base_path))
        
        # Include root files only if not folders_only mode
        if "root_files" in structure and not folders_only:
            for file_path in structure["root_files"]:
                try:
                    # For network paths, use a more robust stat approach with timeout handling
                    if is_network:
                        try:
                            # Just get basic info without heavy stat calls for network paths
                            children.append(
                                {
                                    "name": file_path.name,
                                    "path": str(file_path),
                                    "type": "file",
                                    "size": 0,  # Skip size calculation for network performance
                                    "extension": file_path.suffix.lower(),
                                }
                            )
                        except Exception as e:
                            print(f"Network file error (skipping): {e}", file=sys.stderr)
                            continue
                    else:
                        # For local paths, get full stat info
                        stat_info = file_path.stat()
                        children.append(
                            {
                                "name": file_path.name,
                                "path": str(file_path),
                                "type": "file",
                                "size": stat_info.st_size,
                                "extension": file_path.suffix.lower(),
                            }
                        )
                except Exception:
                    continue
        
        if max_depth > 0:
            # Process directories with progress reporting for large sets
            dir_count = sum(1 for k in structure.keys() if k != "root_files")
            if dir_count > 100:
                print(f"Processing {dir_count} directories in tree structure...", file=sys.stderr)
            
            for i, (dir_name, dir_data) in enumerate(structure.items()):
                if dir_name == "root_files":
                    continue
                    
                # Report progress for large directory sets
                if dir_count > 100 and i % 50 == 0:
                    print(f"Tree conversion progress: {i}/{dir_count} directories", file=sys.stderr)
                    
                dir_path = base_path / dir_name
                dir_node = {"name": dir_name, "path": str(dir_path), "type": "folder"}
                dir_children = []
                
                # Include files in this directory only if not folders_only mode
                if not folders_only:
                    for file_path in dir_data["files"]:
                        try:
                            # Use the same network-aware approach for files in directories
                            if is_network:
                                dir_children.append(
                                    {
                                        "name": file_path.name,
                                        "path": str(file_path),
                                        "type": "file",
                                        "size": 0,  # Skip size calculation for network performance
                                        "extension": file_path.suffix.lower(),
                                    }
                                )
                            else:
                                stat_info = file_path.stat()
                                dir_children.append(
                                    {
                                        "name": file_path.name,
                                        "path": str(file_path),
                                        "type": "file",
                                        "size": stat_info.st_size,
                                        "extension": file_path.suffix.lower(),
                                    }
                                )
                        except Exception:
                            continue
                
                # Recursively process subdirectories
                if dir_data["dirs"] and max_depth > 1:
                    dir_children.extend(
                        self._convert_structure_to_tree(
                            dir_data["dirs"], dir_path, max_depth - 1, folders_only
                        )
                    )
                
                # In folders_only mode, include all folders even if they appear empty in the tree
                # In normal mode, only include folders that have children
                if folders_only or dir_children:
                    if dir_children:
                        dir_node["children"] = dir_children
                    children.append(dir_node)
        return children

    def _count_folders(self, tree: Dict) -> int:
        count = 1 if tree["type"] == "folder" else 0
        for child in tree.get("children", []):
            count += self._count_folders(child)
        return count

    def _should_skip(self, name: str) -> bool:
        for pattern in self.skip_patterns:
            if re.match(pattern, name):
                return True
        return False

    def _build_tree_optimized(
        self, path: Path, depth: int = 0, max_files: int = None
    ) -> Dict[str, Any]:
        if max_files and self.file_count >= max_files:
            return None
        if depth > self.max_depth:
            return None
        name = path.name
        if self._should_skip(name):
            return None
        node = {
            "name": name,
            "path": str(path),
            "type": "folder" if path.is_dir() else "file",
        }
        if path.is_file():
            try:
                stat_info = path.stat()
                node["size"] = stat_info.st_size
                node["extension"] = path.suffix.lower()
                self.file_count += 1
                if self.file_count % 1000 == 0:
                    print(
                        f"Progress: {self.file_count} files scanned...", file=sys.stderr
                    )
            except (OSError, PermissionError):
                return None
            return node
        self.folder_count += 1
        children = []
        try:
            with os.scandir(path) as entries:
                entry_list = list(entries)
                entry_list.sort(key=lambda e: e.name)
                for entry in entry_list:
                    if max_files and self.file_count >= max_files:
                        print(
                            f"Reached file limit of {max_files}, stopping scan",
                            file=sys.stderr,
                        )
                        break
                    if self._should_skip(entry.name):
                        continue
                    try:
                        child_path = Path(entry.path)
                        child_node = self._build_tree_optimized(
                            child_path, depth + 1, max_files
                        )
                        if child_node:
                            children.append(child_node)
                    except (OSError, PermissionError):
                        continue
        except (OSError, PermissionError):
            pass
        if children:
            node["children"] = children
        return node

# --- TEST CODE FOR SCANNER ---
if __name__ == "__main__":
    import os
    print("[TEST][scanner.py] Initializing FileSystemScanner...")
    # Ensure progress_server is running independently for WebSocket updates.
    # This __main__ block will test the scanning logic and its calls to send_progress_update.
    
    scanner = FileSystemScanner()
    
    # Determine the path to the '_progress' directory relative to this script's location
    # This script is in 'python/', so '_progress' is a sibling directory.
    current_script_dir = os.path.dirname(os.path.abspath(__file__))
    # Target directory for scanning is 'python/_progress/'
    test_scan_path = os.path.join(current_script_dir, "_progress")

    print(f"[TEST][scanner.py] Test scan path resolved to: {test_scan_path}")

    if not os.path.exists(test_scan_path):
        print(f"[TEST][scanner.py] Test scan path {test_scan_path} does not exist. Creating it for the test.")
        os.makedirs(test_scan_path, exist_ok=True)
        # Optionally, create a dummy file in it
        with open(os.path.join(test_scan_path, "dummy_for_scan_test.txt"), "w") as f:
            f.write("test content")

    print(f"[TEST][scanner.py] Starting scan on directory: {test_scan_path}")
    try:
        # Scan the local '_progress' directory. It should be small.
        # max_files can be small for this test.
        batch_id_from_scan = scanner.scan_directory_with_progress(test_scan_path, max_files=50, use_fast_scan=False)
        print(f"[TEST][scanner.py] Scan initiated. Batch ID: {batch_id_from_scan}")
        
        # The scan runs, and progress updates should be sent via WebSocket if server is active.
        # We might not see the "completed" status here immediately if the scan is very fast 
        # and this script exits before all async operations fully flush.
        # The test_websocket_client.py is responsible for catching the updates.

        # Give a moment for any final async messages to be processed by the server if it's running
        import time
        time.sleep(2) # Wait for 2 seconds
        print(f"[TEST][scanner.py] Scan test in scanner.py finished for batch_id: {batch_id_from_scan}.")

    except Exception as e:
        print(f"[TEST][scanner.py] Error during scan test: {e}")
        import traceback
        traceback.print_exc()
