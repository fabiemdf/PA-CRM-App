from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime

@dataclass
class DamageItem:
    description: str
    quantity: float
    unit_cost: float
    total_cost: float
    category: str
    notes: Optional[str] = None

@dataclass
class SettlementCalculation:
    claim_id: str
    policy_limits: float
    deductible: float
    total_damages: float
    depreciation: float
    actual_cash_value: float
    replacement_cost_value: float
    settlement_amount: float
    calculation_date: datetime
    damage_items: List[DamageItem]
    notes: Optional[str] = None

    def calculate_totals(self):
        """Calculate all monetary values based on damage items"""
        self.total_damages = sum(item.total_cost for item in self.damage_items)
        self.depreciation = self.total_damages * 0.1  # Example: 10% depreciation
        self.actual_cash_value = self.total_damages - self.depreciation
        self.replacement_cost_value = self.total_damages
        self.settlement_amount = min(
            self.actual_cash_value,
            self.policy_limits - self.deductible
        ) 