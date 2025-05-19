from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QListWidget, QListWidgetItem, QTextEdit,
    QMessageBox, QCheckBox, QComboBox
)
from PySide6.QtCore import Qt
from models.board_view import BoardView
from datetime import datetime

class ViewManagerDialog(QDialog):
    def __init__(self, board_id: str, views: List[BoardView], parent=None):
        super().__init__(parent)
        self.board_id = board_id
        self.views = views
        self.current_view = None
        self.setup_ui()
        self.load_views()

    def setup_ui(self):
        self.setWindowTitle("View Manager")
        self.setMinimumWidth(600)
        self.setMinimumHeight(400)

        layout = QHBoxLayout(self)

        # Left side - Views list
        left_layout = QVBoxLayout()
        self.views_list = QListWidget()
        self.views_list.currentItemChanged.connect(self.view_selected)
        left_layout.addWidget(QLabel("Saved Views"))
        left_layout.addWidget(self.views_list)

        # Add/Delete buttons
        buttons_layout = QHBoxLayout()
        add_button = QPushButton("Add View")
        add_button.clicked.connect(self.add_view)
        delete_button = QPushButton("Delete View")
        delete_button.clicked.connect(self.delete_view)
        buttons_layout.addWidget(add_button)
        buttons_layout.addWidget(delete_button)
        left_layout.addLayout(buttons_layout)

        layout.addLayout(left_layout)

        # Right side - View details
        right_layout = QVBoxLayout()
        
        # Name and description
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("View Name")
        self.description_edit = QTextEdit()
        self.description_edit.setPlaceholderText("View Description")
        self.description_edit.setMaximumHeight(100)
        
        right_layout.addWidget(QLabel("View Name"))
        right_layout.addWidget(self.name_edit)
        right_layout.addWidget(QLabel("Description"))
        right_layout.addWidget(self.description_edit)

        # Default view checkbox
        self.default_checkbox = QCheckBox("Set as Default View")
        right_layout.addWidget(self.default_checkbox)

        # Save button
        save_button = QPushButton("Save View")
        save_button.clicked.connect(self.save_view)
        right_layout.addWidget(save_button)

        # Close button
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.reject)
        right_layout.addWidget(close_button)

        right_layout.addStretch()
        layout.addLayout(right_layout)

    def load_views(self):
        self.views_list.clear()
        for view in self.views:
            item = QListWidgetItem(view.name)
            item.setData(Qt.UserRole, view)
            self.views_list.addItem(item)

    def view_selected(self, current: QListWidgetItem, previous: QListWidgetItem):
        if current:
            self.current_view = current.data(Qt.UserRole)
            self.name_edit.setText(self.current_view.name)
            self.description_edit.setText(self.current_view.description or "")
            self.default_checkbox.setChecked(self.current_view.is_default)
        else:
            self.current_view = None
            self.name_edit.clear()
            self.description_edit.clear()
            self.default_checkbox.setChecked(False)

    def add_view(self):
        self.current_view = None
        self.name_edit.clear()
        self.description_edit.clear()
        self.default_checkbox.setChecked(False)
        self.name_edit.setFocus()

    def delete_view(self):
        if not self.current_view:
            return

        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete the view '{self.current_view.name}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.views.remove(self.current_view)
            self.load_views()
            self.current_view = None
            self.name_edit.clear()
            self.description_edit.clear()
            self.default_checkbox.setChecked(False)

    def save_view(self):
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Error", "Please enter a view name")
            return

        # If setting as default, unset other defaults
        if self.default_checkbox.isChecked():
            for view in self.views:
                view.is_default = False

        if self.current_view:
            # Update existing view
            self.current_view.name = name
            self.current_view.description = self.description_edit.toPlainText().strip()
            self.current_view.is_default = self.default_checkbox.isChecked()
            self.current_view.updated_at = datetime.now()
        else:
            # Create new view
            new_view = BoardView(
                id=None,
                board_id=self.board_id,
                name=name,
                description=self.description_edit.toPlainText().strip(),
                columns=[],  # TODO: Get current visible columns
                filters={},  # TODO: Get current filters
                sort_by=None,  # TODO: Get current sort
                sort_direction='asc',
                created_at=datetime.now(),
                updated_at=datetime.now(),
                is_default=self.default_checkbox.isChecked()
            )
            self.views.append(new_view)

        self.load_views()
        QMessageBox.information(self, "Success", "View saved successfully") 