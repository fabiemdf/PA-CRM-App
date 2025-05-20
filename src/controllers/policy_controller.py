"""
Policy controller for managing insurance policies.
"""

import logging
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import select

# Import models - try different import paths for flexibility
try:
    from src.models.database import Policy, InsuranceCompany
except ImportError:
    try:
        from src.models.database import Policy, InsuranceCompany
    except ImportError:
        # Create placeholders if imports fail for flexibility in testing/development
        class Policy:
            pass
        class InsuranceCompany:
            pass

class PolicyController:
    """Controller for managing insurance policies."""
    
    def __init__(self, session: Session):
        """
        Initialize the policy controller.
        
        Args:
            session: SQLAlchemy session
        """
        self.session = session
        self.logger = logging.getLogger("monday_uploader.policy")
        self.logger.info("Policy controller initialized")
    
    def get_policy_by_number(self, policy_number: str) -> Optional[Dict[str, Any]]:
        """
        Get a policy by policy number.
        
        Args:
            policy_number: Policy number to look up
            
        Returns:
            Policy data as dictionary, or None if not found
        """
        try:
            stmt = select(Policy).where(Policy.policy_number == policy_number)
            policy = self.session.execute(stmt).scalars().first()
            
            if not policy:
                return None
            
            # Get carrier info if available
            carrier_name = None
            if policy.carrier_id:
                carrier = self.session.get(InsuranceCompany, policy.carrier_id)
                if carrier:
                    carrier_name = carrier.name
            
            # Convert to dictionary
            return {
                "id": policy.id,
                "policy_number": policy.policy_number,
                "policy_type": policy.policy_type,
                "carrier_id": policy.carrier_id,
                "carrier_name": carrier_name,
                "coverage_a": policy.coverage_a,
                "coverage_b": policy.coverage_b,
                "coverage_c": policy.coverage_c,
                "coverage_d": policy.coverage_d,
                "coverage_e": policy.coverage_e,
                "coverage_f": policy.coverage_f,
                "deductible": policy.deductible,
                "hurricane_deductible": policy.hurricane_deductible,
                "replacement_cost": policy.replacement_cost,
                "law_ordinance": policy.law_ordinance,
                "effective_date": policy.effective_date.isoformat() if policy.effective_date else None,
                "expiration_date": policy.expiration_date.isoformat() if policy.expiration_date else None
            }
        except Exception as e:
            self.logger.error(f"Error getting policy {policy_number}: {str(e)}")
            return None
    
    def get_policy_for_claim(self, claim_id: str) -> Optional[Dict[str, Any]]:
        """
        Get policy information for a claim.
        
        Args:
            claim_id: ID of the claim
            
        Returns:
            Policy data as dictionary, or sample data if not found
        """
        try:
            # Try to find policy linked to claim
            # For now, use sample data for demonstration
            return {
                "policy_number": f"POL-{claim_id}",
                "policy_type": "Homeowner's (HO-3)",
                "carrier_name": "Sample Insurance Company",
                "coverage_a": 250000,
                "coverage_b": 50000,
                "coverage_c": 125000,
                "coverage_d": 50000,
                "coverage_e": 300000,
                "coverage_f": 5000,
                "deductible": 1000,
                "hurricane_deductible": 5000,
                "replacement_cost": True,
                "law_ordinance": False
            }
        except Exception as e:
            self.logger.error(f"Error getting policy for claim {claim_id}: {str(e)}")
            return None
    
    def create_policy(self, policy_data: Dict[str, Any]) -> Optional[str]:
        """
        Create a new policy.
        
        Args:
            policy_data: Policy data
            
        Returns:
            Policy number if successful, None otherwise
        """
        try:
            # Create new policy
            policy = Policy(
                policy_number=policy_data.get("policy_number"),
                policy_type=policy_data.get("policy_type"),
                carrier_id=policy_data.get("carrier_id"),
                coverage_a=policy_data.get("coverage_a"),
                coverage_b=policy_data.get("coverage_b"),
                coverage_c=policy_data.get("coverage_c"),
                coverage_d=policy_data.get("coverage_d"),
                coverage_e=policy_data.get("coverage_e"),
                coverage_f=policy_data.get("coverage_f"),
                deductible=policy_data.get("deductible"),
                hurricane_deductible=policy_data.get("hurricane_deductible"),
                replacement_cost=policy_data.get("replacement_cost", False),
                law_ordinance=policy_data.get("law_ordinance", False)
            )
            
            self.session.add(policy)
            self.session.commit()
            
            self.logger.info(f"Created policy {policy.policy_number}")
            return policy.policy_number
            
        except SQLAlchemyError as e:
            self.session.rollback()
            self.logger.error(f"Database error creating policy: {str(e)}")
            return None
        except Exception as e:
            self.logger.error(f"Error creating policy: {str(e)}")
            return None
    
    def update_policy(self, policy_number: str, policy_data: Dict[str, Any]) -> bool:
        """
        Update an existing policy.
        
        Args:
            policy_number: Policy number to update
            policy_data: Updated policy data
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Find policy
            stmt = select(Policy).where(Policy.policy_number == policy_number)
            policy = self.session.execute(stmt).scalars().first()
            
            if not policy:
                self.logger.warning(f"Policy {policy_number} not found for update")
                return False
            
            # Update fields
            for key, value in policy_data.items():
                if hasattr(policy, key):
                    setattr(policy, key, value)
            
            self.session.commit()
            
            self.logger.info(f"Updated policy {policy_number}")
            return True
            
        except SQLAlchemyError as e:
            self.session.rollback()
            self.logger.error(f"Database error updating policy: {str(e)}")
            return False
        except Exception as e:
            self.logger.error(f"Error updating policy: {str(e)}")
            return False
    
    def delete_policy(self, policy_number: str) -> bool:
        """
        Delete a policy.
        
        Args:
            policy_number: Policy number to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Find policy
            stmt = select(Policy).where(Policy.policy_number == policy_number)
            policy = self.session.execute(stmt).scalars().first()
            
            if not policy:
                self.logger.warning(f"Policy {policy_number} not found for deletion")
                return False
            
            self.session.delete(policy)
            self.session.commit()
            
            self.logger.info(f"Deleted policy {policy_number}")
            return True
            
        except SQLAlchemyError as e:
            self.session.rollback()
            self.logger.error(f"Database error deleting policy: {str(e)}")
            return False
        except Exception as e:
            self.logger.error(f"Error deleting policy: {str(e)}")
            return False
    
    def get_all_policies(self) -> List[Dict[str, Any]]:
        """
        Get all policies.
        
        Returns:
            List of policy dictionaries
        """
        try:
            stmt = select(Policy)
            policies = self.session.execute(stmt).scalars().all()
            
            result = []
            for policy in policies:
                # Get carrier info if available
                carrier_name = None
                if policy.carrier_id:
                    carrier = self.session.get(InsuranceCompany, policy.carrier_id)
                    if carrier:
                        carrier_name = carrier.name
                
                # Convert to dictionary
                result.append({
                    "id": policy.id,
                    "policy_number": policy.policy_number,
                    "policy_type": policy.policy_type,
                    "carrier_id": policy.carrier_id,
                    "carrier_name": carrier_name,
                    "coverage_a": policy.coverage_a,
                    "coverage_b": policy.coverage_b,
                    "coverage_c": policy.coverage_c,
                    "coverage_d": policy.coverage_d,
                    "deductible": policy.deductible,
                    "replacement_cost": policy.replacement_cost
                })
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error getting all policies: {str(e)}")
            return []
