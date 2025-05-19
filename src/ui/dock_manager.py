"""
Dock manager for handling dockable panels.
"""

import os
import json
import logging
from typing import Dict, Any, Optional

from PySide6.QtCore import Qt, QByteArray
from PySide6.QtWidgets import QMainWindow, QDockWidget, QWidget
from PySide6.QtGui import QAction

# Get logger
logger = logging.getLogger("monday_uploader.dock_manager")

class DockManager:
    """
    Manages dockable panels in the main window.
    """
    
    def __init__(self, main_window: QMainWindow):
        """
        Initialize the dock manager.
        
        Args:
            main_window: Parent main window
        """
        self.main_window = main_window
        self.docks: Dict[str, QDockWidget] = {}
        self.dock_areas: Dict[str, Qt.DockWidgetArea] = {}
        self.default_state: Optional[QByteArray] = None
        
        logger.info("Dock manager initialized")
    
    def add_dock(self, dock: QDockWidget, name: str, area: Qt.DockWidgetArea = Qt.LeftDockWidgetArea):
        """
        Add a dock widget to the main window.
        
        Args:
            dock: Dock widget to add
            name: Unique name for the dock
            area: Initial dock area
        """
        # Store dock widget
        self.docks[name] = dock
        self.dock_areas[name] = area
        
        # Add to main window
        self.main_window.addDockWidget(area, dock)
        
        # Enable context menu in title bar for dock options
        dock.setContextMenuPolicy(Qt.CustomContextMenu)
        dock.customContextMenuRequested.connect(lambda pos, d=dock: self._show_dock_context_menu(d, pos))
        
        # If first dock widget, save default state
        if len(self.docks) == 1:
            self.default_state = self.main_window.saveState()
        
        logger.debug(f"Added dock widget: {name}")
    
    def remove_dock(self, name: str):
        """
        Remove a dock widget from the main window.
        
        Args:
            name: Name of the dock to remove
        """
        if name in self.docks:
            # Remove from main window
            self.main_window.removeDockWidget(self.docks[name])
            
            # Remove from storage
            del self.docks[name]
            del self.dock_areas[name]
            
            logger.debug(f"Removed dock widget: {name}")
    
    def get_dock(self, name: str) -> Optional[QDockWidget]:
        """
        Get a dock widget by name.
        
        Args:
            name: Name of the dock
            
        Returns:
            Dock widget if found, None otherwise
        """
        return self.docks.get(name)
    
    def is_dock_visible(self, name: str) -> bool:
        """
        Check if a dock widget is visible.
        
        Args:
            name: Name of the dock
            
        Returns:
            True if visible, False otherwise
        """
        if name in self.docks:
            return self.docks[name].isVisible()
        return False
    
    def set_dock_visible(self, name: str, visible: bool):
        """
        Set the visibility of a dock widget.
        
        Args:
            name: Name of the dock
            visible: Visibility state
        """
        if name in self.docks:
            self.docks[name].setVisible(visible)
            logger.debug(f"Set dock '{name}' visibility to {visible}")
    
    def save_layout(self, file_path: str):
        """
        Save the current dock layout to a file.
        
        Args:
            file_path: Path to save the layout
        """
        try:
            # Save main window state
            state = self.main_window.saveState()
            
            # Create layout data
            layout_data = {
                "state": state.toBase64().data().decode("utf-8"),
                "docks": {}
            }
            
            # Save dock information
            for name, dock in self.docks.items():
                layout_data["docks"][name] = {
                    "visible": dock.isVisible(),
                    "floating": dock.isFloating(),
                    "area": int(self.dock_areas[name])
                }
                
                if dock.isFloating():
                    geometry = dock.geometry()
                    layout_data["docks"][name]["geometry"] = {
                        "x": geometry.x(),
                        "y": geometry.y(),
                        "width": geometry.width(),
                        "height": geometry.height()
                    }
            
            # Save to file
            with open(file_path, "w") as f:
                json.dump(layout_data, f, indent=4)
                
            logger.info(f"Layout saved to: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save layout: {str(e)}")
            return False
    
    def load_layout(self, file_path: str):
        """
        Load a dock layout from a file.
        
        Args:
            file_path: Path to the layout file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Check if file exists
            if not os.path.exists(file_path):
                logger.error(f"Layout file not found: {file_path}")
                return False
                
            # Load from file
            with open(file_path, "r") as f:
                layout_data = json.load(f)
                
            # Restore main window state
            state_base64 = layout_data.get("state", "")
            if state_base64:
                state = QByteArray.fromBase64(state_base64.encode("utf-8"))
                self.main_window.restoreState(state)
            
            # Restore dock information
            dock_info = layout_data.get("docks", {})
            for name, info in dock_info.items():
                if name in self.docks:
                    dock = self.docks[name]
                    
                    # Set visibility
                    visible = info.get("visible", True)
                    dock.setVisible(visible)
                    
                    # Set floating state
                    floating = info.get("floating", False)
                    dock.setFloating(floating)
                    
                    # Set geometry if floating
                    if floating and "geometry" in info:
                        geometry = info["geometry"]
                        dock.setGeometry(
                            geometry.get("x", 0),
                            geometry.get("y", 0),
                            geometry.get("width", 300),
                            geometry.get("height", 300)
                        )
                    
                    # Set dock area
                    area = info.get("area", int(Qt.LeftDockWidgetArea))
                    self.dock_areas[name] = Qt.DockWidgetArea(area)
                    self.main_window.addDockWidget(Qt.DockWidgetArea(area), dock)
            
            logger.info(f"Layout loaded from: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load layout: {str(e)}")
            return False
    
    def reset_layout(self):
        """
        Reset the dock layout to default.
        """
        try:
            if self.default_state:
                # Restore default state
                self.main_window.restoreState(self.default_state)
                
                # Show all docks
                for name, dock in self.docks.items():
                    dock.setVisible(True)
                    dock.setFloating(False)
                    
                logger.info("Layout reset to default")
                return True
            else:
                logger.warning("No default state available")
                return False
                
        except Exception as e:
            logger.error(f"Failed to reset layout: {str(e)}")
            return False
    
    def _show_dock_context_menu(self, dock: QDockWidget, pos):
        """
        Show the dock context menu.
        
        Args:
            dock: Dock widget
            pos: Position for the menu
        """
        from PySide6.QtWidgets import QMenu
        
        menu = QMenu(self.main_window)
        
        # Floating action
        floating_action = QAction("Floating", self.main_window)
        floating_action.setCheckable(True)
        floating_action.setChecked(dock.isFloating())
        floating_action.triggered.connect(lambda checked: dock.setFloating(checked))
        menu.addAction(floating_action)
        
        menu.addSeparator()
        
        # Dock area actions
        left_action = QAction("Dock Left", self.main_window)
        left_action.triggered.connect(lambda: self._move_dock(dock, Qt.LeftDockWidgetArea))
        menu.addAction(left_action)
        
        right_action = QAction("Dock Right", self.main_window)
        right_action.triggered.connect(lambda: self._move_dock(dock, Qt.RightDockWidgetArea))
        menu.addAction(right_action)
        
        top_action = QAction("Dock Top", self.main_window)
        top_action.triggered.connect(lambda: self._move_dock(dock, Qt.TopDockWidgetArea))
        menu.addAction(top_action)
        
        bottom_action = QAction("Dock Bottom", self.main_window)
        bottom_action.triggered.connect(lambda: self._move_dock(dock, Qt.BottomDockWidgetArea))
        menu.addAction(bottom_action)
        
        menu.addSeparator()
        
        # Close action
        close_action = QAction("Close", self.main_window)
        close_action.triggered.connect(dock.close)
        menu.addAction(close_action)
        
        # Show menu
        menu.exec(dock.mapToGlobal(pos))
    
    def _move_dock(self, dock: QDockWidget, area: Qt.DockWidgetArea):
        """
        Move a dock widget to a new area.
        
        Args:
            dock: Dock widget to move
            area: New dock area
        """
        # Find dock name
        dock_name = None
        for name, d in self.docks.items():
            if d == dock:
                dock_name = name
                break
        
        if dock_name:
            # Update dock area
            self.dock_areas[dock_name] = area
            
            # Move dock
            self.main_window.removeDockWidget(dock)
            self.main_window.addDockWidget(area, dock)
            dock.setFloating(False)
            dock.show()
            
            logger.debug(f"Moved dock '{dock_name}' to area {area}")
    
    def tabify_docks(self, dock1_name: str, dock2_name: str):
        """
        Tabify two dock widgets.
        
        Args:
            dock1_name: Name of the first dock
            dock2_name: Name of the second dock
        """
        if dock1_name in self.docks and dock2_name in self.docks:
            self.main_window.tabifyDockWidget(
                self.docks[dock1_name],
                self.docks[dock2_name]
            )
            logger.debug(f"Tabified docks '{dock1_name}' and '{dock2_name}'")
    
    def split_docks(self, dock1_name: str, dock2_name: str, orientation: Qt.Orientation = Qt.Horizontal):
        """
        Split two dock widgets.
        
        Args:
            dock1_name: Name of the first dock
            dock2_name: Name of the second dock
            orientation: Split orientation
        """
        if dock1_name in self.docks and dock2_name in self.docks:
            self.main_window.splitDockWidget(
                self.docks[dock1_name],
                self.docks[dock2_name],
                orientation
            )
            logger.debug(f"Split docks '{dock1_name}' and '{dock2_name}' with orientation {orientation}") 