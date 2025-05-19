"""
Settlement Calculator dialog for Public Adjuster App
Calculates estimated settlements based on policy information and damage data
"""

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
import json
import os

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QTabWidget, QPushButton, QComboBox, QFormLayout,
    QDoubleSpinBox, QCheckBox, QMessageBox, QFileDialog,
    QTableWidget, QTableWidgetItem, QHeaderView, QSpinBox,
    QGroupBox, QScrollArea, QTextEdit, QFrame, QSplitter,
    QWidget, QTreeWidget, QTreeWidgetItem
)
from PySide6.QtCore import Qt, Signal, QRegularExpression
from PySide6.QtGui import QFont, QIcon, QRegularExpressionValidator

# Get logger - try multiple import paths to be flexible
try:
    from utils.logger import setup_logger, get_logger
    logger = get_logger(__name__)
except ImportError:
    try:
        from src.utils.logger import setup_logger, get_logger
        logger = get_logger(__name__)
    except ImportError:
        import logging
        logger = logging.getLogger(__name__)

# Try to import the models and controllers
try:
    from controllers.policy_controller import PolicyController
    from models.settlement_models import SettlementCalculation
except ImportError:
    try:
        from src.controllers.policy_controller import PolicyController
        from src.models.settlement_models import SettlementCalculation
    except ImportError:
        # If imports fail, create placeholder classes for development
        class PolicyController:
            def __init__(self, *args, **kwargs):
                pass
                
            def get_policy_for_claim(self, claim_id):
                return {
                    "policy_number": f"POL-{claim_id}",
                    "policy_type": "Homeowner's (HO-3)",
                    "coverage_a": 250000,
                    "coverage_b": 50000,
                    "coverage_c": 125000,
                    "coverage_d": 50000,
                    "deductible": 1000,
                    "replacement_cost": True
                }
            
        class SettlementCalculation:
            pass

class SettlementCalculatorDialog(QDialog):
    """
    Dialog for calculating potential claim settlements based on
    policy information, damage data, and historical settlements.
    """
    
    calculation_saved = Signal(dict)
    
    def __init__(self, 
                 policy_controller: PolicyController, 
                 claim_id: Optional[str] = None,
                 parent=None):
        """Initialize the settlement calculator dialog."""
        super().__init__(parent)
        
        self.policy_controller = policy_controller
        self.claim_id = claim_id
        self.categories = {}
        self.calculation_results = {}
        
        self.setWindowTitle("Settlement Calculator")
        self.setMinimumSize(900, 700)
        
        # Setup UI
        self._setup_ui()
        
        # If claim_id is provided, load its data
        if claim_id:
            self._load_claim_data(claim_id)
        
        logger.info("Settlement calculator dialog initialized")
    
    def _setup_ui(self):
        """Setup the user interface."""
        main_layout = QVBoxLayout(self)
        
        # Create splitter for main sections
        splitter = QSplitter(Qt.Horizontal)
        
        # Left side (input panels)
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        # Create tab widget for input sections
        self.tab_widget = QTabWidget()
        
        # Setup tabs
        self._setup_policy_tab()
        self._setup_damage_tab()
        self._setup_adjustments_tab()
        
        # Add tab widget to left layout
        left_layout.addWidget(self.tab_widget)
        
        # Right side (summary and controls)
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        # Results section
        results_group = QGroupBox("Calculation Results")
        results_layout = QVBoxLayout(results_group)
        
        # Create results tree widget
        self.results_tree = QTreeWidget()
        self.results_tree.setHeaderLabels(["Item", "Value"])
        self.results_tree.setAlternatingRowColors(True)
        self.results_tree.setColumnWidth(0, 250)
        results_layout.addWidget(self.results_tree)
        
        # Add results group to right layout
        right_layout.addWidget(results_group)
        
        # Notes section
        notes_group = QGroupBox("Notes")
        notes_layout = QVBoxLayout(notes_group)
        
        # Create notes text edit
        self.notes_edit = QTextEdit()
        self.notes_edit.setPlaceholderText("Enter any notes about this calculation...")
        notes_layout.addWidget(self.notes_edit)
        
        # Add notes group to right layout
        right_layout.addWidget(notes_group)
        
        # Add widgets to splitter
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        
        # Set initial sizes (60/40 split)
        splitter.setSizes([540, 360])
        
        # Add splitter to main layout
        main_layout.addWidget(splitter)
        
        # Create buttons
        button_layout = QHBoxLayout()
        
        # Calculate button
        self.calculate_btn = QPushButton("Calculate")
        self.calculate_btn.clicked.connect(self._on_calculate)
        button_layout.addWidget(self.calculate_btn)
        
        # Save button
        self.save_btn = QPushButton("Save Calculation")
        self.save_btn.setEnabled(False)  # Enable after calculation
        self.save_btn.clicked.connect(self._on_save)
        button_layout.addWidget(self.save_btn)
        
        # Reset button
        self.reset_btn = QPushButton("Reset")
        self.reset_btn.clicked.connect(self._on_reset)
        button_layout.addWidget(self.reset_btn)
        
        # Close button
        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.close_btn)
        
        # Add button layout to main layout
        main_layout.addLayout(button_layout)
    
    def _setup_policy_tab(self):
        """Setup the policy information tab."""
        policy_tab = QWidget()
        policy_layout = QVBoxLayout(policy_tab)
        
        # Add policy details form
        policy_form = QFormLayout()
        
        # Policy number
        self.policy_number = QLineEdit()
        policy_form.addRow("Policy Number:", self.policy_number)
        
        # Policy type
        self.policy_type = QComboBox()
        self.policy_type.addItems([
            "Homeowner's (HO-3)", 
            "Homeowner's (HO-5)",
            "Condominium (HO-6)",
            "Renter's (HO-4)",
            "Dwelling Fire (DP-3)",
            "Landlord (DP-3)",
            "Commercial Property",
            "Business Owner's Policy (BOP)",
            "Other"
        ])
        policy_form.addRow("Policy Type:", self.policy_type)
        
        # Carrier
        self.carrier = QLineEdit()
        policy_form.addRow("Insurance Carrier:", self.carrier)
        
        # Coverage A
        self.coverage_a = QLineEdit()
        self.coverage_a.setValidator(QRegularExpressionValidator(QRegularExpression(r"[0-9]*\.?[0-9]+")))
        policy_form.addRow("Coverage A (Dwelling):", self.coverage_a)
        
        # Coverage B
        self.coverage_b = QLineEdit()
        self.coverage_b.setValidator(QRegularExpressionValidator(QRegularExpression(r"[0-9]*\.?[0-9]+")))
        policy_form.addRow("Coverage B (Other Structures):", self.coverage_b)
        
        # Coverage C
        self.coverage_c = QLineEdit()
        self.coverage_c.setValidator(QRegularExpressionValidator(QRegularExpression(r"[0-9]*\.?[0-9]+")))
        policy_form.addRow("Coverage C (Personal Property):", self.coverage_c)
        
        # Coverage D
        self.coverage_d = QLineEdit()
        self.coverage_d.setValidator(QRegularExpressionValidator(QRegularExpression(r"[0-9]*\.?[0-9]+")))
        policy_form.addRow("Coverage D (Loss of Use):", self.coverage_d)
        
        # Deductible
        self.deductible = QLineEdit()
        self.deductible.setValidator(QRegularExpressionValidator(QRegularExpression(r"[0-9]*\.?[0-9]+")))
        policy_form.addRow("Deductible:", self.deductible)
        
        # Hurricane deductible
        self.hurricane_deductible = QLineEdit()
        self.hurricane_deductible.setValidator(QRegularExpressionValidator(QRegularExpression(r"[0-9]*\.?[0-9]+")))
        policy_form.addRow("Hurricane/Wind Deductible:", self.hurricane_deductible)
        
        # Replacement cost
        self.replacement_cost = QCheckBox("Policy has replacement cost coverage")
        policy_form.addRow("", self.replacement_cost)
        
        # Law & ordinance
        self.law_ordinance = QCheckBox("Policy has law & ordinance coverage")
        policy_form.addRow("", self.law_ordinance)
        
        # Add form to layout
        policy_layout.addLayout(policy_form)
        
        # Add spacer
        policy_layout.addStretch()
        
        # Add tab
        self.tab_widget.addTab(policy_tab, "Policy Information")
    
    def _setup_damage_tab(self):
        """Setup the damage entry tab."""
        damage_tab = QWidget()
        damage_layout = QVBoxLayout(damage_tab)
        
        # Create scroll area for damage entries
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        
        # Damage categories and items will be dynamically added here
        self._setup_damage_categories(scroll_layout)
        
        # Set scroll widget and add to layout
        scroll_area.setWidget(scroll_widget)
        damage_layout.addWidget(scroll_area)
        
        # Add tab
        self.tab_widget.addTab(damage_tab, "Damage Assessment")
    
    def _setup_damage_categories(self, layout):
        """
        Setup damage categories and items.
        
        Args:
            layout: Layout to add categories to
        """
        try:
            # Import initial categories data
            try:
                from src.data.initial_categories import DEFAULT_CATEGORIES
            except ImportError:
                try:
                    from data.initial_categories import DEFAULT_CATEGORIES
                except ImportError:
                    # Create basic categories if import fails
                    DEFAULT_CATEGORIES = [
                        {
                            "name": "Structure",
                            "description": "Damage to the structure",
                            "items": [
                                {"name": "Roof", "default_depreciation_rate": 0.05},
                                {"name": "Walls", "default_depreciation_rate": 0.03}
                            ]
                        },
                        {
                            "name": "Contents",
                            "description": "Damage to contents",
                            "items": [
                                {"name": "Furniture", "default_depreciation_rate": 0.10},
                                {"name": "Electronics", "default_depreciation_rate": 0.15}
                            ]
                        }
                    ]
            
            # Create entry widgets for each category
            for category_data in DEFAULT_CATEGORIES:
                category_name = category_data["name"]
                
                # Create group box for category
                category_group = QGroupBox(f"{category_name} Damage")
                category_layout = QVBoxLayout(category_group)
                
                # Create table for items
                item_layout = QFormLayout()
                
                # Store item widgets
                category_items = {}
                
                # Add rows for each item
                for item_data in category_data["items"]:
                    item_name = item_data["name"]
                    depreciation_rate = item_data.get("default_depreciation_rate", 0.0)
                    
                    # Create inline widget with amount and quantity
                    item_widget = QWidget()
                    item_layout_inner = QHBoxLayout(item_widget)
                    item_layout_inner.setContentsMargins(0, 0, 0, 0)
                    
                    # Amount field
                    amount_label = QLabel("Amount: $")
                    amount_field = QLineEdit()
                    amount_field.setValidator(QRegularExpressionValidator(QRegularExpression(r"[0-9]*\.?[0-9]+")))
                    item_layout_inner.addWidget(amount_label)
                    item_layout_inner.addWidget(amount_field)
                    
                    # Quantity field
                    quantity_label = QLabel("Quantity:")
                    quantity_field = QDoubleSpinBox()
                    quantity_field.setMinimum(0.0)
                    quantity_field.setMaximum(9999.99)
                    quantity_field.setValue(1.0)
                    quantity_field.setDecimals(2)
                    item_layout_inner.addWidget(quantity_label)
                    item_layout_inner.addWidget(quantity_field)
                    
                    # Depreciation rate field
                    depreciation_label = QLabel("Depr. Rate:")
                    depreciation_field = QDoubleSpinBox()
                    depreciation_field.setMinimum(0.0)
                    depreciation_field.setMaximum(1.0)
                    depreciation_field.setValue(depreciation_rate)
                    depreciation_field.setSingleStep(0.01)
                    depreciation_field.setDecimals(2)
                    item_layout_inner.addWidget(depreciation_label)
                    item_layout_inner.addWidget(depreciation_field)
                    
                    # Store fields
                    category_items[item_name] = {
                        "amount": amount_field,
                        "quantity": quantity_field,
                        "depreciation_rate": depreciation_field
                    }
                    
                    # Add to form layout
                    item_layout.addRow(f"{item_name}:", item_widget)
                
                # Add item layout to category
                category_layout.addLayout(item_layout)
                
                # Store category items
                self.categories[category_name] = category_items
                
                # Add category to main layout
                layout.addWidget(category_group)
            
        except Exception as e:
            logger.error(f"Error setting up damage categories: {str(e)}")
            
            # Show empty message
            empty_label = QLabel("Error loading damage categories. Please try again.")
            layout.addWidget(empty_label)
    
    def _setup_adjustments_tab(self):
        """Setup the adjustments tab."""
        adjustments_tab = QWidget()
        adjustments_layout = QVBoxLayout(adjustments_tab)
        
        # Create form layout for adjustments
        form_layout = QFormLayout()
        
        # Depreciation rate
        self.depreciation_rate = QDoubleSpinBox()
        self.depreciation_rate.setMinimum(0.0)
        self.depreciation_rate.setMaximum(1.0)
        self.depreciation_rate.setValue(0.05)  # 5% default
        self.depreciation_rate.setSingleStep(0.01)
        self.depreciation_rate.setDecimals(2)
        form_layout.addRow("Default Depreciation Rate:", self.depreciation_rate)
        
        # Overhead & profit
        self.overhead_profit = QDoubleSpinBox()
        self.overhead_profit.setMinimum(0.0)
        self.overhead_profit.setMaximum(0.5)
        self.overhead_profit.setValue(0.20)  # 20% default
        self.overhead_profit.setSingleStep(0.01)
        self.overhead_profit.setDecimals(2)
        form_layout.addRow("Overhead & Profit Rate:", self.overhead_profit)
        
        # Sales tax
        self.sales_tax = QDoubleSpinBox()
        self.sales_tax.setMinimum(0.0)
        self.sales_tax.setMaximum(0.15)
        self.sales_tax.setValue(0.07)  # 7% default
        self.sales_tax.setSingleStep(0.01)
        self.sales_tax.setDecimals(2)
        form_layout.addRow("Sales Tax Rate:", self.sales_tax)
        
        # Add separator
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        
        # Negotiation adjustment
        self.negotiation_adjustment = QDoubleSpinBox()
        self.negotiation_adjustment.setMinimum(-0.5)
        self.negotiation_adjustment.setMaximum(0.5)
        self.negotiation_adjustment.setValue(0.0)
        self.negotiation_adjustment.setSingleStep(0.01)
        self.negotiation_adjustment.setDecimals(2)
        form_layout.addRow("Negotiation Adjustment:", self.negotiation_adjustment)
        
        # Add form to layout
        adjustments_layout.addLayout(form_layout)
        
        # Add stretch to push form to the top
        adjustments_layout.addStretch()
        
        # Add tab
        self.tab_widget.addTab(adjustments_tab, "Adjustments")
    
    def _load_claim_data(self, claim_id: str):
        """Load data for the specified claim."""
        try:
            # Get data controller from parent window
            data_controller = None
            if hasattr(self.parent(), "controllers") and "data" in self.parent().controllers:
                data_controller = self.parent().controllers["data"]
            
            if data_controller:
                # Load claim data from database
                claims = data_controller.session.query(Claim).filter_by(id=claim_id).all()
                if claims:
                    claim = claims[0]
                    
                    # Set policy number
                    self.policy_number.setText(claim.policy_number or "")
                    
                    # Set carrier
                    self.carrier.setText(claim.insurance_company or "")
                    
                    # Set coverage values
                    self.coverage_a.setText(str(claim.insured_amount or ""))
                    
                    # Set deductible if available
                    if hasattr(claim, "deductible"):
                        self.deductible.setText(str(claim.deductible or ""))
                    
                    # Set initial offer if available
                    if hasattr(claim, "initial_offer"):
                        try:
                            self.negotiation_adjustment.setValue(float(claim.initial_offer or 0))
                        except (ValueError, TypeError):
                            pass
                    
                    # Set policy type based on loss type if available
                    if claim.loss_type:
                        loss_type = claim.loss_type.lower()
                        if "home" in loss_type or "house" in loss_type:
                            self.policy_type.setCurrentText("Homeowner's (HO-3)")
                        elif "condo" in loss_type:
                            self.policy_type.setCurrentText("Condominium (HO-6)")
                        elif "rent" in loss_type:
                            self.policy_type.setCurrentText("Renter's (HO-4)")
                        elif "commercial" in loss_type:
                            self.policy_type.setCurrentText("Commercial Property")
                    
                    logger.info(f"Loaded claim data for claim {claim_id}")
                    return
            
            # If we couldn't load from database, try policy controller
            if self.policy_controller:
                policy_data = self.policy_controller.get_policy_for_claim(claim_id)
                if policy_data:
                    self.policy_number.setText(policy_data.get("policy_number", ""))
                    self.policy_type.setCurrentText(policy_data.get("policy_type", "Homeowner's (HO-3)"))
                    
                    # Set coverage values
                    self.coverage_a.setText(str(policy_data.get("coverage_a", "")))
                    self.coverage_b.setText(str(policy_data.get("coverage_b", "")))
                    self.coverage_c.setText(str(policy_data.get("coverage_c", "")))
                    self.coverage_d.setText(str(policy_data.get("coverage_d", "")))
                    
                    # Set deductible
                    self.deductible.setText(str(policy_data.get("deductible", "")))
                    
                    # Set checkboxes
                    self.replacement_cost.setChecked(policy_data.get("replacement_cost", False))
                    self.law_ordinance.setChecked(policy_data.get("law_ordinance", False))
                    
                    # Set hurricane deductible
                    self.hurricane_deductible.setText(str(policy_data.get("hurricane_deductible", "")))
                    
                    logger.info(f"Loaded policy data for claim {claim_id}")
                
        except Exception as e:
            logger.error(f"Error loading claim data: {str(e)}")
            QMessageBox.warning(
                self, 
                "Data Loading Error",
                f"Could not load claim data: {str(e)}"
            )
    
    def _on_calculate(self):
        """Handle calculate button click."""
        try:
            # Collect policy data
            policy_data = {
                "policy_number": self.policy_number.text(),
                "policy_type": self.policy_type.currentText(),
                "carrier": self.carrier.text(),
                "coverage_a": float(self.coverage_a.text() or 0),
                "coverage_b": float(self.coverage_b.text() or 0),
                "coverage_c": float(self.coverage_c.text() or 0),
                "coverage_d": float(self.coverage_d.text() or 0),
                "deductible": float(self.deductible.text() or 0),
                "hurricane_deductible": float(self.hurricane_deductible.text() or 0),
                "replacement_cost": self.replacement_cost.isChecked(),
                "law_ordinance": self.law_ordinance.isChecked()
            }
            
            # Collect damage entries
            damage_entries = []
            for category_name, items in self.categories.items():
                for item_name, fields in items.items():
                    amount_text = fields["amount"].text()
                    if amount_text:
                        entry = {
                            "category": category_name,
                            "item": item_name,
                            "amount": float(amount_text),
                            "quantity": fields["quantity"].value(),
                            "depreciation_rate": fields["depreciation_rate"].value()
                        }
                        damage_entries.append(entry)
            
            # Collect adjustment data
            adjustment_data = {
                "depreciation_rate": self.depreciation_rate.value(),
                "overhead_profit_rate": self.overhead_profit.value(),
                "sales_tax_rate": self.sales_tax.value(),
                "negotiation_adjustment": self.negotiation_adjustment.value()
            }
            
            # Check if we have damage entries
            if not damage_entries:
                QMessageBox.warning(
                    self,
                    "No Damage Entries",
                    "Please enter at least one damage amount before calculating."
                )
                return
            
            # Calculate settlement
            calculation_input = {
                "policy": policy_data,
                "damage_entries": damage_entries,
                "adjustments": adjustment_data,
                "claim_id": self.claim_id
            }
            
            # Call settlement controller if available
            if hasattr(self.parent(), "controllers") and "settlement" in self.parent().controllers:
                controller = self.parent().controllers["settlement"]
                results = controller.calculate_settlement(calculation_input)
            else:
                # Fallback to direct calculation
                results = self._calculate_settlement(calculation_input)
            
            # Store results
            self.calculation_results = results
            
            # Display results
            self._display_results(results)
            
            # Enable save button
            self.save_btn.setEnabled(True)
            
            logger.info("Settlement calculation completed")
            
        except ValueError as e:
            QMessageBox.warning(
                self,
                "Invalid Input",
                f"Please check your input values: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Error calculating settlement: {str(e)}")
            QMessageBox.critical(
                self,
                "Calculation Error",
                f"An error occurred during calculation: {str(e)}"
            )
    
    def _calculate_settlement(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate settlement results.
        
        Args:
            data: Calculation input data
            
        Returns:
            Calculation results
        """
        # Extract input data
        policy = data["policy"]
        damage_entries = data["damage_entries"]
        adjustments = data["adjustments"]
        
        # Calculate total damage amount
        total_damage = 0.0
        for entry in damage_entries:
            total_damage += entry["amount"] * entry["quantity"]
        
        # Calculate depreciation
        total_depreciation = 0.0
        for entry in damage_entries:
            depreciation_rate = entry["depreciation_rate"]
            depreciation = entry["amount"] * entry["quantity"] * depreciation_rate
            total_depreciation += depreciation
        
        # Calculate actual cash value
        acv = total_damage - total_depreciation
        
        # Calculate replacement cost value (RCV) - same as total damage
        rcv = total_damage
        
        # Calculate overhead and profit
        overhead_profit = total_damage * adjustments["overhead_profit_rate"]
        
        # Calculate sales tax
        sales_tax = total_damage * adjustments["sales_tax_rate"]
        
        # Determine which deductible to use - default to regular deductible
        deductible = policy["deductible"]
        
        # Calculate net claim value (after deductible)
        if policy["replacement_cost"]:
            # If replacement cost policy, deduct from RCV
            net_claim = rcv + overhead_profit + sales_tax - deductible
        else:
            # If ACV policy, deduct from ACV
            net_claim = acv + overhead_profit + sales_tax - deductible
        
        # Apply negotiation adjustment
        adjustment = net_claim * adjustments["negotiation_adjustment"]
        estimated_settlement = net_claim + adjustment
        
        # Create results dictionary
        results = {
            "Total Damage Estimate": total_damage,
            "Depreciation": total_depreciation,
            "Actual Cash Value": acv,
            "Recoverable Depreciation": total_depreciation if policy["replacement_cost"] else 0.0,
            "Replacement Cost Value": rcv,
            "Overhead & Profit": overhead_profit,
            "Sales Tax": sales_tax,
            "Deductible": deductible,
            "Net Claim Value": net_claim,
            "Negotiation Adjustment": adjustment,
            "Estimated Settlement": estimated_settlement
        }
        
        return {
            "inputs": data,
            "results": results
        }
    
    def _display_results(self, calculation_data: Dict[str, Any]):
        """
        Display calculation results in the results tree.
        
        Args:
            calculation_data: Calculation data including results
        """
        # Clear results tree
        self.results_tree.clear()
        
        # Get results
        results = calculation_data["results"]
        
        # Create top-level items
        damage_item = QTreeWidgetItem(["Damage Assessment", ""])
        settlement_item = QTreeWidgetItem(["Settlement Calculation", ""])
        
        # Add damage details
        total_damage_item = QTreeWidgetItem(damage_item, ["Total Damage Estimate", f"${results['Total Damage Estimate']:,.2f}"])
        depreciation_item = QTreeWidgetItem(damage_item, ["Depreciation", f"${results['Depreciation']:,.2f}"])
        acv_item = QTreeWidgetItem(damage_item, ["Actual Cash Value (ACV)", f"${results['Actual Cash Value']:,.2f}"])
        
        # Add settlement details
        rcv_item = QTreeWidgetItem(settlement_item, ["Replacement Cost Value (RCV)", f"${results['Replacement Cost Value']:,.2f}"])
        op_item = QTreeWidgetItem(settlement_item, ["Overhead & Profit", f"${results['Overhead & Profit']:,.2f}"])
        tax_item = QTreeWidgetItem(settlement_item, ["Sales Tax", f"${results['Sales Tax']:,.2f}"])
        deductible_item = QTreeWidgetItem(settlement_item, ["Deductible", f"${results['Deductible']:,.2f}"])
        net_item = QTreeWidgetItem(settlement_item, ["Net Claim Value", f"${results['Net Claim Value']:,.2f}"])
        
        if results['Negotiation Adjustment'] != 0:
            adj_item = QTreeWidgetItem(settlement_item, ["Negotiation Adjustment", f"${results['Negotiation Adjustment']:,.2f}"])
        
        # Create final estimate item (bold)
        final_item = QTreeWidgetItem(["Estimated Settlement", f"${results['Estimated Settlement']:,.2f}"])
        font = final_item.font(0)
        font.setBold(True)
        final_item.setFont(0, font)
        final_item.setFont(1, font)
        
        # Add recoverable depreciation if applicable
        if results['Recoverable Depreciation'] > 0:
            rd_item = QTreeWidgetItem(["Recoverable Depreciation", f"${results['Recoverable Depreciation']:,.2f}"])
            self.results_tree.addTopLevelItem(rd_item)
        
        # Add items to tree
        self.results_tree.addTopLevelItem(damage_item)
        self.results_tree.addTopLevelItem(settlement_item)
        self.results_tree.addTopLevelItem(final_item)
        
        # Expand all items
        self.results_tree.expandAll()
    
    def _on_save(self):
        """Handle save button click."""
        try:
            # Check if we have results
            if not self.calculation_results:
                QMessageBox.warning(
                    self,
                    "No Calculation",
                    "Please calculate the settlement before saving."
                )
                return
            
            # Get notes
            notes = self.notes_edit.toPlainText()
            
            # Create save data
            save_data = self.calculation_results.copy()
            save_data["notes"] = notes
            save_data["calculation_date"] = datetime.datetime.now().isoformat()
            
            # Call settlement controller if available
            if hasattr(self.parent(), "controllers") and "settlement" in self.parent().controllers:
                controller = self.parent().controllers["settlement"]
                saved = controller.save_calculation(save_data)
                
                if saved:
                    QMessageBox.information(
                        self,
                        "Calculation Saved",
                        "The settlement calculation was saved successfully."
                    )
                    
                    # Emit signal
                    self.calculation_saved.emit(save_data)
                else:
                    QMessageBox.warning(
                        self,
                        "Save Error",
                        "Failed to save the settlement calculation."
                    )
            else:
                # Show warning that we're in demo mode
                QMessageBox.information(
                    self,
                    "Demo Mode",
                    "Settlement controller not available. In a production environment, "
                    "this calculation would be saved to the database."
                )
                
                # Still emit signal for demo purposes
                self.calculation_saved.emit(save_data)
            
            logger.info("Settlement calculation saved")
            
        except Exception as e:
            logger.error(f"Error saving calculation: {str(e)}")
            QMessageBox.critical(
                self,
                "Save Error",
                f"An error occurred while saving: {str(e)}"
            )
    
    def _on_reset(self):
        """Handle reset button click."""
        # Confirm reset
        confirmed = QMessageBox.question(
            self,
            "Confirm Reset",
            "Are you sure you want to reset all fields?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        ) == QMessageBox.Yes
        
        if confirmed:
            # Reset damage entries
            for category_name, items in self.categories.items():
                for item_name, fields in items.items():
                    fields["amount"].clear()
                    fields["quantity"].setValue(1.0)
            
            # Reset adjustments to defaults
            self.depreciation_rate.setValue(0.05)
            self.overhead_profit.setValue(0.20)
            self.sales_tax.setValue(0.07)
            self.negotiation_adjustment.setValue(0.0)
            
            # Clear results
            self.results_tree.clear()
            self.calculation_results = {}
            
            # Clear notes
            self.notes_edit.clear()
            
            # Disable save button
            self.save_btn.setEnabled(False)
            
            logger.info("Settlement calculator reset")


# Example model class for settlement calculations
class SettlementController:
    """Controller for claim settlement calculations."""
    
    def __init__(self, engine):
        """Initialize the settlement controller."""
        self.engine = engine
        self.logger = logging.getLogger("monday_uploader.settlement")
    
    def save_calculation(self, calculation: SettlementCalculation) -> bool:
        """Save a settlement calculation to the database."""
        try:
            from sqlalchemy.orm import Session
            
            with Session(self.engine) as session:
                session.add(calculation)
                session.commit()
                
            self.logger.info(f"Saved settlement calculation for claim {calculation.claim_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving settlement calculation: {str(e)}")
            return False
    
    def get_calculation(self, calculation_id: int) -> Optional[SettlementCalculation]:
        """Get a settlement calculation by ID."""
        try:
            from sqlalchemy.orm import Session
            
            with Session(self.engine) as session:
                calculation = session.query(SettlementCalculation).filter_by(id=calculation_id).first()
                return calculation
                
        except Exception as e:
            self.logger.error(f"Error getting settlement calculation: {str(e)}")
            return None
    
    def get_calculations_for_claim(self, claim_id: str) -> List[SettlementCalculation]:
        """Get all settlement calculations for a claim."""
        try:
            from sqlalchemy.orm import Session
            
            with Session(self.engine) as session:
                calculations = session.query(SettlementCalculation).filter_by(claim_id=claim_id).all()
                return calculations
                
        except Exception as e:
            self.logger.error(f"Error getting settlement calculations for claim: {str(e)}")
            return [] 