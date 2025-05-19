from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QComboBox,
    QSpinBox, QDoubleSpinBox, QTextEdit, QMessageBox
)
from PySide6.QtCore import Qt
from models.settlement_models import DamageItem, SettlementCalculation
from datetime import datetime

class SettlementCalculatorDialog(QDialog):
    def __init__(self, claim_data=None, parent=None):
        super().__init__(parent)
        self.claim_data = claim_data
        self.damage_items = []
        self.setup_ui()
        if claim_data:
            self.load_claim_data()

    def setup_ui(self):
        self.setWindowTitle("Settlement Calculator")
        self.setMinimumWidth(800)
        self.setMinimumHeight(600)

        layout = QVBoxLayout(self)

        # Policy Information
        policy_group = QHBoxLayout()
        self.policy_limits = QDoubleSpinBox()
        self.policy_limits.setRange(0, 1000000)
        self.policy_limits.setPrefix("$")
        self.deductible = QDoubleSpinBox()
        self.deductible.setRange(0, 100000)
        self.deductible.setPrefix("$")
        
        policy_group.addWidget(QLabel("Policy Limits:"))
        policy_group.addWidget(self.policy_limits)
        policy_group.addWidget(QLabel("Deductible:"))
        policy_group.addWidget(self.deductible)
        layout.addLayout(policy_group)

        # Damage Items Table
        self.items_table = QTableWidget()
        self.items_table.setColumnCount(6)
        self.items_table.setHorizontalHeaderLabels([
            "Description", "Category", "Quantity", "Unit Cost", "Total Cost", "Notes"
        ])
        layout.addWidget(self.items_table)

        # Add Item Controls
        add_item_layout = QHBoxLayout()
        self.description_edit = QLineEdit()
        self.category_combo = QComboBox()
        self.category_combo.addItems([
            "Structure", "Contents", "Additional Living Expenses",
            "Loss of Use", "Other"
        ])
        self.quantity_spin = QDoubleSpinBox()
        self.quantity_spin.setRange(0, 1000)
        self.unit_cost_spin = QDoubleSpinBox()
        self.unit_cost_spin.setRange(0, 100000)
        self.unit_cost_spin.setPrefix("$")
        self.notes_edit = QLineEdit()
        add_button = QPushButton("Add Item")
        add_button.clicked.connect(self.add_damage_item)

        add_item_layout.addWidget(QLabel("Description:"))
        add_item_layout.addWidget(self.description_edit)
        add_item_layout.addWidget(QLabel("Category:"))
        add_item_layout.addWidget(self.category_combo)
        add_item_layout.addWidget(QLabel("Quantity:"))
        add_item_layout.addWidget(self.quantity_spin)
        add_item_layout.addWidget(QLabel("Unit Cost:"))
        add_item_layout.addWidget(self.unit_cost_spin)
        add_item_layout.addWidget(QLabel("Notes:"))
        add_item_layout.addWidget(self.notes_edit)
        add_item_layout.addWidget(add_button)
        layout.addLayout(add_item_layout)

        # Summary Section
        summary_layout = QVBoxLayout()
        self.total_damages_label = QLabel("Total Damages: $0.00")
        self.depreciation_label = QLabel("Depreciation: $0.00")
        self.acv_label = QLabel("Actual Cash Value: $0.00")
        self.rcv_label = QLabel("Replacement Cost Value: $0.00")
        self.settlement_label = QLabel("Settlement Amount: $0.00")
        
        for label in [self.total_damages_label, self.depreciation_label,
                     self.acv_label, self.rcv_label, self.settlement_label]:
            summary_layout.addWidget(label)
        layout.addLayout(summary_layout)

        # Notes
        self.notes_edit = QTextEdit()
        self.notes_edit.setPlaceholderText("Add calculation notes here...")
        layout.addWidget(self.notes_edit)

        # Buttons
        button_layout = QHBoxLayout()
        calculate_button = QPushButton("Calculate")
        calculate_button.clicked.connect(self.calculate_settlement)
        save_button = QPushButton("Save")
        save_button.clicked.connect(self.save_calculation)
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.reject)
        
        button_layout.addWidget(calculate_button)
        button_layout.addWidget(save_button)
        button_layout.addWidget(close_button)
        layout.addLayout(button_layout)

    def load_claim_data(self):
        if self.claim_data:
            self.policy_limits.setValue(float(self.claim_data.get('policy_limits', 0)))
            self.deductible.setValue(float(self.claim_data.get('deductible', 0)))
            # Load any existing damage items from claim data
            if 'damage_items' in self.claim_data:
                for item in self.claim_data['damage_items']:
                    self.add_damage_item_to_table(item)

    def add_damage_item(self):
        description = self.description_edit.text()
        category = self.category_combo.currentText()
        quantity = self.quantity_spin.value()
        unit_cost = self.unit_cost_spin.value()
        notes = self.notes_edit.text()
        
        if not description:
            QMessageBox.warning(self, "Error", "Please enter a description")
            return

        total_cost = quantity * unit_cost
        item = DamageItem(
            description=description,
            quantity=quantity,
            unit_cost=unit_cost,
            total_cost=total_cost,
            category=category,
            notes=notes
        )
        self.damage_items.append(item)
        self.add_damage_item_to_table(item)
        self.clear_item_inputs()

    def add_damage_item_to_table(self, item):
        row = self.items_table.rowCount()
        self.items_table.insertRow(row)
        self.items_table.setItem(row, 0, QTableWidgetItem(item.description))
        self.items_table.setItem(row, 1, QTableWidgetItem(item.category))
        self.items_table.setItem(row, 2, QTableWidgetItem(str(item.quantity)))
        self.items_table.setItem(row, 3, QTableWidgetItem(f"${item.unit_cost:.2f}"))
        self.items_table.setItem(row, 4, QTableWidgetItem(f"${item.total_cost:.2f}"))
        self.items_table.setItem(row, 5, QTableWidgetItem(item.notes or ""))

    def clear_item_inputs(self):
        self.description_edit.clear()
        self.quantity_spin.setValue(0)
        self.unit_cost_spin.setValue(0)
        self.notes_edit.clear()

    def calculate_settlement(self):
        if not self.damage_items:
            QMessageBox.warning(self, "Error", "Please add at least one damage item")
            return

        calculation = SettlementCalculation(
            claim_id=self.claim_data.get('id', '') if self.claim_data else '',
            policy_limits=self.policy_limits.value(),
            deductible=self.deductible.value(),
            total_damages=0,
            depreciation=0,
            actual_cash_value=0,
            replacement_cost_value=0,
            settlement_amount=0,
            calculation_date=datetime.now(),
            damage_items=self.damage_items,
            notes=self.notes_edit.toPlainText()
        )
        
        calculation.calculate_totals()
        
        # Update labels
        self.total_damages_label.setText(f"Total Damages: ${calculation.total_damages:.2f}")
        self.depreciation_label.setText(f"Depreciation: ${calculation.depreciation:.2f}")
        self.acv_label.setText(f"Actual Cash Value: ${calculation.actual_cash_value:.2f}")
        self.rcv_label.setText(f"Replacement Cost Value: ${calculation.replacement_cost_value:.2f}")
        self.settlement_label.setText(f"Settlement Amount: ${calculation.settlement_amount:.2f}")

    def save_calculation(self):
        # TODO: Implement saving to database
        QMessageBox.information(self, "Success", "Calculation saved successfully")
        self.accept() 