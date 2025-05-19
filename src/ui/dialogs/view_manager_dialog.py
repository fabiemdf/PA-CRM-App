from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QListWidget, QListWidgetItem, QMessageBox,
    QCheckBox, QSpinBox, QGroupBox, QComboBox, QDialogButtonBox
)
from PySide6.QtCore import Qt, Signal
import json

class ViewManagerDialog(QDialog):
    """Dialog for managing board views."""
    
    view_saved = Signal(str)  # Signal emitted when a view is saved
    
    def __init__(self, parent=None, board_id=None, current_columns=None, current_view=None):
        super().__init__(parent)
        self.board_id = board_id
        self.current_columns = current_columns or []
        self.current_view = current_view
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the dialog UI."""
        self.setWindowTitle("Manage Views")
        self.setMinimumWidth(600)
        
        layout = QVBoxLayout(self)
        
        # View name
        name_layout = QHBoxLayout()
        name_label = QLabel("View Name:")
        self.name_edit = QLineEdit()
        if self.current_view:
            self.name_edit.setText(self.current_view.name)
        name_layout.addWidget(name_label)
        name_layout.addWidget(self.name_edit)
        layout.addLayout(name_layout)
        
        # Column management
        columns_group = QGroupBox("Columns")
        columns_layout = QVBoxLayout(columns_group)
        
        # Column list
        self.column_list = QListWidget()
        self.column_list.setDragDropMode(QListWidget.InternalMove)
        
        # Get current column order and hidden columns
        current_order = []
        hidden_columns = []
        if self.current_view:
            try:
                current_order = json.loads(self.current_view.column_order or '[]')
                hidden_columns = json.loads(self.current_view.hidden_columns or '[]')
            except:
                pass
        
        # Add columns to list
        for col in self.current_columns:
            item = QListWidgetItem(col)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Checked if col not in hidden_columns else Qt.Unchecked)
            self.column_list.addItem(item)
            
            # If we have a current order, use it
            if current_order and col in current_order:
                # Move item to correct position
                current_index = current_order.index(col)
                self.column_list.takeItem(self.column_list.row(item))
                self.column_list.insertItem(current_index, item)
        
        columns_layout.addWidget(self.column_list)
        
        # Add buttons for column management
        button_layout = QHBoxLayout()
        
        show_all_btn = QPushButton("Show All")
        show_all_btn.clicked.connect(self._show_all_columns)
        button_layout.addWidget(show_all_btn)
        
        hide_all_btn = QPushButton("Hide All")
        hide_all_btn.clicked.connect(self._hide_all_columns)
        button_layout.addWidget(hide_all_btn)
        
        columns_layout.addLayout(button_layout)
        layout.addWidget(columns_group)
        
        # Add dialog buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self._save_view)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
    def _show_all_columns(self):
        """Show all columns."""
        for i in range(self.column_list.count()):
            item = self.column_list.item(i)
            item.setCheckState(Qt.Checked)
            
    def _hide_all_columns(self):
        """Hide all columns."""
        for i in range(self.column_list.count()):
            item = self.column_list.item(i)
            item.setCheckState(Qt.Unchecked)
            
    def _save_view(self):
        """Save the view configuration."""
        # Get view name
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Error", "Please enter a view name.")
            return
            
        # Get column order
        column_order = []
        for i in range(self.column_list.count()):
            item = self.column_list.item(i)
            column_order.append(item.text())
            
        # Get hidden columns
        hidden_columns = []
        for i in range(self.column_list.count()):
            item = self.column_list.item(i)
            if item.checkState() == Qt.Unchecked:
                hidden_columns.append(item.text())
                
        # Create view configuration
        view_config = {
            'name': name,
            'column_order': column_order,
            'hidden_columns': hidden_columns,
            'column_widths': {}  # We'll implement this later
        }
        
        # Emit signal with view configuration
        self.view_saved.emit(json.dumps(view_config))
        self.accept() 