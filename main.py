from controllers.settlement_controller import SettlementController
from ui.settlement_calculator_dialog import SettlementCalculatorDialog
from controllers.view_controller import ViewController
from ui.view_manager_dialog import ViewManagerDialog
from controllers.feedback_controller import FeedbackController
from src.controllers.data_controller import DataController
import sys
import logging

class MainWindow(QMainWindow):
    def __init__(self, engine, default_boards):
        super().__init__()
        self.db_manager = engine
        self.settlement_controller = SettlementController(self.db_manager)
        self.view_controller = ViewController(self.db_manager)
        self.default_boards = default_boards

    def setup_ui(self):
        # Add Settlement Calculator to Tools menu
        tools_menu = self.menuBar().addMenu("Tools")
        settlement_action = QAction("Settlement Calculator", self)
        settlement_action.triggered.connect(self.open_settlement_calculator)
        tools_menu.addAction(settlement_action)

        # Add View Manager to View menu
        view_menu = self.menuBar().addMenu("View")
        manage_views_action = QAction("Manage Views", self)
        manage_views_action.triggered.connect(self.open_view_manager)
        view_menu.addAction(manage_views_action)

    def open_settlement_calculator(self):
        # Get selected claim if any
        selected_claim = self.get_selected_claim()
        claim_data = None
        
        if selected_claim:
            claim_data = self.settlement_controller.get_claim_data(selected_claim['id'])
        
        dialog = SettlementCalculatorDialog(claim_data, self)
        if dialog.exec_() == QDialog.Accepted:
            # Handle saved calculation if needed
            pass

    def open_view_manager(self):
        current_board = self.get_current_board()
        if not current_board:
            QMessageBox.warning(self, "Error", "Please select a board first")
            return

        views = self.view_controller.get_board_views(current_board['id'])
        dialog = ViewManagerDialog(current_board['id'], views, self)
        if dialog.exec_() == QDialog.Accepted:
            # Save any changes to views
            for view in views:
                self.view_controller.save_view(view)
            
            # Apply the default view if one exists
            default_view = self.view_controller.get_default_view(current_board['id'])
            if default_view:
                self.apply_view(default_view)

    def apply_view(self, view: BoardView):
        """Apply a view's settings to the current board display"""
        # TODO: Implement view application logic
        # This will depend on how your board display is implemented
        pass

    def get_selected_claim(self):
        # Implement this method to get the currently selected claim
        # This will depend on your UI implementation
        pass

    def get_current_board(self):
        # TODO: Implement getting the currently selected board
        # This will depend on your UI implementation
        pass

def main():
    """Application entry point"""
    try:
        # Initialize logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        logger = logging.getLogger("monday_uploader")
        
        # Create application
        app = QApplication(sys.argv)
        
        # Set application style
        app.setStyle("Fusion")
        
        # Initialize database
        engine = init_db('monday_sync.db')
        
        # Initialize controllers
        data_controller = DataController(db_path='monday_sync.db')
        feedback_controller = FeedbackController(engine)
        
        # Create main window
        main_window = MainWindow(engine, DEFAULT_BOARDS)
        main_window.show()
        
        # Start event loop
        sys.exit(app.exec())
    except Exception as e:
        logger.error(f"Application error: {str(e)}")
        sys.exit(1) 