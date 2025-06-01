"""
Tree Manager Module - PyQt5 Compatible

Handles tree population and management functionality
for the Clean Incomings GUI application.
"""

import os
from typing import List, Dict, Any, Optional
from pathlib import Path
from PyQt5.QtWidgets import QTreeWidgetItem
from PyQt5.QtCore import Qt


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
        """Clear folder-based filtering."""
        print(f"[TREE_MANAGER_DEBUG] Clearing source folder filter")
        self.selected_source_folder = None
        self._refresh_preview_tree()

    def populate_source_tree(self, tree_data: List[Dict[str, Any]], base_path: str):
        """
        Populate the source tree with file/folder structure.
        
        Args:
            tree_data: List of tree node dictionaries
            base_path: Base path for the tree
        """
        if not hasattr(self.app, 'source_tree'):
            print("Source tree widget not available")
            return
            
        try:
            # Clear existing items
            self.app.source_tree.clear()
            
            if not tree_data:
                print("No tree data to populate")
                return
            
            # Add root item
            root_item = QTreeWidgetItem(self.app.source_tree)
            root_item.setText(0, os.path.basename(base_path) or base_path)
            root_item.setText(1, "Folder")
            root_item.setText(2, "")
            
            # Populate children recursively
            self._populate_tree_recursive(root_item, tree_data)
            
            # Expand the root
            root_item.setExpanded(True)
            
            print(f"Populated source tree with {len(tree_data)} items")
            
        except Exception as e:
            print(f"Error populating source tree: {e}")
            import traceback
            traceback.print_exc()

    def _populate_tree_recursive(self, parent_item: QTreeWidgetItem, children: List[Dict[str, Any]]):
        """Recursively populate tree items."""
        for child_data in children:
            try:
                child_item = QTreeWidgetItem(parent_item)
                
                # Set basic info
                name = child_data.get('name', 'Unknown')
                node_type = child_data.get('type', 'Unknown')
                size = child_data.get('size_str', '')
                
                child_item.setText(0, name)
                child_item.setText(1, node_type)
                child_item.setText(2, size)
                
                # Store full data as user data
                child_item.setData(0, Qt.UserRole, child_data)
                
                # Add children if any
                if 'children' in child_data and child_data['children']:
                    self._populate_tree_recursive(child_item, child_data['children'])
                    
            except Exception as e:
                print(f"Error adding tree item: {e}")

    def populate_preview_tree(self, proposals: List[Dict[str, Any]], base_path: str):
        """
        Populate the preview tree with normalized proposals.
        
        Args:
            proposals: List of normalized proposal dictionaries
            base_path: Base path for proposals
        """
        if not hasattr(self.app, 'preview_tree'):
            print("Preview tree widget not available")
            return
            
        try:
            # Store original data for filtering/sorting
            self.original_data = proposals.copy()
            
            # Clear existing items
            self.app.preview_tree.clear()
            
            if not proposals:
                print("No proposals to populate")
                return
            
            # Create tree items
            for i, proposal in enumerate(proposals):
                try:
                    item = QTreeWidgetItem(self.app.preview_tree)
                    
                    # Extract data from proposal
                    source_path = proposal.get('source_path', '')
                    filename = os.path.basename(source_path) if source_path else 'Unknown'
                    task = proposal.get('task', '')
                    asset = proposal.get('asset', '')
                    dest_path = proposal.get('destination_path', '')
                    matched_tags = ', '.join(proposal.get('matched_tags', []))
                    
                    # Set checkbox (unchecked by default)
                    item.setCheckState(0, Qt.Unchecked)
                    
                    # Set text for columns
                    item.setText(1, filename)
                    item.setText(2, task)
                    item.setText(3, asset)
                    item.setText(4, dest_path)
                    item.setText(5, matched_tags)
                    
                    # Store full proposal data
                    item.setData(0, Qt.UserRole, proposal)
                    
                    # Store item mapping for quick access
                    if hasattr(self.app, 'preview_tree_item_data_map'):
                        item_id = f"item_{i}"
                        self.app.preview_tree_item_data_map[item_id] = proposal
                        item.setData(1, Qt.UserRole, item_id)
                    
                except Exception as e:
                    print(f"Error adding preview item {i}: {e}")
            
            print(f"Populated preview tree with {len(proposals)} proposals")
            
            # Update selection stats
            self.update_selection_stats()
            
        except Exception as e:
            print(f"Error populating preview tree: {e}")
            import traceback
            traceback.print_exc()

    def _refresh_preview_tree(self):
        """Refresh the preview tree with current filter/sort settings."""
        if not self.original_data:
            return
            
        # Apply filtering
        filtered_data = self._apply_filter(self.original_data)
        
        # Apply sorting
        sorted_data = self._apply_sort(filtered_data)
        
        # Re-populate with filtered/sorted data
        base_path = self.app.selected_source_folder.get() if hasattr(self.app, 'selected_source_folder') else ""
        self.populate_preview_tree(sorted_data, base_path)

    def _apply_filter(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Apply current filter to data."""
        if self.current_filter == "all":
            return data
        elif self.current_filter == "sequences":
            return [item for item in data if item.get('type') == 'Sequence']
        elif self.current_filter == "files":
            return [item for item in data if item.get('type') != 'Sequence']
        else:
            return data

    def _apply_sort(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Apply current sort to data."""
        sort_key_map = {
            "filename": lambda x: os.path.basename(x.get('source_path', '')).lower(),
            "task": lambda x: x.get('task', '').lower(),
            "asset": lambda x: x.get('asset', '').lower(),
            "destination": lambda x: x.get('destination_path', '').lower(),
            "type": lambda x: x.get('type', '').lower()
        }
        
        sort_key = sort_key_map.get(self.current_sort_column.lower(), sort_key_map["filename"])
        
        try:
            return sorted(data, key=sort_key, reverse=self.sort_reverse)
        except Exception as e:
            print(f"Error sorting data: {e}")
            return data

    def get_selected_items(self) -> List[Dict[str, Any]]:
        """Get list of selected (checked) items from preview tree."""
        selected_items = []
        
        if not hasattr(self.app, 'preview_tree'):
            return selected_items
            
        try:
            root = self.app.preview_tree.invisibleRootItem()
            for i in range(root.childCount()):
                item = root.child(i)
                if item.checkState(0) == Qt.Checked:
                    proposal_data = item.data(0, Qt.UserRole)
                    if proposal_data:
                        selected_items.append(proposal_data)
                        
        except Exception as e:
            print(f"Error getting selected items: {e}")
            
        return selected_items

    def select_all_items(self, item_type: str = "all"):
        """Select all items of specified type."""
        if not hasattr(self.app, 'preview_tree'):
            return
            
        try:
            root = self.app.preview_tree.invisibleRootItem()
            for i in range(root.childCount()):
                item = root.child(i)
                proposal_data = item.data(0, Qt.UserRole)
                
                should_select = False
                if item_type == "all":
                    should_select = True
                elif item_type == "sequences" and proposal_data and proposal_data.get('type') == 'Sequence':
                    should_select = True
                elif item_type == "files" and proposal_data and proposal_data.get('type') != 'Sequence':
                    should_select = True
                    
                if should_select:
                    item.setCheckState(0, Qt.Checked)
                    
            self.update_selection_stats()
            
        except Exception as e:
            print(f"Error selecting items: {e}")

    def clear_selection(self):
        """Clear all selections."""
        if not hasattr(self.app, 'preview_tree'):
            return
            
        try:
            root = self.app.preview_tree.invisibleRootItem()
            for i in range(root.childCount()):
                item = root.child(i)
                item.setCheckState(0, Qt.Unchecked)
                
            self.update_selection_stats()
            
        except Exception as e:
            print(f"Error clearing selection: {e}")

    def update_selection_stats(self):
        """Update selection statistics display."""
        selected_count = len(self.get_selected_items())
        total_count = 0
        
        if hasattr(self.app, 'preview_tree'):
            root = self.app.preview_tree.invisibleRootItem()
            total_count = root.childCount()
            
        stats_text = f"Selected: {selected_count} of {total_count} items"
        
        if hasattr(self.app, 'selection_stats_label'):
            self.app.selection_stats_label.setText(stats_text)

    def on_tree_item_selection_changed(self):
        """Handle tree item selection changes."""
        self.update_selection_stats()
        
        # Enable/disable action buttons based on selection
        has_selection = len(self.get_selected_items()) > 0
        
        if hasattr(self.app, 'copy_selected_btn'):
            self.app.copy_selected_btn.setEnabled(has_selection)
        if hasattr(self.app, 'move_selected_btn'):
            self.app.move_selected_btn.setEnabled(has_selection)
        if hasattr(self.app, 'batch_edit_btn'):
            self.app.batch_edit_btn.setEnabled(has_selection)
