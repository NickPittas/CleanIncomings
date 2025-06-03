"""
Tree Manager Module - PyQt5 Compatible

Handles tree population and management functionality
for the Clean Incomings GUI application.
"""

import os
from typing import List, Dict, Any, Optional
from pathlib import Path
from PyQt5.QtWidgets import QTreeWidgetItem, QTreeWidget
from PyQt5.QtCore import Qt

# Column indices for the preview tree (ensure these match WidgetFactory setup)
COL_FILENAME = 0
COL_SIZE = 1
COL_TYPE = 2
COL_TASK = 3
COL_ASSET = 4
COL_VERSION = 5
COL_RESOLUTION = 6
COL_DEST_PATH = 7
COL_MATCHED_TAGS = 8  # Column for matched tags (must match header setup)
# If you update these, also update the preview tree widget headers in the UI accordingly.

class TreeManager:
    """Manages tree views and their population for the GUI."""
    
    def __init__(self, app_instance):
        self.app = app_instance
        self.current_sort_column_idx = COL_FILENAME  # Default sort
        self.sort_order = Qt.AscendingOrder  # Default sort order
        self.current_filter_text = "All"  # Default filter
        self.selected_source_folder_path: Optional[str] = None  # For folder-based filtering in preview

        # This will hold the comprehensive data for all items currently meant to be in the preview.
        # It's the source of truth for rebuilding the tree.
        self.master_item_data_list: List[Dict[str, Any]] = []
        
        # A map from item ID to its QTreeWidgetItem widget for quick lookups
        self._item_id_to_widget_map: Dict[str, QTreeWidgetItem] = {}

    def _clear_preview_tree_internal_state(self):
        """Clears internal state related to the preview tree items."""
        self.master_item_data_list.clear()
        self._item_id_to_widget_map.clear()
        if hasattr(self.app, 'preview_tree_item_data_map'):  # Clear app's map too if it exists
            self.app.preview_tree_item_data_map.clear()

    def populate_source_tree(self, items: List[Dict[str, Any]], base_path: str):
        """Populates the source_tree (QTreeWidget) with scanned directory items."""
        if not hasattr(self.app, 'source_tree'):
            self.app.logger.error("Source tree widget not found in app instance.")
            return

        self.app.source_tree.clear()
        # self.app.logger.debug(  # (Silenced for normal use. Re-enable for troubleshooting.)f"Source tree cleared. Populating with {len(items)} top-level items from base: {base_path}")

        if not items:
            placeholder_item = QTreeWidgetItem(self.app.source_tree)
            placeholder_item.setText(0, "No items found or directory is empty.")
            self.app.source_tree.addTopLevelItem(placeholder_item)
            return

        # Sort items: folders first, then by name
        items.sort(key=lambda x: (x.get('type', 'file') != 'folder', x.get('name', 'Unnamed Item').lower()))

        self._insert_source_items_recursively(self.app.source_tree, items)
        # # self.app.logger.debug(  # (Silenced for normal use. Re-enable for troubleshooting.)"Finished populating source tree.")  # (Silenced for normal use. Re-enable for troubleshooting.)

    def _insert_source_items_recursively(self, parent_widget_or_item, current_items: List[Dict[str, Any]]):
        """Helper to recursively insert items into the source tree."""
        current_items.sort(key=lambda x: (x.get('type', 'file') != 'folder', x.get('name', 'Unnamed Item').lower()))
        
        for item_data in current_items:
            name = item_data.get('name', 'Unnamed Item')
            item_type = item_data.get('type', 'file')
            item_path = item_data.get('path')
            size_bytes = item_data.get('size')

            if not item_path:
                self.app.logger.warning(f"Item missing 'path', cannot add to source tree: {item_data}")
                continue

            tree_item = QTreeWidgetItem()
            tree_item.setText(0, name)  # Name column
            tree_item.setData(0, Qt.UserRole, {'path': item_path, 'type': item_type})  # Store path and type

            icon_name = 'folder_closed' if item_type == 'folder' else self.app.normalizer.get_icon_name_for_file(name) if hasattr(self.app, 'normalizer') else 'file'
            if hasattr(self.app, 'widget_factory'):
                icon = self.app.widget_factory.get_icon(icon_name)
                if not icon.isNull():
                    tree_item.setIcon(0, icon)

            if item_type == 'folder':
                tree_item.setText(1, "Folder")  # Type column
                tree_item.setText(2, "N/A")    # Size column
                if isinstance(parent_widget_or_item, QTreeWidget):
                    parent_widget_or_item.addTopLevelItem(tree_item)
                else:  # It's a QTreeWidgetItem
                    parent_widget_or_item.addChild(tree_item)
                
                children = item_data.get('children')
                if children and isinstance(children, list):
                    self._insert_source_items_recursively(tree_item, children)
                elif children and isinstance(children, dict) and 'error' in children:
                    error_child_item = QTreeWidgetItem(tree_item)
                    error_child_item.setText(0, f"Error scanning: {children['error']}")
                    if hasattr(self.app, 'widget_factory'):
                         error_icon = self.app.widget_factory.get_icon('error')
                         if not error_icon.isNull():
                            error_child_item.setIcon(0, error_icon)
            else:  # It's a file, currently we don't add files to the source tree by default
                pass  # Files are not added to the source tree in this version

    def get_selected_items(self) -> List[Dict[str, Any]]:
        """
        Return a list of the most up-to-date item data dicts for all selected items in the preview tree.
        This ensures move/copy operations always use the latest values (including destination path, version, etc.).
        Returns:
            List[Dict[str, Any]]: List of item data dicts as stored in the preview tree selection.
        """
        selected_items = []
        if hasattr(self.app, 'preview_tree'):
            for item_widget in self.app.preview_tree.selectedItems():
                item_data = item_widget.data(0, Qt.UserRole)
                if item_data and isinstance(item_data, dict):
                    selected_items.append(item_data)
        return selected_items

    def _format_size(self, size_bytes: Optional[Any]) -> str:
        """Formats byte size into a human-readable string."""
        if isinstance(size_bytes, (int, float)):
            if size_bytes < 1024:
                return f"{size_bytes} B"
            elif size_bytes < 1024**2:
                return f"{size_bytes/1024:.1f} KB"
            elif size_bytes < 1024**3:
                return f"{size_bytes/1024**2:.1f} MB"
            else:
                return f"{size_bytes/1024**3:.1f} GB"
        return ""

    def on_source_tree_selection_changed(self):
        """Handles selection changes in the source tree to filter the preview tree."""
        if not hasattr(self.app, 'source_tree'):
            return
        
        selected_items = self.app.source_tree.selectedItems()
        if selected_items:
            selected_item_widget = selected_items[0]
            item_data = selected_item_widget.data(0, Qt.UserRole)
            if item_data and item_data.get('type') == 'folder':
                folder_path = item_data.get('path')
                # self.app.logger.debug(  # (Silenced for normal use. Re-enable for troubleshooting.)f"Source tree folder selected: {folder_path}")
                self.set_source_folder_filter(folder_path)
            else:  # Item selected is not a folder or has no path data
                self.clear_source_folder_filter()
        else:
            self.clear_source_folder_filter()

    def set_source_folder_filter(self, folder_path: Optional[str]):
        """Sets a filter for the preview tree based on the selected source folder."""
        # self.app.logger.debug(  # (Silenced for normal use. Re-enable for troubleshooting.)f"Setting preview filter to source folder: {folder_path}")
        self.selected_source_folder_path = folder_path
        self.rebuild_preview_tree_from_current_data(preserve_selection=True)  # Rebuild will apply filter

    def clear_source_folder_filter(self):
        """Clears the source folder filter for the preview tree."""
        if self.selected_source_folder_path is not None:
            # self.app.logger.debug(  # (Silenced for normal use. Re-enable for troubleshooting.)"Clearing source folder filter for preview.")
            self.selected_source_folder_path = None
            self.rebuild_preview_tree_from_current_data(preserve_selection=True)  # Rebuild will apply filter

    def populate_preview_tree(self, item_data_list: List[Dict[str, Any]], base_path: Optional[str] = None):
        """
        Populates the preview tree with the given item data.
        This method now becomes the primary way to build/rebuild the preview tree.
        Assumes that sequences are represented as single items in item_data_list.
        """
        # # self.app.logger.debug(  # (Silenced for normal use. Re-enable for troubleshooting.)"Populating preview tree...")  # (Silenced for normal use. Re-enable for troubleshooting.)
        if not hasattr(self.app, 'preview_tree'):
            self.app.logger.error("Preview tree widget not found in app instance.")
            return
            
        self.app.preview_tree.clear()
        self._clear_preview_tree_internal_state()  # Clear previous state
        self.master_item_data_list = list(item_data_list)  # Store a copy of the new master list

        if not self.app.normalizer:
            self.app.logger.error("TreeManager: Normalizer not available, cannot populate preview tree.")
            return

        if not self.master_item_data_list:
            self.app.logger.info("TreeManager: No items to populate in the preview tree.")
            return

        self._populate_preview_tree_internal(self.master_item_data_list)

    def rebuild_preview_tree_from_current_data(self, preserve_selection: bool = False):
        """
        Clears and rebuilds the preview tree using the current self.master_item_data_list.
        Filters by selected_source_folder_path if set.
        """
        self.app.logger.info("TreeManager: Rebuilding preview tree from current data.")
        
        selected_ids = set()
        if preserve_selection and hasattr(self.app, 'preview_tree'):
            for item_widget in self.app.preview_tree.selectedItems():
                data = item_widget.data(0, Qt.UserRole)
                if data and data.get('id'):
                    selected_ids.add(data.get('id'))

        # Apply source folder filter if active
        data_to_populate = self.master_item_data_list
        if self.selected_source_folder_path:
            # self.app.logger.debug(  # (Silenced for normal use. Re-enable for troubleshooting.)f"Applying source folder filter: {self.selected_source_folder_path}")
            filtered_data = []
            for item_data in self.master_item_data_list:
                item_source_path = item_data.get('source_path', '')  # Ensure items have 'source_path'
                if item_source_path and item_source_path.startswith(self.selected_source_folder_path):
                    filtered_data.append(item_data)
            data_to_populate = filtered_data
            # self.app.logger.debug(  # (Silenced for normal use. Re-enable for troubleshooting.)f"After source folder filter, {len(data_to_populate)} items remain.")

        self._populate_preview_tree_internal(data_to_populate)

        if preserve_selection and selected_ids and hasattr(self.app, 'preview_tree'):
            items_to_reselect = []
            for item_id in selected_ids:
                widget = self._item_id_to_widget_map.get(item_id)
                if widget:
                    items_to_reselect.append(widget)
            
            if items_to_reselect:
                for item_widget in items_to_reselect:
                    if not item_widget.isHidden():
                        item_widget.setSelected(True)

        self.app.status_manager.set_status("Preview tree rebuilt.")

    def _populate_preview_tree_internal(self, data_to_display: List[Dict[str, Any]]):
        """Internal method to populate the preview tree with given data, used by populate_preview_tree and rebuild_preview_tree_from_current_data."""
        self.app.preview_tree.clear()
        self._item_id_to_widget_map.clear()
        if hasattr(self.app, 'preview_tree_item_data_map'):
            self.app.preview_tree_item_data_map.clear()

        if not self.app.normalizer:
            self.app.logger.error("TreeManager: Normalizer not available, cannot populate preview tree.")
            return

        if not data_to_display:
            self.app.logger.info("TreeManager: No items to populate in the preview tree (after potential filtering).")
            return

        for item_data in data_to_display:
            item_id = item_data.get('id')
            try:
                display_details = self.app.normalizer.get_item_display_details(item_data)
                columns_dict = display_details.get('columns', {})
            except Exception as e:
                self.app.logger.error(f"Error getting display details for item {item_id}: {e}")
                columns_dict = {}
            tree_item_widget = QTreeWidgetItem()

            # --- COLUMN MAPPING ---
            # 0: Filename
            # 1: Size
            # 2: Type
            # 3: Task
            # 4: Asset
            # 5: Version
            # 6: Resolution
            # 7: Destination Path
            # 8: Matched Tags
            tree_item_widget.setText(COL_FILENAME, columns_dict.get('Filename', 'N/A'))
            tree_item_widget.setText(COL_SIZE, columns_dict.get('Size', ''))
            tree_item_widget.setText(COL_TYPE, columns_dict.get('Type', ''))
            tree_item_widget.setText(COL_TASK, columns_dict.get('Task', ''))
            tree_item_widget.setText(COL_ASSET, columns_dict.get('Asset', ''))
            tree_item_widget.setText(COL_VERSION, columns_dict.get('Version', ''))
            tree_item_widget.setText(COL_RESOLUTION, columns_dict.get('Resolution', ''))
            tree_item_widget.setText(COL_DEST_PATH, columns_dict.get('Destination Path', ''))
            # Matched Tags (column 8): try to extract tags from item_data
            matched_tags = item_data.get('matched_tags', {})
            if matched_tags:
                tags_str = ', '.join(f"{k}={v}" for k, v in matched_tags.items() if v)
                tree_item_widget.setText(COL_MATCHED_TAGS, tags_str)
            else:
                tree_item_widget.setText(COL_MATCHED_TAGS, '')

            # Set icon in column 0 (filename)
            icon_name = display_details.get('icon_name', 'file_generic')
            if hasattr(self.app, 'widget_factory') and hasattr(self.app.widget_factory, 'get_icon'):
                try:
                    icon = self.app.widget_factory.get_icon(icon_name)
                    if icon and not icon.isNull():
                        tree_item_widget.setIcon(COL_FILENAME, icon)
                    else:
                        self.app.logger.warning(f"WidgetFactory returned no or null icon for '{icon_name}'. Item ID: {item_id}")
                except Exception as e:
                    log_message = f"Error getting icon '{icon_name}' for item {item_id}: {e}"
                    self.app.logger.error(log_message, exc_info=True)
            # Tooltip on filename column
            tree_item_widget.setToolTip(COL_FILENAME, display_details.get('tooltip', ''))
            # Guarantee 'path' and 'filename' are present in item_data for playback/debug
            if 'path' not in item_data:
                item_data['path'] = display_details.get('path') or columns_dict.get('Filename', 'N/A')
            if 'filename' not in item_data:
                item_data['filename'] = columns_dict.get('Filename', 'N/A')
            tree_item_widget.setData(0, Qt.UserRole, item_data.copy())

            self.app.preview_tree.addTopLevelItem(tree_item_widget)
            self._item_id_to_widget_map[item_id] = tree_item_widget
            if hasattr(self.app, 'preview_tree_item_data_map'):
                self.app.preview_tree_item_data_map[item_id] = item_data.copy()

        # --- UI Enhancements: Auto-resize columns and compact row spacing ---
        # Auto-resize all columns to fit contents
        header = self.app.preview_tree.header()
        for col in range(self.app.preview_tree.columnCount()):
            header.resizeSection(col, 80)  # Set a reasonable default width first
            self.app.preview_tree.resizeColumnToContents(col)
        # Reduce row spacing for a denser UI
        self.app.preview_tree.setStyleSheet("QTreeWidget::item { padding-top: 1px; padding-bottom: 1px; }")


        # After all items are added, log, sort, and filter
        # # self.app.logger.debug(  # (Silenced for normal use. Re-enable for troubleshooting.)"Preview tree populated with {} top-level items.".format(self.app.preview_tree.topLevelItemCount()))  # (Silenced for normal use. Re-enable for troubleshooting.)
        self.apply_current_sort()
        self.filter_preview_tree(self.current_filter_text)

    def sort_preview_tree(self, column_name: str, ascending: bool):
        print(f"[DEBUG] Entering sort_preview_tree with column_name={column_name}, ascending={ascending}")
        try:
            column_map = {
                "Filename": COL_FILENAME, "Task": COL_TASK, "Asset": COL_ASSET,
                "Destination Path": COL_DEST_PATH, "Type": COL_TYPE, "Version": COL_VERSION,
                "Resolution": COL_RESOLUTION
            }
            print(f"[DEBUG] column_map keys: {list(column_map.keys())}")
            column_idx = column_map.get(column_name, COL_FILENAME)
            print(f"[DEBUG] column_idx resolved to {column_idx}")
            self.current_sort_column_idx = column_idx
            self.sort_order = Qt.AscendingOrder if ascending else Qt.DescendingOrder
            print(f"[DEBUG] sort_order set to {self.sort_order}")
            # print("[DEBUG]  # (Silenced for normal use. Re-enable for troubleshooting.) Calling apply_current_sort from sort_preview_tree")
            self.apply_current_sort()
        except Exception as e:
            print(f"[ERROR] Exception in sort_preview_tree: {e}")
            raise

    def update_item_properties_and_refresh_display(self, item_id: str, updated_item_data: dict) -> bool:
        """
        Update the properties of a preview item and refresh its display in the tree.

        Args:
            item_id (str): The unique identifier of the item to update.
            updated_item_data (dict): The new data for the item (after batch edit).

        Returns:
            bool: True if the item was found and updated, False otherwise.

        This method updates the master data, the preview_tree_item_data_map, and the QTreeWidgetItem display.
        """
        # Find and update in master_item_data_list
        found = False
        for idx, item in enumerate(self.master_item_data_list):
            if item.get('id') == item_id:
                print(f"[DEBUG] Updating master_item_data_list at idx={idx} for item_id={item_id}")
                self.master_item_data_list[idx] = updated_item_data.copy()
                # Clean, organized log for updated item data
                summary_lines = [f"[DEBUG] Updated item data for item_id={item_id}:"]
                summary_lines.append(f"  id: {updated_item_data.get('id')}")
                summary_lines.append(f"  filename: {updated_item_data.get('filename')}")
                summary_lines.append(f"  new_destination_path: {updated_item_data.get('new_destination_path')}")
                summary_lines.append(f"  new_name: {updated_item_data.get('new_name')}")
                summary_lines.append(f"  error_message: {updated_item_data.get('error_message')}")
                summary_lines.append(f"  matched_tags: {updated_item_data.get('matched_tags')}")
                summary_lines.append(f"  matched_rules: {updated_item_data.get('matched_rules')}")
                summary_lines.append(f"  normalized_parts: {updated_item_data.get('normalized_parts')}")
                seq_info = updated_item_data.get('sequence_info')
                if seq_info and isinstance(seq_info, dict) and seq_info.get('files'):
                    first_file = seq_info['files'][0] if seq_info['files'] else None
                    summary_lines.append(f"  sequence_first_file: {first_file}")
                    summary_lines.append(f"  sequence_base_name: {seq_info.get('base_name')}")
                    summary_lines.append(f"  sequence_directory: {seq_info.get('directory')}")
                print('\n'.join(summary_lines))
                found = True
                break
        if not found:
            print(f"[DEBUG] Item ID {item_id} not found in master_item_data_list. Current IDs: {[item.get('id') for item in self.master_item_data_list]}")
            if hasattr(self.app, 'logger'):
                self.app.logger.error(f"update_item_properties_and_refresh_display: Item ID {item_id} not found in master_item_data_list.")
            return False
        # Update preview_tree_item_data_map if present
        if hasattr(self.app, 'preview_tree_item_data_map'):
            self.app.preview_tree_item_data_map[item_id] = updated_item_data.copy()
        # Update the tree widget item in-place
        tree_item_widget = self._item_id_to_widget_map.get(item_id)
        if not tree_item_widget:
            if hasattr(self.app, 'logger'):
                self.app.logger.error(f"update_item_properties_and_refresh_display: QTreeWidgetItem for ID {item_id} not found.")
            return False
        # Get updated display details
        # Clean, organized log for passing updated_item_data
        summary_lines = [f"[DEBUG] Passing updated_item_data to normalizer for item_id={item_id}:"]
        summary_lines.append(f"  id: {updated_item_data.get('id')}")
        summary_lines.append(f"  filename: {updated_item_data.get('filename')}")
        summary_lines.append(f"  new_destination_path: {updated_item_data.get('new_destination_path')}")
        summary_lines.append(f"  new_name: {updated_item_data.get('new_name')}")
        summary_lines.append(f"  error_message: {updated_item_data.get('error_message')}")
        summary_lines.append(f"  matched_tags: {updated_item_data.get('matched_tags')}")
        summary_lines.append(f"  matched_rules: {updated_item_data.get('matched_rules')}")
        summary_lines.append(f"  normalized_parts: {updated_item_data.get('normalized_parts')}")
        seq_info = updated_item_data.get('sequence_info')
        if seq_info and isinstance(seq_info, dict) and seq_info.get('files'):
            first_file = seq_info['files'][0] if seq_info['files'] else None
            summary_lines.append(f"  sequence_first_file: {first_file}")
            summary_lines.append(f"  sequence_base_name: {seq_info.get('base_name')}")
            summary_lines.append(f"  sequence_directory: {seq_info.get('directory')}")
        print('\n'.join(summary_lines))
        try:
            display_details = self.app.normalizer.get_item_display_details(updated_item_data)
            columns_dict = display_details.get('columns', {})
        except Exception as e:
            if hasattr(self.app, 'logger'):
                self.app.logger.error(f"update_item_properties_and_refresh_display: Error getting display details for item {item_id}: {e}")
            columns_dict = {}
        # Update columns in the existing widget
        tree_item_widget.setText(COL_FILENAME, columns_dict.get('Filename', 'N/A'))
        tree_item_widget.setText(COL_SIZE, columns_dict.get('Size', ''))
        tree_item_widget.setText(COL_TYPE, columns_dict.get('Type', ''))
        tree_item_widget.setText(COL_TASK, columns_dict.get('Task', ''))
        tree_item_widget.setText(COL_ASSET, columns_dict.get('Asset', ''))
        tree_item_widget.setText(COL_VERSION, columns_dict.get('Version', ''))
        tree_item_widget.setText(COL_RESOLUTION, columns_dict.get('Resolution', ''))
        tree_item_widget.setText(COL_DEST_PATH, columns_dict.get('Destination Path', ''))
        # Matched Tags
        matched_tags = updated_item_data.get('matched_tags', {})
        if matched_tags:
            tags_str = ', '.join(f"{k}={v}" for k, v in matched_tags.items() if v)
            tree_item_widget.setText(COL_MATCHED_TAGS, tags_str)
        else:
            tree_item_widget.setText(COL_MATCHED_TAGS, '')
        # Update icon and tooltip
        icon_name = display_details.get('icon_name', 'file_generic') if 'display_details' in locals() else 'file_generic'
        if hasattr(self.app, 'widget_factory') and hasattr(self.app.widget_factory, 'get_icon'):
            try:
                icon = self.app.widget_factory.get_icon(icon_name)
                if icon and not icon.isNull():
                    tree_item_widget.setIcon(COL_FILENAME, icon)
            except Exception as e:
                if hasattr(self.app, 'logger'):
                    self.app.logger.error(f"update_item_properties_and_refresh_display: Error getting icon '{icon_name}' for item {item_id}: {e}", exc_info=True)
        tree_item_widget.setToolTip(COL_FILENAME, display_details.get('tooltip', '') if 'display_details' in locals() else '')
        # Update the stored item data in the widget
        tree_item_widget.setData(0, Qt.UserRole, updated_item_data.copy())
        # Clean, organized log for master_item_data_list after update
        summary_lines = [f"[DEBUG] master_item_data_list after update: {len(self.master_item_data_list)} items"]
        for i, item in enumerate(self.master_item_data_list):
            summary_lines.append(f"  [{i}] id: {item.get('id')}, filename: {item.get('filename')}, new_destination_path: {item.get('new_destination_path')}")
        print('\n'.join(summary_lines))
        return True

    def apply_current_sort(self):
        # print("[DEBUG]  # (Silenced for normal use. Re-enable for troubleshooting.) Entering apply_current_sort")
        if hasattr(self.app, 'preview_tree'):
            # Default to sort by filename ascending if not set
            if not hasattr(self, 'current_sort_column_idx'):
                # print("[DEBUG]  # (Silenced for normal use. Re-enable for troubleshooting.) current_sort_column_idx not set, defaulting to COL_FILENAME")
                self.current_sort_column_idx = COL_FILENAME
            if not hasattr(self, 'sort_order'):
                # print("[DEBUG]  # (Silenced for normal use. Re-enable for troubleshooting.) sort_order not set, defaulting to Qt.AscendingOrder")
                self.sort_order = Qt.AscendingOrder
            print(f"[DEBUG] Sorting preview tree with column {self.current_sort_column_idx}, order {self.sort_order}")
            self.app.preview_tree.sortItems(self.current_sort_column_idx, self.sort_order)
            # # self.app.logger.debug(  # (Silenced for normal use. Re-enable for troubleshooting.)f"Sorted preview tree by column index {self.current_sort_column_idx}, order: {'Asc' if self.sort_order == Qt.AscendingOrder else 'Desc'}")  # (Silenced for normal use. Re-enable for troubleshooting.)
        # print("[DEBUG]  # (Silenced for normal use. Re-enable for troubleshooting.) Exiting apply_current_sort")


    def filter_preview_tree(self, filter_text: str):
        """Filters the preview tree items based on their type or other criteria.
           This is the general filter (All, Sequences, Files), not the source folder filter.
        """
        self.current_filter_text = filter_text.lower()
        if not hasattr(self.app, 'preview_tree'):
            return
            
        root = self.app.preview_tree.invisibleRootItem()
        for i in range(root.childCount()):
            item = root.child(i)
            item_data = item.data(0, Qt.UserRole)
            if not item_data:
                item.setHidden(False) 
                continue

            actual_item_type = item_data.get('type', 'file').lower()

            should_hide = False
            if self.current_filter_text == "all":
                should_hide = False
            elif self.current_filter_text == "sequences":
                if actual_item_type != 'sequence':
                    should_hide = True
            elif self.current_filter_text == "files":
                if actual_item_type != 'file':
                    should_hide = True
            
            item.setHidden(should_hide)
        # # self.app.logger.debug(  # (Silenced for normal use. Re-enable for troubleshooting.)f"Applied general filter: '{self.current_filter_text}'. Visible items may also be affected by source folder filter.")  # (Silenced for normal use. Re-enable for troubleshooting.)

    def select_all_sequences_in_preview_tree(self):
        """Selects all top-level items identified as sequences in the preview tree, respecting current filters."""
        self.app.preview_tree.clearSelection()
        root = self.app.preview_tree.invisibleRootItem()
        for i in range(root.childCount()):
            item = root.child(i)
            item_type_display = item.text(COL_TYPE).lower()
            if 'sequence' in item_type_display:
                item.setSelected(True)

    def select_all_files_in_preview_tree(self):
        """Selects all top-level items identified as files in the preview tree, respecting current filters."""
        self.app.preview_tree.clearSelection()
        root = self.app.preview_tree.invisibleRootItem()
        for i in range(root.childCount()):
            item = root.child(i)
            item_type_display = item.text(COL_TYPE).lower()
            if 'file' in item_type_display:
                item.setSelected(True)

    def get_selected_items(self) -> List[Dict[str, Any]]:
        """Gets the data of selected items from the preview tree."""
        selected_data = []
        if not hasattr(self.app, 'preview_tree'):
            return selected_data
            
        for item_widget in self.app.preview_tree.selectedItems():
            data = item_widget.data(0, Qt.UserRole)
            if data and isinstance(data, dict):
                selected_data.append(data)
        return selected_data

    def select_all_items(self, item_type: str = "all"):
        """Select all items of specified type."""
        if item_type.lower() == "all":
            self.app.preview_tree.selectAll()
        elif item_type.lower() == "sequences":
            self.select_all_sequences_in_preview_tree()
        elif item_type.lower() == "files":
            self.select_all_files_in_preview_tree()
        else:
            print(f"Unknown item_type for select_all_items: {item_type}")
