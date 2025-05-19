"""
Main window implementation with dockable panels.
"""

import os
import sys
import json
import logging
from typing import Dict, List, Any, Optional, Set

from PySide6.QtCore import Qt, QSize, QSettings, QPoint, QTimer
from PySide6.QtGui import QIcon, QAction, QKeySequence, QCloseEvent
from PySide6.QtWidgets import (
    QMainWindow, QDockWidget, QMenu, QToolBar, QMessageBox,
    QStatusBar, QTabWidget, QFileDialog, QWidget, QVBoxLayout, QMenuBar
)

# Import application-specific modules
from ui.dock_manager import DockManager
from ui.panels.board_panel import BoardPanel
from ui.panels.items_panel import ItemsPanel
from ui.panels.calendar_panel import CalendarPanel
from ui.panels.map_panel import MapPanel
from ui.panels.news_panel import NewsPanel
from ui.dialogs.settings_dialog import SettingsDialog
from ui.dialogs.template_dialog import TemplateDialog

from controllers.board_controller import BoardController
from controllers.data_controller import DataController
from controllers.sync_controller import SyncController
from controllers.calendar_controller import CalendarController
from controllers.feedback_controller import FeedbackController

from api.monday_api import MondayAPI
from utils.error_handling import handle_error, MondayError, ErrorCodes
from utils.settings import load_settings

# Get logger
logger = logging.getLogger("monday_uploader.main_window")

class MainWindow(QMainWindow):
    """
    Main application window with dockable panels.
    """
    
    def __init__(self, engine, default_boards: Dict[str, str]):
        """
        Initialize the main window.
        
        Args:
            engine: SQLAlchemy engine
            default_boards: Default boards mapping
        """
        super().__init__()
        
        # Set window properties
        self.setWindowTitle("Monday Uploader (PySide Edition)")
        self.setMinimumSize(1200, 800)
        
        # Initialize members
        self.engine = engine
        self.default_boards = default_boards
        self.session = None
        self.dock_manager = DockManager(self)
        self.panels = {}
        self.controllers = {}
        
        # Setup session
        from sqlalchemy.orm import sessionmaker
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
        
        # Load settings
        self.settings = load_settings()
        
        # Initialize API
        self.api_key = self.settings.get('api_key', '')
        self.monday_api = MondayAPI(self.api_key)
        
        # Initialize controllers
        self._init_controllers()
        
        # Setup UI
        self._setup_ui()
        
        # Restore window state
        self._restore_window_state()
        
        # Start update timer for auto-sync
        self._update_timer = QTimer(self)
        self._update_timer.timeout.connect(self._on_update_timer)
        
        # Start timer if auto-sync is enabled
        if self.settings.get('auto_sync', False):
            sync_interval = self.settings.get('sync_interval', 300) * 1000  # convert to milliseconds
            self._update_timer.start(sync_interval)
        
        logger.info("Main window initialized")
        
    def _init_controllers(self):
        """Initialize controllers."""
        try:
            # Create controllers
            self.controllers['board'] = BoardController(
                self.monday_api, 
                self.session,
                self.default_boards
            )
            
            self.controllers['data'] = DataController(
                self.controllers['board'], 
                self.session
            )
            
            self.controllers['sync'] = SyncController(
                self.monday_api, 
                self.session
            )
            
            self.controllers['calendar'] = CalendarController(
                self.session
            )
            
            self.controllers['feedback'] = FeedbackController(
                self.session
            )
            
            # Set sync controller to offline mode by default to avoid API calls
            if 'sync' in self.controllers:
                self.controllers['sync'].set_offline_mode(True)
            
            logger.info("Controllers initialized")
        except Exception as e:
            logger.error(f"Failed to initialize controllers: {str(e)}")
            handle_error(
                exception=e,
                parent=self,
                context={"module": "MainWindow", "method": "_init_controllers"},
                title="Controller Initialization Error"
            )
    
    def _setup_ui(self):
        """Setup the user interface."""
        # Create central widget - This will be the items panel
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.setMovable(True)
        self.tab_widget.setDocumentMode(True)
        self.tab_widget.tabCloseRequested.connect(self._on_tab_close_requested)
        
        # Create menu bar
        self._create_menu_bar()
        
        # Create status bar
        self.status_bar = QStatusBar(self)
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
        
        # Create tool bar
        self._create_tool_bar()
        
        # Create dock widgets
        self._create_dock_widgets()
        
        # Create items panel and set as central widget
        try:
            # Create items panel
            items_panel = ItemsPanel(self.controllers['data'], self)
            
            # Set as central widget
            self.setCentralWidget(items_panel)
            
            # Store panel reference
            self.panels["items"] = items_panel
            
        except Exception as e:
            logger.error(f"Failed to create items panel: {str(e)}")
            handle_error(
                exception=e,
                parent=self,
                context={"module": "MainWindow", "method": "_setup_ui"}
            )
    
    def _create_action(self, text: str, tooltip: str, slot=None, shortcut: Optional[str] = None) -> QAction:
        """
        Create a QAction with the given properties.
        
        Args:
            text: Action text
            tooltip: Action tooltip
            slot: Slot to connect to
            shortcut: Optional keyboard shortcut
            
        Returns:
            Created QAction
        """
        action = QAction(text, self)
        action.setToolTip(tooltip)
        if shortcut:
            action.setShortcut(QKeySequence(shortcut))
        if slot:
            action.triggered.connect(slot)
        return action
    
    def _create_menu_bar(self):
        """Create the application menu bar."""
        menu_bar = self.menuBar()
        
        # File menu
        file_menu = menu_bar.addMenu("&File")
        file_menu.addAction(self._create_action("&New", "Create new project", self._on_new))
        file_menu.addAction(self._create_action("&Open...", "Open existing project", self._on_open))
        file_menu.addAction(self._create_action("&Save", "Save current project", self._on_save))
        file_menu.addAction(self._create_action("Save &As...", "Save project as...", self._on_save_as))
        file_menu.addSeparator()
        file_menu.addAction(self._create_action("E&xit", "Exit application", self.close))
        
        # Edit menu
        edit_menu = menu_bar.addMenu("&Edit")
        edit_menu.addAction(self._create_action("&Undo", "Undo last action", self._on_undo))
        edit_menu.addAction(self._create_action("&Redo", "Redo last action", self._on_redo))
        edit_menu.addSeparator()
        edit_menu.addAction(self._create_action("Cu&t", "Cut selection", self._on_cut))
        edit_menu.addAction(self._create_action("&Copy", "Copy selection", self._on_copy))
        edit_menu.addAction(self._create_action("&Paste", "Paste selection", self._on_paste))
        
        # View menu
        view_menu = menu_bar.addMenu("&View")
        view_menu.addAction(self._create_action("&Dock Manager", "Show/hide dock manager", self._toggle_dock_manager))
        view_menu.addAction(self._create_action("&Items Panel", "Show/hide items panel", self._toggle_items_panel))
        
        # Sync menu
        sync_menu = menu_bar.addMenu("&Sync")
        sync_menu.addAction(self._create_action("&Sync Now", "Sync with Monday.com", self._on_sync))
        sync_menu.addAction(self._create_action("Sync &Settings...", "Configure sync settings", self._on_sync_settings))
        
        # Help menu
        help_menu = menu_bar.addMenu("&Help")
        help_menu.addAction(self._create_action("&Documentation", "View documentation", self._on_documentation))
        help_menu.addAction(self._create_action("&About", "About application", self._on_about))
        help_menu.addSeparator()
        help_menu.addAction(self._create_action("Send &Feedback", "Send feedback to developers", self._on_feedback))
        help_menu.addAction(self._create_action("View &Feedback", "View and manage feedback", self._on_view_feedback))
    
    def _create_tool_bar(self):
        """Create the tool bar."""
        tool_bar = QToolBar("Main Toolbar", self)
        tool_bar.setMovable(True)
        tool_bar.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        self.addToolBar(tool_bar)
        
        # Refresh action
        refresh_action = QAction("Refresh", self)
        refresh_action.triggered.connect(self._on_refresh)
        tool_bar.addAction(refresh_action)
        
        tool_bar.addSeparator()
        
        # New item action
        new_item_action = QAction("New Item", self)
        new_item_action.triggered.connect(self._on_new_item)
        tool_bar.addAction(new_item_action)
        
        # Delete item action
        delete_item_action = QAction("Delete Item", self)
        delete_item_action.triggered.connect(self._on_delete_item)
        tool_bar.addAction(delete_item_action)
        
        tool_bar.addSeparator()
        
        # Sync action
        sync_action = QAction("Sync Now", self)
        sync_action.triggered.connect(self._on_sync_now)
        tool_bar.addAction(sync_action)
    
    def _create_dock_widgets(self):
        """Create the dock widgets."""
        # Create dock widgets
        self._create_boards_dock()
        # Items dock is now the central widget
        self._create_calendar_dock()
        self._create_map_dock()
        self._create_news_dock()
    
    def _create_boards_dock(self):
        """Create the boards dock widget."""
        try:
            # Create board panel
            board_panel = BoardPanel(self.controllers['board'], self)
            
            # Create dock widget
            dock = QDockWidget("Boards", self)
            dock.setWidget(board_panel)
            dock.setObjectName("BoardsDock")
            dock.setAllowedAreas(Qt.AllDockWidgetAreas)
            
            # Add to dock manager
            self.dock_manager.add_dock(dock, "boards", Qt.LeftDockWidgetArea)
            
            # Store panel reference
            self.panels["boards"] = board_panel
            
            # Connect signals
            board_panel.board_selected.connect(self._on_board_selected)
            
        except Exception as e:
            logger.error(f"Failed to create boards dock: {str(e)}")
            handle_error(
                exception=e,
                parent=self,
                context={"module": "MainWindow", "method": "_create_boards_dock"}
            )
    
    def _create_items_dock(self):
        """Create the items dock widget."""
        # This method is no longer used since items panel is now central widget
        pass
    
    def _create_calendar_dock(self):
        """Create the calendar dock widget."""
        try:
            # Create calendar panel
            calendar_panel = CalendarPanel(self.controllers['calendar'], self)
            
            # Create dock widget
            dock = QDockWidget("Calendar", self)
            dock.setWidget(calendar_panel)
            dock.setObjectName("CalendarDock")
            dock.setAllowedAreas(Qt.AllDockWidgetAreas)
            
            # Add to dock manager
            self.dock_manager.add_dock(dock, "calendar", Qt.BottomDockWidgetArea)
            
            # Store panel reference
            self.panels["calendar"] = calendar_panel
            
        except Exception as e:
            logger.error(f"Failed to create calendar dock: {str(e)}")
            handle_error(
                exception=e,
                parent=self,
                context={"module": "MainWindow", "method": "_create_calendar_dock"}
            )
    
    def _create_map_dock(self):
        """Create the map dock widget."""
        try:
            # Create map panel
            map_panel = MapPanel(self)
            
            # Create dock widget
            dock = QDockWidget("Map", self)
            dock.setWidget(map_panel)
            dock.setObjectName("MapDock")
            dock.setAllowedAreas(Qt.AllDockWidgetAreas)
            
            # Add to dock manager
            self.dock_manager.add_dock(dock, "map", Qt.BottomDockWidgetArea)
            
            # Store panel reference
            self.panels["map"] = map_panel
            
        except Exception as e:
            logger.error(f"Failed to create map dock: {str(e)}")
            handle_error(
                exception=e,
                parent=self,
                context={"module": "MainWindow", "method": "_create_map_dock"}
            )
    
    def _create_news_dock(self):
        """Create the news dock widget."""
        try:
            # Create news panel with data controller
            news_panel = NewsPanel(self, self.controllers.get('data'))
            
            # Create dock widget
            dock = QDockWidget("Weather & News", self)
            dock.setWidget(news_panel)
            dock.setObjectName("NewsDock")
            dock.setAllowedAreas(Qt.AllDockWidgetAreas)
            
            # Add to dock manager
            self.dock_manager.add_dock(dock, "news", Qt.BottomDockWidgetArea)
            
            # Store panel reference
            self.panels["news"] = news_panel
            
        except Exception as e:
            logger.error(f"Failed to create news dock: {str(e)}")
            handle_error(
                exception=e,
                parent=self,
                context={"module": "MainWindow", "method": "_create_news_dock"}
            )
            
    def _restore_window_state(self):
        """Restore window state from settings."""
        try:
            # Create QSettings object
            qsettings = QSettings("MondayUploader", "PySideEdition")
            
            # Restore geometry and state if available
            if qsettings.contains("MainWindow/geometry"):
                self.restoreGeometry(qsettings.value("MainWindow/geometry"))
            
            if qsettings.contains("MainWindow/state"):
                self.restoreState(qsettings.value("MainWindow/state"))
                
            logger.info("Window state restored")
        except Exception as e:
            logger.warning(f"Failed to restore window state: {str(e)}")
    
    def _save_window_state(self):
        """Save window state to settings."""
        try:
            # Create QSettings object
            qsettings = QSettings("MondayUploader", "PySideEdition")
            
            # Save geometry and state
            qsettings.setValue("MainWindow/geometry", self.saveGeometry())
            qsettings.setValue("MainWindow/state", self.saveState())
            
            logger.info("Window state saved")
        except Exception as e:
            logger.warning(f"Failed to save window state: {str(e)}")
    
    def closeEvent(self, event: QCloseEvent):
        """Handle window close event."""
        try:
            # Save window state
            self._save_window_state()
            
            # Close database session
            if self.session:
                self.session.close()
                
            # Stop update timer
            if self._update_timer.isActive():
                self._update_timer.stop()
                
            logger.info("Application closing")
        except Exception as e:
            logger.error(f"Error during shutdown: {str(e)}")
        
        event.accept()
    
    # Event handlers
    def _on_settings(self):
        """Open settings dialog."""
        settings_dialog = SettingsDialog(self.settings, self)
        if settings_dialog.exec():
            # Update settings
            self.settings = settings_dialog.get_settings()
            
            # Update API key if changed
            api_key = self.settings.get('api_key', '')
            if api_key != self.api_key:
                self.api_key = api_key
                self.monday_api = MondayAPI(self.api_key)
                
                # Update controllers
                for controller_name, controller in self.controllers.items():
                    if hasattr(controller, 'set_api'):
                        controller.set_api(self.monday_api)
            
            # Update auto-sync timer
            if self.settings.get('auto_sync', False):
                sync_interval = self.settings.get('sync_interval', 300) * 1000  # convert to milliseconds
                self._update_timer.start(sync_interval)
            else:
                self._update_timer.stop()
    
    def _on_import(self):
        """Import data from file."""
        file_path, file_filter = QFileDialog.getOpenFileName(
            self,
            "Import Data",
            "",
            "Excel Files (*.xlsx);;CSV Files (*.csv);;All Files (*)"
        )
        
        if file_path:
            self.status_bar.showMessage(f"Importing {file_path}...")
            # TODO: Implement import functionality
    
    def _on_export(self):
        """Export data to file."""
        file_path, file_filter = QFileDialog.getSaveFileName(
            self,
            "Export Data",
            "",
            "Excel Files (*.xlsx);;CSV Files (*.csv);;All Files (*)"
        )
        
        if file_path:
            self.status_bar.showMessage(f"Exporting to {file_path}...")
            # TODO: Implement export functionality
    
    def _on_template_creator(self):
        """Open template creator dialog."""
        template_dialog = TemplateDialog(self.session, self)
        template_dialog.show()
    
    def _on_new_item(self):
        """Create new item."""
        if "items" in self.panels:
            self.panels["items"].create_new_item()
    
    def _on_delete_item(self):
        """Delete selected item."""
        if "items" in self.panels:
            self.panels["items"].delete_selected_item()
    
    def _on_refresh(self):
        """Refresh all panels."""
        for panel_name, panel in self.panels.items():
            if hasattr(panel, 'refresh'):
                panel.refresh()
        
        self.status_bar.showMessage("Refreshed", 3000)
    
    def _on_select_board(self, board_id):
        """Select a board from the menu."""
        try:
            # Update status bar
            self.status_bar.showMessage(f"Loading board {board_id}...")
            
            # Select the board in the boards panel
            if "boards" in self.panels:
                self.panels["boards"].select_board(board_id)
            
            # Update status bar
            board_name = "Unknown"
            if 'board' in self.controllers:
                board_name = self.controllers['board'].get_board_name(board_id) or "Unknown"
            
            self.status_bar.showMessage(f"Selected {board_name} board", 3000)
        except Exception as e:
            logger.error(f"Error selecting board: {str(e)}")
            self.status_bar.showMessage(f"Error selecting board: {str(e)}", 5000)
            handle_error(
                exception=e,
                parent=self,
                context={"module": "MainWindow", "method": "_on_select_board"},
                title="Board Selection Error"
            )
    
    def _toggle_panel(self, panel_name, visible):
        """Toggle panel visibility."""
        self.dock_manager.set_dock_visible(panel_name, visible)
    
    def _reset_layout(self):
        """Reset dock layout to default."""
        self.dock_manager.reset_layout()
    
    def _save_layout(self):
        """Save current dock layout."""
        file_path, file_filter = QFileDialog.getSaveFileName(
            self,
            "Save Layout",
            "",
            "Layout Files (*.layout);;All Files (*)"
        )
        
        if file_path:
            self.dock_manager.save_layout(file_path)
            self.status_bar.showMessage(f"Layout saved to {file_path}", 3000)
    
    def _load_layout(self):
        """Load dock layout from file."""
        file_path, file_filter = QFileDialog.getOpenFileName(
            self,
            "Load Layout",
            "",
            "Layout Files (*.layout);;All Files (*)"
        )
        
        if file_path:
            self.dock_manager.load_layout(file_path)
            self.status_bar.showMessage(f"Layout loaded from {file_path}", 3000)
    
    def _on_sync_now(self):
        """Synchronize with Monday.com."""
        self.status_bar.showMessage("Syncing with Monday.com...")
        
        # Call sync controller
        if 'sync' in self.controllers:
            try:
                success = self.controllers['sync'].force_sync()
                if success:
                    self.status_bar.showMessage("Sync completed successfully", 3000)
                else:
                    self.status_bar.showMessage("Sync partially completed - rate limit reached", 3000)
                
                # Refresh panels
                self._on_refresh()
            except Exception as e:
                logger.error(f"Sync failed: {str(e)}")
                self.status_bar.showMessage("Sync failed", 3000)
                handle_error(
                    exception=e,
                    parent=self,
                    context={"module": "MainWindow", "method": "_on_sync_now"}
                )
    
    def _on_toggle_auto_sync(self, checked):
        """Toggle auto sync."""
        self.settings['auto_sync'] = checked
        
        if checked:
            sync_interval = self.settings.get('sync_interval', 300) * 1000  # convert to milliseconds
            self._update_timer.start(sync_interval)
            self.status_bar.showMessage(f"Auto-sync enabled (every {sync_interval/1000} seconds)", 3000)
        else:
            self._update_timer.stop()
            self.status_bar.showMessage("Auto-sync disabled", 3000)
    
    def _on_about(self):
        """Show about dialog."""
        QMessageBox.about(
            self,
            "About Monday Uploader",
            "Monday Uploader (PySide Edition)\nVersion 1.0.0\n\nA modern, feature-rich Monday.com integration application."
        )
    
    def _on_help(self):
        """Show help dialog."""
        # TODO: Implement help functionality
        QMessageBox.information(
            self,
            "Help",
            "Help documentation is not yet implemented."
        )
    
    def _on_tab_close_requested(self, index):
        """Handle tab close request."""
        self.tab_widget.removeTab(index)
    
    def _on_update_timer(self):
        """Handle update timer event."""
        # Perform sync if auto-sync is enabled
        if self.settings.get('auto_sync', False):
            logger.info("Auto-sync timer triggered")
            self._on_sync_now()
    
    def _on_board_selected(self, board_id):
        """Handle board selection."""
        try:
            # Update status bar
            self.status_bar.showMessage(f"Loading board {board_id}...")
            
            # Get board name for better status message
            board_name = "Unknown"
            if 'board' in self.controllers:
                board_name = self.controllers['board'].get_board_name(board_id) or "Unknown"
                self.status_bar.showMessage(f"Loading {board_name} board...")
            
            # Load items in the items panel
            if "items" in self.panels:
                self.panels["items"].load_board_items(board_id)
                
            # Update status bar
            self.status_bar.showMessage(f"Loaded {board_name} board", 3000)
        except Exception as e:
            logger.error(f"Error selecting board: {str(e)}")
            self.status_bar.showMessage(f"Error loading board: {str(e)}", 5000)
            handle_error(
                exception=e,
                parent=self,
                context={"module": "MainWindow", "method": "_on_board_selected"},
                title="Board Selection Error"
            )

    def _on_feedback(self):
        """Handle feedback menu action."""
        from ui.dialogs.feedback_dialog import FeedbackDialog
        dialog = FeedbackDialog(self)
        dialog.exec_()

    def _on_new(self):
        """Create new project."""
        # TODO: Implement new project creation
        self.status_bar.showMessage("New project creation not yet implemented", 3000)
    
    def _on_open(self):
        """Open existing project."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Project",
            "",
            "Project Files (*.json);;All Files (*)"
        )
        if file_path:
            # TODO: Implement project loading
            self.status_bar.showMessage(f"Opening project: {file_path}", 3000)
    
    def _on_save(self):
        """Save current project."""
        # TODO: Implement project saving
        self.status_bar.showMessage("Saving project...", 3000)
    
    def _on_save_as(self):
        """Save project as..."""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Project As",
            "",
            "Project Files (*.json);;All Files (*)"
        )
        if file_path:
            # TODO: Implement project saving
            self.status_bar.showMessage(f"Saving project as: {file_path}", 3000)
    
    def _on_undo(self):
        """Undo last action."""
        # TODO: Implement undo functionality
        self.status_bar.showMessage("Undo not yet implemented", 3000)
    
    def _on_redo(self):
        """Redo last action."""
        # TODO: Implement redo functionality
        self.status_bar.showMessage("Redo not yet implemented", 3000)
    
    def _on_cut(self):
        """Cut selection."""
        # TODO: Implement cut functionality
        self.status_bar.showMessage("Cut not yet implemented", 3000)
    
    def _on_copy(self):
        """Copy selection."""
        # TODO: Implement copy functionality
        self.status_bar.showMessage("Copy not yet implemented", 3000)
    
    def _on_paste(self):
        """Paste selection."""
        # TODO: Implement paste functionality
        self.status_bar.showMessage("Paste not yet implemented", 3000)
    
    def _toggle_dock_manager(self):
        """Toggle dock manager visibility."""
        if "boards" in self.panels:
            self.panels["boards"].setVisible(not self.panels["boards"].isVisible())
    
    def _toggle_items_panel(self):
        """Toggle items panel visibility."""
        if "items" in self.panels:
            self.panels["items"].setVisible(not self.panels["items"].isVisible())
    
    def _on_sync(self):
        """Sync with Monday.com."""
        self._on_sync_now()
    
    def _on_sync_settings(self):
        """Configure sync settings."""
        # TODO: Implement sync settings dialog
        self.status_bar.showMessage("Sync settings not yet implemented", 3000)
    
    def _on_documentation(self):
        """View documentation."""
        # TODO: Implement documentation viewer
        QMessageBox.information(
            self,
            "Documentation",
            "Documentation is not yet implemented."
        )
    
    def _on_view_feedback(self):
        """Open feedback manager dialog."""
        from ui.dialogs.feedback_manager_dialog import FeedbackManagerDialog
        dialog = FeedbackManagerDialog(self.controllers['feedback'], self)
        dialog.feedback_updated.connect(self._on_feedback_updated)
        dialog.exec_()
    
    def _on_feedback_updated(self):
        """Handle feedback update."""
        # Refresh any relevant UI elements
        self.status_bar.showMessage("Feedback updated", 3000) 