"""
Main window for the application.
"""

import logging
from PySide6.QtWidgets import QMainWindow, QMessageBox
from PySide6.QtCore import Qt
from controllers.board_controller import BoardController
from src.controllers.data_controller import DataController
from controllers.sync_controller import SyncController
from controllers.calendar_controller import CalendarController
from controllers.feedback_controller import FeedbackController
from controllers.settlement_controller import SettlementController
from controllers.view_controller import ViewController
from utils.error_handler import handle_error

# Get logger
logger = logging.getLogger("monday_uploader.main_window")

class MainWindow(QMainWindow):
    """
    Main window for the application.
    """
    
    def __init__(self, engine, default_boards):
        super().__init__()
        self.engine = engine
        self.default_boards = default_boards
        self.controllers = {}
        self._init_controllers()
        self._init_ui()
        
    def _init_controllers(self):
        """Initialize controllers."""
        try:
            # Create controllers
            self.controllers['board'] = BoardController(
                self.monday_api, 
                self.session,
                self.default_boards
            )
            
            # Initialize DataController with database path and parent
            self.controllers['data'] = DataController(
                db_path='monday_sync.db',
                parent=self
            )
            
            # Initialize other controllers
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
            
            # Create settlement controller if not exists
            self.controllers['settlement'] = SettlementController(self.engine)
            
            # Create view controller
            self.controllers['view'] = ViewController(self.engine)
            
            logger.info("Controllers initialized")
        except Exception as e:
            logger.error(f"Failed to initialize controllers: {str(e)}")
            handle_error(
                exception=e,
                parent=self,
                context={"module": "MainWindow", "method": "_init_controllers"},
                title="Controller Initialization Error"
            ) 