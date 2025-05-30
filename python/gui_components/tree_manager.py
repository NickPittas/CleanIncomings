"""
Tree Manager Module

Handles tree population and management functionality
for the Clean Incomings GUI application.
Enhanced with sorting, filtering, and batch editing capabilities.
"""

import os
import tkinter as tk
from typing import List, Dict, Any, Optional
from pathlib import Path
import uuid


class TreeManager:
    """Manages tree views and their population for the GUI."""
    
    def __init__(self, app_instance):
        """
        Initialize the TreeManager.
        
        Args:
            app_instance: Reference to the main application instance
        """
        self.app = app_instance
        self.current_sort_column = "filename"
        self.sort_reverse = False
        self.current_filter = "all"  # all, sequences, files
        self.selected_source_folder = None  # For folder-based filtering
        self.original_data = []  # Store original data for filtering/sorting
        
    def set_sort_order(self, column: str, reverse: bool = False):
        """Set the sort order for the preview tree."""
        self.current_sort_column = column
        self.sort_reverse = reverse
        self._refresh_preview_tree()
    
    def set_filter(self, filter_type: str):
        """Set the filter for the preview tree."""
        print(f"[TREE_MANAGER_DEBUG] Setting filter from '{self.current_filter}' to '{filter_type}'")
        self.current_filter = filter_type
        self._refresh_preview_tree()
        
    def set_source_folder_filter(self, folder_path: Optional[str]):
        """Set folder-based filtering from source tree selection."""
        print(f"[TREE_MANAGER_DEBUG] Setting source folder filter: {folder_path}")
        self.selected_source_folder = folder_path
        self._refresh_preview_tree()
        
    def clear_source_folder_filter(self):
        """Clear folder-based filtering to show all sequences."""
        print(f"[TREE_MANAGER_DEBUG] Clearing source folder filter")
        self.selected_source_folder = None
        self._refresh_preview_tree()
    
    def _sort_data(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Sort data based on current sort settings."""
        def get_sort_key(item):
            if self.current_sort_column == "filename":
                return item.get('filename', '').lower()
            elif self.current_sort_column == "task":
                return item.get('normalized_parts', {}).get('task', '').lower()
            elif self.current_sort_column == "asset":
                return item.get('normalized_parts', {}).get('asset', '').lower()
            elif self.current_sort_column == "destination":
                return item.get('new_destination_path', '').lower()
            elif self.current_sort_column == "type":
                return item.get('type', 'file').lower()
            else:
                return item.get('filename', '').lower()
        
        return sorted(data, key=get_sort_key, reverse=self.sort_reverse)
    
    def _filter_data(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter data based on current filter settings."""
        print(f"[TREE_MANAGER_DEBUG] Filtering {len(data)} items with filter='{self.current_filter}', folder='{self.selected_source_folder}'")
        
        # Start with all data
        filtered_data = data.copy()
        
        # Apply type filter (sequences, files, or all)
        if self.current_filter == "sequences":
            filtered_data = [item for item in filtered_data if item.get('type', '').lower() == 'sequence']
        elif self.current_filter == "files":
            filtered_data = [item for item in filtered_data if item.get('type', '').lower() == 'file']
        # For 'all', keep everything
        
        # Apply folder-based filter if a source folder is selected
        if self.selected_source_folder:
            folder_filtered = []
            for item in filtered_data:
                source_path = item.get('source_path', '')
                # Check if the item's source path is within the selected folder
                if source_path and source_path.startswith(self.selected_source_folder):
                    folder_filtered.append(item)
            filtered_data = folder_filtered
        
        print(f"[TREE_MANAGER_DEBUG] After filtering: {len(filtered_data)} items")
        return filtered_data
    
    def _refresh_preview_tree(self):
        """Refresh the preview tree with current sort and filter settings."""
        if not self.original_data:
            print(f"[TREE_MANAGER_DEBUG] No original data to refresh")
            return
        
        print(f"[TREE_MANAGER_DEBUG] Refreshing preview tree with {len(self.original_data)} original items")
        
        # Apply filter then sort
        filtered_data = self._filter_data(self.original_data)
        sorted_data = self._sort_data(filtered_data)
        
        # Repopulate tree
        self._populate_preview_tree_internal(sorted_data)

    def populate_source_tree(self, items: List[Dict[str, Any]], base_path: str):
        """Populates the source_tree with scanned items."""
        # Clear existing items
        for i in self.app.source_tree.get_children():
            self.app.source_tree.delete(i)

        if not items:
            self.app.source_tree.insert("", "end", text="No items found or directory is empty.", values=("", ""))
            return

        # Sort items: folders first, then files, then by name. Use .get() for safety.
        items.sort(key=lambda x: (x.get('type', 'file') != 'folder', x.get('name', 'Unnamed Item').lower()))

        # Helper function to insert items recursively
        def insert_items_recursively(parent_node_id, current_items):
            current_items.sort(key=lambda x: (x.get('type', 'file') != 'folder', x.get('name', 'Unnamed Item').lower()))
            for item_data in current_items:
                name = item_data.get('name', 'Unnamed Item')
                item_type_cap = item_data.get('type', 'file').capitalize()
                size_bytes = item_data.get('size')
                path = item_data.get('path')

                if not path:
                    self.app.status_manager.add_log_message(f"Item missing 'path' in recursive insert, cannot add to source tree: {item_data}", "WARNING")
                    continue

                if isinstance(size_bytes, (int, float)):
                    if size_bytes < 1024:
                        size_display = f"{size_bytes} B"
                    elif size_bytes < 1024**2:
                        size_display = f"{size_bytes/1024:.1f} KB"
                    elif size_bytes < 1024**3:
                        size_display = f"{size_bytes/1024**2:.1f} MB"
                    else:
                        size_display = f"{size_bytes/1024**3:.1f} GB"
                else:
                    size_display = "N/A" if item_type_cap == "Folder" else ""
                
                if item_data.get('type') == 'folder':
                    # Only insert and process children if the item is a folder
                    node_id = self.app.source_tree.insert(parent_node_id, "end", iid=path, text=name, values=(item_type_cap, size_display), open=False)
                    
                    if 'children' in item_data and item_data['children']:
                        # If it's a folder and has children, recursively insert them
                        if not isinstance(item_data['children'], dict) or 'error' not in item_data['children']:
                            insert_items_recursively(node_id, item_data['children'])
                        elif isinstance(item_data['children'], dict) and 'error' in item_data['children']:
                            # Optionally, insert an error node for this folder
                            self.app.source_tree.insert(node_id, "end", text=f"Error scanning: {item_data['children']['error']}", values=("Error", ""))
                # Files are intentionally skipped for display in the source_tree

        # Start recursive insertion from the root of the treeview (parent_node_id = "")
        self.app.status_manager.add_log_message(f"Initiating recursive insertion into source tree for {len(items) if items else 0} items.", "DEBUG")
        insert_items_recursively("", items)
        self.app.status_manager.add_log_message(f"Finished populating source tree.", "DEBUG")

    def on_source_tree_selection(self, event=None):
        """Handle source tree selection for folder-based filtering."""
        selection = self.app.source_tree.selection()
        if selection:
            # Get the selected folder path
            selected_folder = selection[0]  # The iid is the folder path
            print(f"[TREE_MANAGER_DEBUG] Source tree selection: {selected_folder}")
            self.set_source_folder_filter(selected_folder)
        else:
            # No selection - clear filter
            self.clear_source_folder_filter()

    def populate_preview_tree(self, normalized_file_list: List[Dict[str, Any]], source_path_base: str):
        """Populates the preview_tree with the flat list of normalized file/sequence data."""
        if not hasattr(self.app, 'preview_tree'):
            print("Preview tree not available.")
            return

        if not normalized_file_list:
            self.app.status_label.configure(text="No files/sequences found or processed.")
            print("No data for preview tree.")
            return

        # Store original data and populate using internal method
        self.original_data = normalized_file_list
        self._populate_preview_tree_internal(normalized_file_list)

        self.app.status_label.configure(text=f"Preview populated with {len(normalized_file_list)} items from {os.path.basename(source_path_base)}.")
        print(f"Preview tree populated with {len(normalized_file_list)} items.")
        self.update_action_button_states()  # Update button states after populating tree

    def update_action_button_states(self, event=None):
        """Enable/disable copy/move buttons based on selection and destination folder."""
        has_selection = bool(self.app.preview_tree.selection())
        has_destination = bool(self.app.selected_destination_folder.get())
        buttons_state = tk.NORMAL if has_selection and has_destination else tk.DISABLED

        if hasattr(self.app, 'copy_selected_btn'):
            self.app.copy_selected_btn.configure(state=buttons_state)
        if hasattr(self.app, 'move_selected_btn'):
            self.app.move_selected_btn.configure(state=buttons_state)

    def get_selected_items(self) -> List[Dict[str, Any]]:
        """Get data for selected items in the preview tree."""
        selected_tree_item_ids = self.app.preview_tree.selection()
        if not selected_tree_item_ids:
            return []

        items_to_process = []
        for tree_item_id in selected_tree_item_ids:
            if hasattr(self.app, 'preview_tree_item_data_map') and tree_item_id in self.app.preview_tree_item_data_map:
                item_data = self.app.preview_tree_item_data_map[tree_item_id]
                items_to_process.append(item_data)
            else:
                self.app.status_manager.add_log_message(f"Data not found for selected tree item ID: {tree_item_id}", "WARNING")
        
        return items_to_process

    def sort_by_column(self, column: str):
        """Sort by clicking column header."""
        # If clicking the same column, toggle direction
        if self.current_sort_column == column:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_reverse = False
        
        self.set_sort_order(column, self.sort_reverse)
        
        # Update UI indicators if available
        if hasattr(self.app, 'sort_combo'):
            column_display_map = {
                "filename": "Filename",
                "task": "Task",
                "asset": "Asset", 
                "destination": "Destination",
                "type": "Type"
            }
            display_name = column_display_map.get(column, "Filename")
            self.app.sort_combo.set(display_name)
            
        if hasattr(self.app, 'sort_direction_btn'):
            self.app.sort_direction_btn.configure(text="↓" if self.sort_reverse else "↑")

    def select_all_sequences(self):
        """Select all sequence items in the preview tree."""
        if not hasattr(self.app, 'preview_tree'):
            return
        
        # Clear current selection
        self.app.preview_tree.selection_remove(self.app.preview_tree.selection())
        
        # Select all sequence items
        for item_id in self.app.preview_tree.get_children():
            if hasattr(self.app, 'preview_tree_item_data_map') and item_id in self.app.preview_tree_item_data_map:
                item_data = self.app.preview_tree_item_data_map[item_id]
                if item_data.get('type', '').lower() == 'sequence':
                    self.app.preview_tree.selection_add(item_id)

    def select_all_files(self):
        """Select all individual file items in the preview tree."""
        if not hasattr(self.app, 'preview_tree'):
            return
        
        # Clear current selection
        self.app.preview_tree.selection_remove(self.app.preview_tree.selection())
        
        # Select all file items
        for item_id in self.app.preview_tree.get_children():
            if hasattr(self.app, 'preview_tree_item_data_map') and item_id in self.app.preview_tree_item_data_map:
                item_data = self.app.preview_tree_item_data_map[item_id]
                if item_data.get('type', '').lower() == 'file':
                    self.app.preview_tree.selection_add(item_id)

    def clear_selection(self):
        """Clear all selections in the preview tree."""
        if not hasattr(self.app, 'preview_tree'):
            return
        
        self.app.preview_tree.selection_remove(self.app.preview_tree.selection())

    def get_selection_stats(self) -> Dict[str, int]:
        """Get statistics about the current selection."""
        selected_items = self.get_selected_items()
        
        stats = {
            'total': len(selected_items),
            'sequences': 0,
            'files': 0,
            'auto_mapped': 0,
            'manual_required': 0
        }
        
        for item in selected_items:
            item_type = item.get('type', 'file').lower()
            if item_type == 'sequence':
                stats['sequences'] += 1
            else:
                stats['files'] += 1
            
            status = item.get('status', 'unknown')
            if status == 'auto':
                stats['auto_mapped'] += 1
            else:
                stats['manual_required'] += 1
        
        return stats

    def _populate_preview_tree_internal(self, data: List[Dict[str, Any]]):
        """Internal method to populate the preview tree with given data."""
        print(f"[TREE_MANAGER_DEBUG] Populating preview tree with {len(data)} items")
        
        # Clear existing items
        for i in self.app.preview_tree.get_children():
            self.app.preview_tree.delete(i)
        if hasattr(self.app, 'preview_tree_item_data_map'):
            self.app.preview_tree_item_data_map.clear()

        if not data:
            print(f"[TREE_MANAGER_DEBUG] No data to populate")
            return

        # Populate with the provided data
        for item_data in data:
            filename = item_data.get('filename', 'N/A')
            task = item_data.get('normalized_parts', {}).get('task', '')
            asset = item_data.get('normalized_parts', {}).get('asset', '')
            new_path = item_data.get('new_destination_path', '')
            tags_dict = item_data.get('matched_tags', {})
            
            # Format tags nicely - show key-value pairs
            if isinstance(tags_dict, dict) and tags_dict:
                tags = ", ".join([f"{k}:{v}" for k, v in tags_dict.items() if v])
            else:
                tags = ""
            
            original_path = item_data.get('source_path', '')
            item_id = item_data.get('id', original_path)
            status = item_data.get('status', 'unknown')
            error_msg = item_data.get('error_message')

            # Customize appearance based on status
            tag_list_for_style = []
            if status == 'error' or error_msg:
                tag_list_for_style.append('error')
                tags = f"ERROR: {error_msg[:50]}{'...' if error_msg and len(error_msg) > 50 else ''}"
            elif status == 'manual':
                tag_list_for_style.append('manual')
            elif status == 'unmatched':
                tag_list_for_style.append('unmatched')
            
            # Insert into tree
            self.app.preview_tree.insert('', 'end', iid=item_id, text="☐", 
                                         values=(filename, task, asset, new_path, tags),
                                         tags=tuple(tag_list_for_style),
                                         open=False)
            if hasattr(self.app, 'preview_tree_item_data_map'):
                self.app.preview_tree_item_data_map[item_id] = item_data 
        
        print(f"[TREE_MANAGER_DEBUG] Preview tree populated with {len(data)} items") 