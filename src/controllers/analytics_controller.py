#!/usr/bin/env python3
"""
Analytics Controller
Handles data processing and statistics generation for the Claims Analytics Dashboard
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import pandas as pd
from sqlalchemy import func, and_, desc, Integer

from models.database import Claim, CalendarEvent, BoardView
from utils.error_handling import handle_error, MondayError, ErrorCodes

logger = logging.getLogger(__name__)

class AnalyticsController:
    def __init__(self, session):
        self.session = session

    def get_claims_statistics(self, time_period='all'):
        """Get claims statistics for the specified time period."""
        try:
            # Get date range based on time period
            end_date = datetime.now()
            if time_period == 'week':
                start_date = end_date - timedelta(days=7)
            elif time_period == 'month':
                start_date = end_date - timedelta(days=30)
            elif time_period == 'year':
                start_date = end_date - timedelta(days=365)
            else:  # 'all'
                start_date = datetime.min

            # Get total claims
            total_claims = self.session.query(Claim).filter(
                Claim.created_at >= start_date
            ).count()

            # Get recent claims (last 30 days)
            recent_claims = self.session.query(Claim).filter(
                Claim.created_at >= end_date - timedelta(days=30)
            ).count()

            # Get average settlement time
            try:
                avg_settlement_time = self.session.query(
                    func.avg(
                        func.cast(
                            func.strftime('%d', Claim.settled_at - Claim.created_at),
                            Integer
                        )
                    )
                ).filter(
                    Claim.settled_at.isnot(None),
                    Claim.created_at.isnot(None)
                ).scalar() or 0
            except Exception as e:
                logger.warning(f"Could not calculate average settlement time: {str(e)}")
                avg_settlement_time = 0

            # Get success rate
            try:
                total_settled = self.session.query(Claim).filter(
                    Claim.settled_at.isnot(None)
                ).count()
                success_rate = (total_settled / total_claims * 100) if total_claims > 0 else 0
            except Exception as e:
                logger.warning(f"Could not calculate success rate: {str(e)}")
                success_rate = 0

            return {
                'total_claims': total_claims,
                'recent_claims': recent_claims,
                'avg_settlement_time': round(avg_settlement_time, 1),
                'success_rate': round(success_rate, 1)
            }

        except Exception as e:
            logger.error(f"Error getting claims statistics: {str(e)}")
            raise MondayError(
                ErrorCodes.DATABASE_ERROR,
                f"Error getting claims statistics: {str(e)}"
            )

    def get_claims_by_status(self) -> List[Dict[str, Any]]:
        """Get claims count grouped by status"""
        try:
            status_counts = self.session.query(
                Claim.status,
                func.count(Claim.id)
            ).group_by(Claim.status).all()

            return [{'status': status or 'Unknown', 'count': count} 
                   for status, count in status_counts]
        except Exception as e:
            logger.error(f"Error getting claims by status: {str(e)}")
            raise MondayError(
                f"Error getting claims by status: {str(e)}",
                error_code=ErrorCodes.DB_QUERY_ERROR,
                original_exception=e
            )

    def get_monthly_claims_trend(self) -> List[Dict[str, Any]]:
        """Get monthly claims trend for the last 12 months"""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=365)

            monthly_claims = self.session.query(
                func.strftime('%Y-%m', Claim.created_at).label('month'),
                func.count(Claim.id).label('count')
            ).filter(
                Claim.created_at >= start_date
            ).group_by('month').order_by('month').all()

            return [{'month': month, 'count': count} 
                   for month, count in monthly_claims]
        except Exception as e:
            logger.error(f"Error getting monthly claims trend: {str(e)}")
            raise MondayError(
                f"Error getting monthly claims trend: {str(e)}",
                error_code=ErrorCodes.DB_QUERY_ERROR,
                original_exception=e
            )

    def get_settlement_amounts(self) -> Dict[str, float]:
        """Get settlement amount statistics"""
        try:
            result = self.session.query(
                func.min(Claim.settlement_amount).label('min'),
                func.max(Claim.settlement_amount).label('max'),
                func.avg(Claim.settlement_amount).label('avg')
            ).filter(
                Claim.settlement_amount.isnot(None),
                Claim.settlement_amount > 0
            ).first()

            return {
                'min': result.min or 0,
                'max': result.max or 0,
                'avg': result.avg or 0
            }
        except Exception as e:
            logger.error(f"Error getting settlement amounts: {str(e)}")
            raise MondayError(
                f"Error getting settlement amounts: {str(e)}",
                error_code=ErrorCodes.DB_QUERY_ERROR,
                original_exception=e
            )

    def get_claims_by_insurance_company(self) -> List[Dict[str, Any]]:
        """Get claims count grouped by insurance company"""
        try:
            company_counts = self.session.query(
                Claim.insurance_company,
                func.count(Claim.id)
            ).group_by(Claim.insurance_company).all()

            return [{'company': company or 'Unknown', 'count': count} 
                   for company, count in company_counts]
        except Exception as e:
            logger.error(f"Error getting claims by insurance company: {str(e)}")
            raise MondayError(
                f"Error getting claims by insurance company: {str(e)}",
                error_code=ErrorCodes.DB_QUERY_ERROR,
                original_exception=e
            ) 