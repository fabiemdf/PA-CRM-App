"""
Settlement controller for calculating and managing claim settlements.
"""

import logging
import json
import datetime
from typing import Dict, List, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from sqlalchemy.exc import SQLAlchemyError

# Try different import paths for flexibility
try:
    from models.settlement_models import SettlementCalculation, DamageEntry, DamageItem
    from models.database import Policy
except ImportError:
    try:
        from src.models.settlement_models import SettlementCalculation, DamageEntry, DamageItem
        from src.models.database import Policy
    except ImportError:
        # Create placeholders for development/testing
        class SettlementCalculation:
            pass
        class DamageEntry:
            pass
        class DamageItem:
            pass
        class Policy:
            pass

# Get logger
logger = logging.getLogger("monday_uploader.settlement")

class SettlementController:
    """Controller for claim settlement calculations."""
    
    def __init__(self, engine):
        """
        Initialize the settlement controller.
        
        Args:
            engine: SQLAlchemy engine
        """
        self.engine = engine
        logger.info("Settlement controller initialized")
    
    def calculate_settlement(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate a settlement based on policy and damage data.
        
        Args:
            data: Calculation input data
            
        Returns:
            Calculation results
        """
        try:
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
            
            logger.info(f"Calculated settlement for claim {data.get('claim_id')}")
            
            return {
                "inputs": data,
                "results": results
            }
            
        except Exception as e:
            logger.error(f"Error calculating settlement: {str(e)}")
            raise
    
    def save_calculation(self, calculation_data: Dict[str, Any]) -> bool:
        """
        Save a settlement calculation to the database.
        
        Args:
            calculation_data: Calculation data including results
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Extract data
            inputs = calculation_data["inputs"]
            results = calculation_data["results"]
            policy = inputs["policy"]
            claim_id = inputs.get("claim_id")
            
            # Create calculation object
            with Session(self.engine) as session:
                calculation = SettlementCalculation(
                    claim_id=claim_id,
                    policy_number=policy["policy_number"],
                    depreciation_rate=inputs["adjustments"]["depreciation_rate"],
                    overhead_profit_rate=inputs["adjustments"]["overhead_profit_rate"],
                    sales_tax_rate=inputs["adjustments"]["sales_tax_rate"],
                    total_damage_estimate=results["Total Damage Estimate"],
                    depreciation_amount=results["Depreciation"],
                    actual_cash_value=results["Actual Cash Value"],
                    recoverable_depreciation=results["Recoverable Depreciation"],
                    replacement_cost_value=results["Replacement Cost Value"],
                    overhead_profit_amount=results["Overhead & Profit"],
                    sales_tax_amount=results["Sales Tax"],
                    deductible_amount=results["Deductible"],
                    net_claim_value=results["Net Claim Value"],
                    negotiation_adjustment=results["Negotiation Adjustment"],
                    estimated_settlement=results["Estimated Settlement"],
                    calculation_data=json.dumps(calculation_data),
                    created_at=datetime.datetime.now()
                )
                
                # Add to session
                session.add(calculation)
                
                # Save damage entries if we have item IDs
                for entry in inputs["damage_entries"]:
                    # First check if we have the damage item in database
                    item_name = entry["item"]
                    category_name = entry["category"]
                    
                    # Try to find item
                    stmt = select(DamageItem).where(DamageItem.name == item_name)
                    item = session.execute(stmt).scalar_one_or_none()
                    
                    if item:
                        # Create damage entry
                        damage_entry = DamageEntry(
                            calculation_id=calculation.id,
                            item_id=item.id,
                            amount=entry["amount"],
                            quantity=entry["quantity"],
                            notes=f"Category: {category_name}"
                        )
                        session.add(damage_entry)
                
                # Commit changes
                session.commit()
                
                logger.info(f"Saved settlement calculation for claim {claim_id}")
                return True
                
        except SQLAlchemyError as e:
            logger.error(f"Database error saving settlement calculation: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Error saving settlement calculation: {str(e)}")
            return False
    
    def get_calculation(self, calculation_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a settlement calculation by ID.
        
        Args:
            calculation_id: Calculation ID
            
        Returns:
            Calculation data, or None if not found
        """
        try:
            with Session(self.engine) as session:
                calculation = session.get(SettlementCalculation, calculation_id)
                
                if not calculation:
                    return None
                
                # Convert to dictionary
                result = {
                    "id": calculation.id,
                    "claim_id": calculation.claim_id,
                    "policy_number": calculation.policy_number,
                    "total_damage_estimate": calculation.total_damage_estimate,
                    "depreciation_amount": calculation.depreciation_amount,
                    "actual_cash_value": calculation.actual_cash_value,
                    "replacement_cost_value": calculation.replacement_cost_value,
                    "deductible_amount": calculation.deductible_amount,
                    "estimated_settlement": calculation.estimated_settlement,
                    "created_at": calculation.created_at.isoformat()
                }
                
                # Add full data if available
                if calculation.calculation_data:
                    try:
                        result["full_data"] = json.loads(calculation.calculation_data)
                    except:
                        pass
                
                return result
                
        except Exception as e:
            logger.error(f"Error getting settlement calculation: {str(e)}")
            return None
    
    def get_calculations_for_claim(self, claim_id: str) -> List[Dict[str, Any]]:
        """
        Get all settlement calculations for a claim.
        
        Args:
            claim_id: Claim ID
            
        Returns:
            List of calculation data
        """
        try:
            with Session(self.engine) as session:
                stmt = select(SettlementCalculation).where(SettlementCalculation.claim_id == claim_id)
                calculations = session.execute(stmt).scalars().all()
                
                result = []
                for calc in calculations:
                    result.append({
                        "id": calc.id,
                        "claim_id": calc.claim_id,
                        "policy_number": calc.policy_number,
                        "total_damage_estimate": calc.total_damage_estimate,
                        "actual_cash_value": calc.actual_cash_value,
                        "estimated_settlement": calc.estimated_settlement,
                        "created_at": calc.created_at.isoformat()
                    })
                
                return result
                
        except Exception as e:
            logger.error(f"Error getting settlement calculations for claim: {str(e)}")
            return []
    
    def delete_calculation(self, calculation_id: int) -> bool:
        """
        Delete a settlement calculation.
        
        Args:
            calculation_id: Calculation ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with Session(self.engine) as session:
                calculation = session.get(SettlementCalculation, calculation_id)
                
                if not calculation:
                    return False
                
                # Delete related damage entries
                session.execute(DamageEntry).where(DamageEntry.calculation_id == calculation_id).delete()
                
                # Delete calculation
                session.delete(calculation)
                session.commit()
                
                logger.info(f"Deleted settlement calculation {calculation_id}")
                return True
                
        except SQLAlchemyError as e:
            logger.error(f"Database error deleting settlement calculation: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Error deleting settlement calculation: {str(e)}")
            return False
    
    def get_calculation_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about settlement calculations.
        
        Returns:
            Statistics data
        """
        try:
            with Session(self.engine) as session:
                # Get count
                count_stmt = select(func.count(SettlementCalculation.id))
                count = session.execute(count_stmt).scalar_one()
                
                # Get average settlement
                avg_stmt = select(func.avg(SettlementCalculation.estimated_settlement))
                avg_settlement = session.execute(avg_stmt).scalar_one() or 0
                
                # Get max settlement
                max_stmt = select(func.max(SettlementCalculation.estimated_settlement))
                max_settlement = session.execute(max_stmt).scalar_one() or 0
                
                return {
                    "count": count,
                    "average_settlement": avg_settlement,
                    "max_settlement": max_settlement
                }
                
        except Exception as e:
            logger.error(f"Error getting settlement statistics: {str(e)}")
            return {
                "count": 0,
                "average_settlement": 0,
                "max_settlement": 0
            } 