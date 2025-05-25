"""
Main window implementation with dockable panels.
"""

import os
import sys
import json
import logging
from typing import Dict, List, Any, Optional, Set

from PySide6.QtCore import Qt, QSize, QSettings, QPoint, QTimer
from PySide6.QtGui import QIcon, QAction, QKeySequence, QCloseEvent, QCursor
from PySide6.QtWidgets import (
    QMainWindow, QDockWidget, QMenu, QToolBar, QMessageBox,
    QStatusBar, QTabWidget, QFileDialog, QWidget, QVBoxLayout, QMenuBar, QDialog,
    QPushButton, QLabel, QHBoxLayout, QStyle, QInputDialog
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
from ui.panels.analytics_panel import AnalyticsPanel

from controllers.board_controller import BoardController
from controllers.data_controller import DataController
from controllers.sync_controller import SyncController
from controllers.calendar_controller import CalendarController
from controllers.feedback_controller import FeedbackController
from controllers.settlement_controller import SettlementController
from ui.dialogs.settlement_calculator_dialog import SettlementCalculatorDialog
from controllers.analytics_controller import AnalyticsController

from api.monday_api import MondayAPI
from utils.error_handling import handle_error, MondayError, ErrorCodes
from utils.settings import load_settings

# Import feature flags with fallback options
try:
    from src.utils.feature_flags import feature_flags, is_feature_enabled
except ImportError:
    try:
        from utils.feature_flags import feature_flags, is_feature_enabled
    except ImportError:
        # Create placeholder feature flags function if module can't be imported
        def is_feature_enabled(feature_name):
            return False
        class FeatureFlagsPlaceholder:
            def __init__(self):
                self.flags = {}
            def get_enabled_features(self):
                return []
        feature_flags = FeatureFlagsPlaceholder()

# Import feature dialogs with fallback handling
try:
    from src.ui.dialogs.feature_manager_dialog import FeatureManagerDialog
except ImportError:
    try:
        from ui.dialogs.feature_manager_dialog import FeatureManagerDialog
    except ImportError:
        # Will be handled at runtime if needed
        pass

# Import database migration with fallback options
try:
    from src.utils.database_migration import DatabaseMigration
except ImportError:
    try:
        from utils.database_migration import DatabaseMigration
    except ImportError:
        # Create placeholder DatabaseMigration class if module can't be imported
        class DatabaseMigration:
            def __init__(self, *args, **kwargs):
                pass
            def apply_pending_migrations(self):
                return (0, 0)
            def get_applied_migrations(self):
                return []

# Import new dialogs
from ui.dialogs.board_manager_dialog import BoardManagerDialog
from ui.dialogs.column_manager_dialog import ColumnManagerDialog
from ui.dialogs.item_manager_dialog import ItemManagerDialog

# Import database models and utilities
from src.models.database import Session, Base
from src.utils.logger import setup_logger

# Get logger
logger = logging.getLogger("monday_uploader.main_window")

class MainWindow(QMainWindow):
    """
    Main application window with dockable panels.
    """
    
    def __init__(self, engine, default_boards=None):
        """
        Initialize the main window.
        
        Args:
            engine: SQLAlchemy engine
            default_boards: Default boards mapping
        """
        super().__init__()
        
        # Initialize logger
        self.logger = setup_logger()
        
        # Store engine and create session
        self.engine = engine
        self.session = Session(bind=engine)
        
        # Store default boards
        self.default_boards = default_boards or {}
        
        # Load settings
        self.settings = load_settings()
        
        # Initialize API
        self.api_key = self.settings.get('api_key', '')
        self.monday_api = MondayAPI(self.api_key)
        
        # Initialize controllers
        self.controllers = {}
        self._init_controllers()
        
        # Initialize panels dictionary
        self.panels = {}
        
        # Initialize dock manager
        self.dock_manager = DockManager(self)
        
        # Apply any pending migrations
        try:
            # Import here to avoid circular imports
            from src.utils.database_migration import apply_pending_migrations, create_sample_data
            apply_pending_migrations(self.engine)
            # Create sample data if needed
            create_sample_data(self.session)
        except Exception as e:
            self.logger.error(f"Error applying migrations: {str(e)}")
            QMessageBox.critical(
                self,
                "Database Error",
                f"Error applying database migrations: {str(e)}"
            )
        
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
        
        # Initialize weather feeds
        try:
            if 'data' in self.controllers:
                weather_board_id = self.controllers['board'].get_board_id("Weather Reports")
                if weather_board_id:
                    # Fetch and store weather feeds
                    weather_feeds = self.controllers['data'].fetch_and_store_weather_feeds()
                    if not weather_feeds:
                        logger.warning("No weather feeds were fetched")
        except Exception as e:
            logger.error(f"Error fetching weather feeds: {str(e)}")
        
        logger.info("Main window initialized")
        
    def _init_controllers(self):
        """Initialize controllers."""
        try:
            # Initialize board controller
            self.controllers['board'] = BoardController(
                session=Session(bind=self.engine),
                default_boards=self.default_boards
            )
            
            # Initialize data controller
            self.controllers['data'] = DataController(
                engine=self.engine,
                board_controller=self.controllers['board']
            )
            
            # Initialize other controllers
            self.controllers['calendar'] = CalendarController(self.engine)
            self.controllers['feedback'] = FeedbackController(session=Session(bind=self.engine))
            self.controllers['sync'] = SyncController(self.engine, Session(bind=self.engine))
            self.controllers['analytics'] = AnalyticsController(self.engine)
            
            logger.info("Controllers initialized")
        except Exception as e:
            logger.error(f"Error initializing controllers: {str(e)}")
            handle_error(e)
            
    def _setup_ui(self):
        """Setup the user interface."""
        # Create central widget - This will be the tab widget
        self.tab_widget = QTabWidget()
        
        # Create panels
        self.panels['items'] = ItemsPanel(self.controllers['board'], self.controllers['data'])
        self.panels['analytics'] = AnalyticsPanel()
        self.panels['analytics'].set_analytics_controller(self.controllers['analytics'])
        
        # Add panels to tab widget
        self.tab_widget.addTab(self.panels['items'], "Items")
        self.tab_widget.addTab(self.panels['analytics'], "Analytics")
        
        # Set tab widget as central widget
        self.setCentralWidget(self.tab_widget)
        
        # Create menu bar
        self._create_menu_bar()
        
        # Create tool bar
        self._create_tool_bar()
        
        # Create dock widgets
        self._create_dock_widgets()
        
        # Create status bar
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("Ready")
        
        # Setup settlement calculator
        self._setup_settlement_calculator()
        
        # Update UI based on enabled features
        self._update_ui_for_features()
    
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
        """Create the menu bar."""
        menu_bar = self.menuBar()
        
        # File menu
        self.file_menu = menu_bar.addMenu("&File")
        
        # New action
        new_action = self._create_action(
            "&New",
            "Create a new board",
            self._on_new,
            "Ctrl+N"
        )
        self.file_menu.addAction(new_action)
        
        # Open action
        open_action = self._create_action(
            "&Open",
            "Open an existing board",
            self._on_open,
            "Ctrl+O"
        )
        self.file_menu.addAction(open_action)
        
        self.file_menu.addSeparator()
        
        # Save action
        save_action = self._create_action(
            "&Save",
            "Save the current board",
            self._on_save,
            "Ctrl+S"
        )
        self.file_menu.addAction(save_action)
        
        # Save As action
        save_as_action = self._create_action(
            "Save &As...",
            "Save the current board with a new name",
            self._on_save_as,
            "Ctrl+Shift+S"
        )
        self.file_menu.addAction(save_as_action)
        
        self.file_menu.addSeparator()
        
        # Import action
        import_action = self._create_action(
            "&Import...",
            "Import data from a file",
            self._on_import
        )
        self.file_menu.addAction(import_action)
        
        # Export action
        export_action = self._create_action(
            "&Export...",
            "Export data to a file",
            self._on_export
        )
        self.file_menu.addAction(export_action)
        
        self.file_menu.addSeparator()
        
        # Exit action
        exit_action = self._create_action(
            "E&xit",
            "Exit the application",
            self.close,
            "Alt+F4"
        )
        self.file_menu.addAction(exit_action)
        
        # Edit menu
        edit_menu = menu_bar.addMenu("&Edit")
        
        # Undo action
        undo_action = self._create_action(
            "&Undo",
            "Undo the last action",
            self._on_undo,
            "Ctrl+Z"
        )
        edit_menu.addAction(undo_action)
        
        # Redo action
        redo_action = self._create_action(
            "&Redo",
            "Redo the last undone action",
            self._on_redo,
            "Ctrl+Y"
        )
        edit_menu.addAction(redo_action)
        
        edit_menu.addSeparator()
        
        # Cut action
        cut_action = self._create_action(
            "Cu&t",
            "Cut the selected item",
            self._on_cut,
            "Ctrl+X"
        )
        edit_menu.addAction(cut_action)
        
        # Copy action
        copy_action = self._create_action(
            "&Copy",
            "Copy the selected item",
            self._on_copy,
            "Ctrl+C"
        )
        edit_menu.addAction(copy_action)
        
        # Paste action
        paste_action = self._create_action(
            "&Paste",
            "Paste the copied item",
            self._on_paste,
            "Ctrl+V"
        )
        edit_menu.addAction(paste_action)
        
        # View menu
        self.view_menu = menu_bar.addMenu("&View")
        
        # Analytics action
        self.analytics_action = self._create_action(
            "&Analytics",
            "Show analytics dashboard",
            lambda: self._toggle_panel("analytics", True)
        )
        self.view_menu.addAction(self.analytics_action)
        
        # Tools menu
        tools_menu = menu_bar.addMenu("&Tools")
        
        # Settings action
        settings_action = self._create_action(
            "&Settings",
            "Configure application settings",
            self._on_settings
        )
        tools_menu.addAction(settings_action)
        
        # Template Creator action
        template_action = self._create_action(
            "&Template Creator",
            "Create or edit templates",
            self._on_template_creator
        )
        tools_menu.addAction(template_action)
        
        # Settlement Calculator action
        settlement_action = self._create_action(
            "&Settlement Calculator",
            "Calculate settlement amounts",
            self._on_settlement_calculator
        )
        tools_menu.addAction(settlement_action)
        
        # Help menu
        help_menu = menu_bar.addMenu("&Help")
        
        # Documentation action
        docs_action = self._create_action(
            "&Documentation",
            "View application documentation",
            self._on_documentation
        )
        help_menu.addAction(docs_action)
        
        # About action
        about_action = self._create_action(
            "&About",
            "About the application",
            self._on_about
        )
        help_menu.addAction(about_action)
    
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
            board_panel = BoardPanel(parent=self, board_controller=self.controllers['board'])
            
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
            self.statusBar.showMessage(f"Importing {file_path}...")
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
            self.statusBar.showMessage(f"Exporting to {file_path}...")
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
        
        self.statusBar.showMessage("Refreshed", 3000)
    
    def _on_select_board(self, board_id):
        """Select a board from the menu."""
        try:
            # Update status bar
            self.statusBar.showMessage(f"Loading board {board_id}...")
            
            # Select the board in the boards panel
            if "boards" in self.panels:
                self.panels["boards"].select_board(board_id)
            
            # Update status bar
            board_name = "Unknown"
            if 'board' in self.controllers:
                board_name = self.controllers['board'].get_board_name(board_id) or "Unknown"
            
            self.statusBar.showMessage(f"Selected {board_name} board", 3000)
        except Exception as e:
            logger.error(f"Error selecting board: {str(e)}")
            self.statusBar.showMessage(f"Error selecting board: {str(e)}", 5000)
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
            self.statusBar.showMessage(f"Layout saved to {file_path}", 3000)
    
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
            self.statusBar.showMessage(f"Layout loaded from {file_path}", 3000)
    
    def _on_sync_now(self):
        """Synchronize with Monday.com."""
        self.statusBar.showMessage("Syncing with Monday.com...")
        
        # Call sync controller
        if 'sync' in self.controllers:
            try:
                success = self.controllers['sync'].force_sync()
                if success:
                    self.statusBar.showMessage("Sync completed successfully", 3000)
                else:
                    self.statusBar.showMessage("Sync partially completed - rate limit reached", 3000)
                
                # Refresh panels
                self._on_refresh()
            except Exception as e:
                logger.error(f"Sync failed: {str(e)}")
                self.statusBar.showMessage("Sync failed", 3000)
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
            self.statusBar.showMessage(f"Auto-sync enabled (every {sync_interval/1000} seconds)", 3000)
        else:
            self._update_timer.stop()
            self.statusBar.showMessage("Auto-sync disabled", 3000)
    
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
    
    def _on_board_selected(self, board_id: str):
        """
        Handle board selection.
        
        Args:
            board_id: Selected board ID
        """
        try:
            # Get board name
            board_name = self.controllers['board'].get_board_name(board_id)
            if not board_name:
                logger.error(f"Unknown board ID: {board_id}")
                return
                
            logger.info(f"Selected board: {board_name} (ID: {board_id})")
            
            # Load board items
            items = self.controllers['data'].load_board_items(board_id)
            
            # Update board view
            if "boards" in self.panels:
                if not items:
                    # Show message if no data
                    self.panels["boards"].show_message(
                        f"No data available for {board_name}.\n\n"
                        "Please use 'Import Board Data...' from the File menu to import data from Excel."
                    )
                else:
                    # Update the items panel instead of the board panel
                    if "items" in self.panels:
                        self.panels["items"].load_board_items(board_id)
            
            # Update status
            if hasattr(self, 'statusBar'):
                self.statusBar.showMessage(f"Loaded {len(items)} items from {board_name}")
                
        except Exception as e:
            logger.error(f"Error selecting board: {str(e)}")
            handle_error(e)
    
    def _on_feedback(self):
        """Handle feedback menu action."""
        from ui.dialogs.feedback_dialog import FeedbackDialog
        dialog = FeedbackDialog(self, feedback_controller=self.controllers.get('feedback'))
        dialog.exec_()

    def _on_new(self):
        """Create new project."""
        # TODO: Implement new project creation
        self.statusBar.showMessage("New project creation not yet implemented", 3000)
    
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
            self.statusBar.showMessage(f"Opening project: {file_path}", 3000)
    
    def _on_save(self):
        """Save current project."""
        # TODO: Implement project saving
        self.statusBar.showMessage("Saving project...", 3000)
    
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
            self.statusBar.showMessage(f"Saving project as: {file_path}", 3000)
    
    def _on_undo(self):
        """Undo last action."""
        # TODO: Implement undo functionality
        self.statusBar.showMessage("Undo not yet implemented", 3000)
    
    def _on_redo(self):
        """Redo last action."""
        # TODO: Implement redo functionality
        self.statusBar.showMessage("Redo not yet implemented", 3000)
    
    def _on_cut(self):
        """Cut selection."""
        # TODO: Implement cut functionality
        self.statusBar.showMessage("Cut not yet implemented", 3000)
    
    def _on_copy(self):
        """Copy selection."""
        # TODO: Implement copy functionality
        self.statusBar.showMessage("Copy not yet implemented", 3000)
    
    def _on_paste(self):
        """Paste selection."""
        # TODO: Implement paste functionality
        self.statusBar.showMessage("Paste not yet implemented", 3000)
    
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
        self.statusBar.showMessage("Sync settings not yet implemented", 3000)
    
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
        self.statusBar.showMessage("Feedback updated", 3000)
    
    def _setup_settlement_calculator(self):
        """Setup the settlement calculator menu and toolbar items."""
        # Check if feature is enabled
        if not is_feature_enabled("settlement_calculator_enabled"):
            logger.info("Settlement calculator feature is disabled")
            return
            
        # Add to toolbar
        if hasattr(self, 'toolbar'):
            # Create toolbar button with icon
            calculator_icon = QIcon.fromTheme("accessories-calculator")
            self.toolbar_settlement = QAction(calculator_icon, "Settlement Calculator", self)
            self.toolbar_settlement.setStatusTip("Calculate potential claim settlements")
            self.toolbar_settlement.triggered.connect(self._on_settlement_calculator)
            
            # Add to toolbar
            self.toolbar.addAction(self.toolbar_settlement)
        
        logger.info("Settlement calculator UI components initialized")

    def _on_settlement_calculator(self):
        """Open the settlement calculator dialog."""
        try:
            # Get the currently selected claim, if any
            claim_id = None
            if hasattr(self, 'current_claim_id'):
                claim_id = self.current_claim_id
            
            # Create and show dialog
            policy_controller = self.controllers.get('policy')
            dialog = SettlementCalculatorDialog(policy_controller, claim_id, self)
            
            # Connect signals
            dialog.calculation_saved.connect(self._on_settlement_calculation_saved)
            
            # Show dialog
            dialog.exec()
            
        except Exception as e:
            logger.error(f"Error opening settlement calculator: {str(e)}")
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to open settlement calculator: {str(e)}"
            )

    def _on_settlement_calculation_saved(self, calculation_data):
        """Handle settlement calculation saved event."""
        try:
            # Log the successful save
            claim_id = calculation_data.get("inputs", {}).get("claim_id", "unknown")
            amount = calculation_data.get("results", {}).get("Estimated Settlement", 0)
            
            # Format the amount as currency
            formatted_amount = f"${amount:,.2f}"
            
            # Show notification to the user
            self.statusBar.showMessage(f"Settlement calculation saved for claim {claim_id}: {formatted_amount}", 5000)
            
            # Refresh any relevant views
            if hasattr(self, "refresh_claims_view") and callable(self.refresh_claims_view):
                self.refresh_claims_view()
            
            # If we have the settlement controller, refresh data
            if "settlement" in self.controllers:
                # Get updated statistics
                stats = self.controllers["settlement"].get_calculation_statistics()
                if stats:
                    logger.info(f"Settlement stats: {stats['count']} calculations, avg: ${stats['average_settlement']:,.2f}")
            
            logger.info(f"Settlement calculation saved for claim {claim_id}: {formatted_amount}")
            
        except Exception as e:
            logger.error(f"Error handling settlement calculation saved: {str(e)}")
            self.statusBar.showMessage(f"Error processing saved calculation: {str(e)}", 3000)

    def _on_launch_settlement_calculator(self):
        """Launch the settlement calculator dialog."""
        try:
            # Import the settlement calculator dialog
            try:
                from src.ui.dialogs.settlement_calculator_dialog import SettlementCalculatorDialog
            except ImportError:
                try:
                    from ui.dialogs.settlement_calculator_dialog import SettlementCalculatorDialog
                except ImportError:
                    raise ImportError("Could not import SettlementCalculatorDialog")
            
            # Get selected claim ID if available
            claim_id = None
            if hasattr(self, "selected_claim_id"):
                claim_id = self.selected_claim_id
            
            # Get policy controller
            policy_controller = None
            if "policy" in self.controllers:
                policy_controller = self.controllers["policy"]
            
            # Create and show dialog
            dialog = SettlementCalculatorDialog(policy_controller, claim_id, self)
            dialog.show()
            
            # Connect to calculation saved signal
            dialog.calculation_saved.connect(self._on_settlement_calculation_saved)
            
            logger.info("Launched settlement calculator dialog")
            
        except Exception as e:
            logger.error(f"Error launching settlement calculator: {str(e)}")
            QMessageBox.critical(
                self,
                "Error",
                f"Could not launch settlement calculator: {str(e)}"
            )

    def _on_launch_feature_manager(self):
        """Launch the feature manager dialog."""
        try:
            # Import the feature manager dialog
            try:
                from src.ui.dialogs.feature_manager_dialog import FeatureManagerDialog
            except ImportError:
                try:
                    from ui.dialogs.feature_manager_dialog import FeatureManagerDialog
                except ImportError:
                    raise ImportError("Could not import FeatureManagerDialog")
            
            # Create and show dialog
            dialog = FeatureManagerDialog(self)
            result = dialog.exec()
            
            # Refresh UI if changes were made
            if result == QDialog.Accepted and dialog.changes_made:
                self._refresh_ui_for_feature_changes()
            
            logger.info("Feature manager dialog completed")
            
        except Exception as e:
            logger.error(f"Error launching feature manager: {str(e)}")
            QMessageBox.critical(
                self,
                "Error",
                f"Could not launch feature manager: {str(e)}"
            )

    def _on_database_manager(self):
        """Open the database management dialog."""
        try:
            # Create database migration manager
            migration_manager = DatabaseMigration(self.engine)
            
            # Get pending migrations
            pending_migrations = migration_manager.get_pending_migrations()
            
            if pending_migrations:
                # Ask user if they want to apply pending migrations
                apply_all = QMessageBox.question(
                    self,
                    "Database Migrations",
                    f"There are {len(pending_migrations)} pending database migrations. Apply them now?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                ) == QMessageBox.Yes
                
                if apply_all:
                    # Backup database first
                    backup_path = migration_manager.backup_database()
                    if backup_path:
                        logger.info(f"Database backed up to: {backup_path}")
                        
                        # Apply migrations
                        success_count, total = migration_manager.apply_pending_migrations()
                        
                        QMessageBox.information(
                            self,
                            "Database Migrations",
                            f"Applied {success_count} of {total} migrations successfully.\nDatabase backed up to: {backup_path}"
                        )
                    else:
                        QMessageBox.warning(
                            self,
                            "Database Backup Failed",
                            "Failed to back up database, migrations not applied."
                        )
            else:
                QMessageBox.information(
                    self,
                    "Database Migrations",
                    "No pending database migrations."
                )
            
        except Exception as e:
            logger.error(f"Error managing database: {str(e)}")
            QMessageBox.critical(
                self,
                "Database Error",
                f"Error managing database: {str(e)}"
            )

    def _on_features_changed(self):
        """Handle changes to feature flags."""
        try:
            # Show notification about restart
            QMessageBox.information(
                self,
                "Feature Changes",
                "Feature flag changes have been applied. Some changes will take effect after restart."
            )
            
            # Update UI based on feature flags
            self._update_ui_for_features()
            
        except Exception as e:
            logger.error(f"Error handling feature changes: {str(e)}")
    
    def _update_ui_for_features(self):
        """Update UI components based on feature flags."""
        # This method can be called at startup and when features change
        # to show/hide UI elements based on enabled features
        
        # Check settlement calculator
        if hasattr(self, 'toolbar_settlement'):
            self.toolbar_settlement.setVisible(is_feature_enabled("settlement_calculator_enabled"))
        
        # Update other UI elements based on feature flags
        # ...
        
        # Refresh status bar
        enabled_features = feature_flags.get_enabled_features()
        self.statusBar.showMessage(f"Active features: {len(enabled_features)}", 3000)
    
    def _refresh_ui_for_feature_changes(self):
        """Update UI elements based on feature flag changes."""
        try:
            # First, try to import feature flags
            try:
                from src.utils.feature_flags import feature_flags
            except ImportError:
                try:
                    from utils.feature_flags import feature_flags
                except ImportError:
                    logger.warning("Could not import feature flags module")
                    return
            
            # Refresh the menu to show/hide features
            self._create_menu_bar()
            
            # Update toolbar to show/hide buttons
            if hasattr(self, "settlement_tool_button") and hasattr(self.settlement_tool_button, "setVisible"):
                self.settlement_tool_button.setVisible(feature_flags.is_enabled("settlement_calculator_enabled"))
            
            # Notify user about changes
            QMessageBox.information(
                self,
                "Feature Changes Applied",
                "Feature flag changes have been applied. Some changes may require a restart to take full effect."
            )
            
            # Log enabled features
            enabled_features = feature_flags.get_enabled_features()
            feature_count = len(enabled_features)
            logger.info(f"UI refreshed with {feature_count} enabled features")
            
            # Update status bar
            self.statusBar.showMessage(f"Features updated: {feature_count} features enabled", 3000)
            
        except Exception as e:
            logger.error(f"Error refreshing UI for feature changes: {str(e)}")
            QMessageBox.warning(
                self,
                "Feature Update Error",
                f"Error updating UI for feature changes: {str(e)}"
            )

    def show_board_manager(self):
        """Show the board manager dialog."""
        try:
            dialog = BoardManagerDialog(self.controllers['board'], self)
            dialog.board_updated.connect(self.refresh_boards)
            dialog.exec_()
        except Exception as e:
            handle_error(e, self, "Error showing board manager")
            
    def show_column_manager(self):
        """Show the column manager dialog."""
        try:
            # Get current board ID
            current_board = self.panels['items'].get_current_board()
            if not current_board:
                QMessageBox.warning(
                    self, "Warning",
                    "Please select a board first."
                )
                return
                
            dialog = ColumnManagerDialog(
                self.controllers['board'],
                current_board,
                self
            )
            dialog.column_updated.connect(self.refresh_columns)
            dialog.exec_()
        except Exception as e:
            handle_error(e, self, "Error showing column manager")
            
    def show_item_manager(self):
        """Show the item manager dialog."""
        try:
            # Get current board ID
            current_board = self.panels['items'].get_current_board()
            if not current_board:
                QMessageBox.warning(
                    self, "Warning",
                    "Please select a board first."
                )
                return
                
            dialog = ItemManagerDialog(
                self.controllers['board'],
                current_board,
                self
            )
            dialog.item_updated.connect(self.refresh_items)
            dialog.exec_()
        except Exception as e:
            handle_error(e, self, "Error showing item manager")
            
    def refresh_boards(self):
        """Refresh the boards list."""
        try:
            self.panels['items'].refresh_boards()
        except Exception as e:
            handle_error(e, self, "Error refreshing boards")
            
    def refresh_columns(self):
        """Refresh the columns list."""
        try:
            self.panels['items'].refresh_columns()
        except Exception as e:
            handle_error(e, self, "Error refreshing columns")
            
    def refresh_items(self):
        """Refresh the items list."""
        try:
            self.panels['items'].refresh_items()
        except Exception as e:
            handle_error(e, self, "Error refreshing items")
            
    def show_about(self):
        """Show the about dialog."""
        QMessageBox.about(
            self,
            "About PA CRM App",
            "PA CRM App\n\n"
            "A comprehensive CRM application for managing claims and settlements.\n\n"
            "Version 1.0.0"
        ) 