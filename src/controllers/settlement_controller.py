from datetime import datetime
from typing import List, Optional, Dict, Any
from src.models.settlement_models import DamageItem, SettlementCalculation
from src.database.database_manager import DatabaseManager

class SettlementController:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    def create_calculation(self, claim_id: str, policy_limits: float, deductible: float,
                         damage_items: List[DamageItem], notes: Optional[str] = None) -> SettlementCalculation:
        """Create a new settlement calculation"""
        calculation = SettlementCalculation(
            claim_id=claim_id,
            policy_limits=policy_limits,
            deductible=deductible,
            total_damages=0,
            depreciation=0,
            actual_cash_value=0,
            replacement_cost_value=0,
            settlement_amount=0,
            calculation_date=datetime.now(),
            damage_items=damage_items,
            notes=notes
        )
        calculation.calculate_totals()
        return calculation

    def save_calculation(self, calculation: SettlementCalculation) -> bool:
        """Save a settlement calculation to the database"""
        try:
            # Convert calculation to dictionary for database storage
            calculation_dict = {
                'claim_id': calculation.claim_id,
                'policy_limits': calculation.policy_limits,
                'deductible': calculation.deductible,
                'total_damages': calculation.total_damages,
                'depreciation': calculation.depreciation,
                'actual_cash_value': calculation.actual_cash_value,
                'replacement_cost_value': calculation.replacement_cost_value,
                'settlement_amount': calculation.settlement_amount,
                'calculation_date': calculation.calculation_date.isoformat(),
                'notes': calculation.notes,
                'damage_items': [
                    {
                        'description': item.description,
                        'quantity': item.quantity,
                        'unit_cost': item.unit_cost,
                        'total_cost': item.total_cost,
                        'category': item.category,
                        'notes': item.notes
                    }
                    for item in calculation.damage_items
                ]
            }
            
            # Save to database
            self.db_manager.insert('settlement_calculations', calculation_dict)
            return True
        except Exception as e:
            print(f"Error saving calculation: {str(e)}")
            return False

    def get_calculation(self, claim_id: str) -> Optional[SettlementCalculation]:
        """Retrieve a settlement calculation for a claim"""
        try:
            result = self.db_manager.query(
                "SELECT * FROM settlement_calculations WHERE claim_id = ?",
                (claim_id,)
            )
            
            if not result:
                return None
                
            data = result[0]
            damage_items = [
                DamageItem(
                    description=item['description'],
                    quantity=item['quantity'],
                    unit_cost=item['unit_cost'],
                    total_cost=item['total_cost'],
                    category=item['category'],
                    notes=item['notes']
                )
                for item in data['damage_items']
            ]
            
            return SettlementCalculation(
                claim_id=data['claim_id'],
                policy_limits=data['policy_limits'],
                deductible=data['deductible'],
                total_damages=data['total_damages'],
                depreciation=data['depreciation'],
                actual_cash_value=data['actual_cash_value'],
                replacement_cost_value=data['replacement_cost_value'],
                settlement_amount=data['settlement_amount'],
                calculation_date=datetime.fromisoformat(data['calculation_date']),
                damage_items=damage_items,
                notes=data['notes']
            )
        except Exception as e:
            print(f"Error retrieving calculation: {str(e)}")
            return None

    def get_claim_data(self, claim_id: str) -> Optional[Dict[str, Any]]:
        """Get claim data needed for settlement calculation"""
        try:
            result = self.db_manager.query(
                "SELECT id, policy_limits, deductible FROM claims WHERE id = ?",
                (claim_id,)
            )
            
            if not result:
                return None
                
            return result[0]
        except Exception as e:
            print(f"Error retrieving claim data: {str(e)}")
            return None 