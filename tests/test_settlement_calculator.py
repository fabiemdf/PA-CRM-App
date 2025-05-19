"""
Tests for the settlement calculator functionality.
"""

import unittest
from unittest.mock import Mock, patch
import json
from datetime import datetime

from src.controllers.settlement_controller import SettlementController
from src.models.settlement_models import SettlementCalculation, DamageEntry, DamageItem
from src.models.database import Policy, InsuranceCompany

class TestSettlementCalculator(unittest.TestCase):
    """Test cases for settlement calculator functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create mock engine
        self.engine = Mock()
        
        # Create controller
        self.controller = SettlementController(self.engine)
        
        # Sample policy data
        self.sample_policy = {
            "policy_number": "POL-123",
            "policy_type": "Homeowner's (HO-3)",
            "coverage_a": 250000,
            "coverage_b": 50000,
            "coverage_c": 125000,
            "coverage_d": 50000,
            "deductible": 1000,
            "replacement_cost": True
        }
        
        # Sample damage entries
        self.sample_damage_entries = [
            {
                "category": "Roof",
                "item": "Shingles",
                "amount": 5000.0,
                "quantity": 1.0,
                "depreciation_rate": 0.05
            },
            {
                "category": "Interior",
                "item": "Drywall",
                "amount": 2000.0,
                "quantity": 2.0,
                "depreciation_rate": 0.10
            }
        ]
        
        # Sample adjustments
        self.sample_adjustments = {
            "depreciation_rate": 0.05,
            "overhead_profit_rate": 0.20,
            "sales_tax_rate": 0.07,
            "negotiation_adjustment": 0.0
        }
    
    def test_calculate_settlement(self):
        """Test settlement calculation logic."""
        # Prepare input data
        data = {
            "policy": self.sample_policy,
            "damage_entries": self.sample_damage_entries,
            "adjustments": self.sample_adjustments,
            "claim_id": "CLM-123"
        }
        
        # Calculate settlement
        result = self.controller.calculate_settlement(data)
        
        # Verify results
        self.assertIn("results", result)
        results = result["results"]
        
        # Check total damage
        expected_damage = 5000.0 + (2000.0 * 2.0)  # 9000.0
        self.assertAlmostEqual(results["Total Damage Estimate"], expected_damage)
        
        # Check depreciation
        expected_depreciation = (5000.0 * 0.05) + (4000.0 * 0.10)  # 650.0
        self.assertAlmostEqual(results["Depreciation"], expected_depreciation)
        
        # Check ACV
        expected_acv = expected_damage - expected_depreciation  # 8350.0
        self.assertAlmostEqual(results["Actual Cash Value"], expected_acv)
        
        # Check RCV
        self.assertAlmostEqual(results["Replacement Cost Value"], expected_damage)
        
        # Check overhead and profit
        expected_op = expected_damage * 0.20  # 1800.0
        self.assertAlmostEqual(results["Overhead & Profit"], expected_op)
        
        # Check sales tax
        expected_tax = expected_damage * 0.07  # 630.0
        self.assertAlmostEqual(results["Sales Tax"], expected_tax)
        
        # Check net claim
        expected_net = expected_damage + expected_op + expected_tax - 1000.0  # 10430.0
        self.assertAlmostEqual(results["Net Claim Value"], expected_net)
        
        # Check final settlement
        self.assertAlmostEqual(results["Estimated Settlement"], expected_net)
    
    def test_save_calculation(self):
        """Test saving settlement calculation."""
        # Prepare calculation data
        calculation_data = {
            "inputs": {
                "policy": self.sample_policy,
                "damage_entries": self.sample_damage_entries,
                "adjustments": self.sample_adjustments,
                "claim_id": "CLM-123"
            },
            "results": {
                "Total Damage Estimate": 9000.0,
                "Depreciation": 650.0,
                "Actual Cash Value": 8350.0,
                "Recoverable Depreciation": 650.0,
                "Replacement Cost Value": 9000.0,
                "Overhead & Profit": 1800.0,
                "Sales Tax": 630.0,
                "Deductible": 1000.0,
                "Net Claim Value": 10430.0,
                "Negotiation Adjustment": 0.0,
                "Estimated Settlement": 10430.0
            }
        }
        
        # Mock session
        mock_session = Mock()
        self.engine.__enter__.return_value = mock_session
        
        # Save calculation
        result = self.controller.save_calculation(calculation_data)
        
        # Verify result
        self.assertTrue(result)
        
        # Verify session calls
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()
    
    def test_get_calculation(self):
        """Test retrieving settlement calculation."""
        # Mock calculation data
        calculation = SettlementCalculation(
            id=1,
            claim_id="CLM-123",
            policy_number="POL-123",
            total_damage_estimate=9000.0,
            depreciation_amount=650.0,
            actual_cash_value=8350.0,
            replacement_cost_value=9000.0,
            deductible_amount=1000.0,
            estimated_settlement=10430.0,
            created_at=datetime.now()
        )
        
        # Mock session
        mock_session = Mock()
        mock_session.get.return_value = calculation
        self.engine.__enter__.return_value = mock_session
        
        # Get calculation
        result = self.controller.get_calculation(1)
        
        # Verify result
        self.assertIsNotNone(result)
        self.assertEqual(result["id"], 1)
        self.assertEqual(result["claim_id"], "CLM-123")
        self.assertEqual(result["policy_number"], "POL-123")
        self.assertEqual(result["total_damage_estimate"], 9000.0)
        self.assertEqual(result["estimated_settlement"], 10430.0)
    
    def test_get_calculations_for_claim(self):
        """Test retrieving calculations for a claim."""
        # Mock calculations
        calculations = [
            SettlementCalculation(
                id=1,
                claim_id="CLM-123",
                policy_number="POL-123",
                total_damage_estimate=9000.0,
                actual_cash_value=8350.0,
                estimated_settlement=10430.0,
                created_at=datetime.now()
            ),
            SettlementCalculation(
                id=2,
                claim_id="CLM-123",
                policy_number="POL-123",
                total_damage_estimate=10000.0,
                actual_cash_value=9000.0,
                estimated_settlement=12000.0,
                created_at=datetime.now()
            )
        ]
        
        # Mock session
        mock_session = Mock()
        mock_session.execute.return_value.scalars.return_value.all.return_value = calculations
        self.engine.__enter__.return_value = mock_session
        
        # Get calculations
        result = self.controller.get_calculations_for_claim("CLM-123")
        
        # Verify result
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["id"], 1)
        self.assertEqual(result[1]["id"], 2)
        self.assertEqual(result[0]["estimated_settlement"], 10430.0)
        self.assertEqual(result[1]["estimated_settlement"], 12000.0)
    
    def test_delete_calculation(self):
        """Test deleting a settlement calculation."""
        # Mock calculation
        calculation = SettlementCalculation(id=1)
        
        # Mock session
        mock_session = Mock()
        mock_session.get.return_value = calculation
        self.engine.__enter__.return_value = mock_session
        
        # Delete calculation
        result = self.controller.delete_calculation(1)
        
        # Verify result
        self.assertTrue(result)
        
        # Verify session calls
        mock_session.execute.assert_called_once()
        mock_session.delete.assert_called_once_with(calculation)
        mock_session.commit.assert_called_once()
    
    def test_get_calculation_statistics(self):
        """Test getting calculation statistics."""
        # Mock session
        mock_session = Mock()
        mock_session.execute.return_value.scalar_one.side_effect = [2, 11215.0, 12000.0]
        self.engine.__enter__.return_value = mock_session
        
        # Get statistics
        result = self.controller.get_calculation_statistics()
        
        # Verify result
        self.assertEqual(result["count"], 2)
        self.assertEqual(result["average_settlement"], 11215.0)
        self.assertEqual(result["max_settlement"], 12000.0)

if __name__ == '__main__':
    unittest.main() 