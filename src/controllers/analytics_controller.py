#!/usr/bin/env python3
"""
Analytics Controller
Handles data processing and statistics generation for the Claims Analytics Dashboard
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import pandas as pd
from sqlalchemy import func, and_, desc

from models.database import Claims, CalendarEvent, BoardView
from utils.error_handling import handle_error

logger = logging.getLogger(__name__)

class AnalyticsController:
    def __init__(self, session):
        self.session = session

    @handle_error
    def get_claims_statistics(self, time_period: str = '30d') -> Dict[str, Any]:
        """
        Get overall claims statistics for the dashboard
        time_period: '7d', '30d', '90d', '1y', 'all'
        """
        try:
            # Calculate date range
            end_date = datetime.now()
            if time_period == '7d':
                start_date = end_date - timedelta(days=7)
            elif time_period == '30d':
                start_date = end_date - timedelta(days=30)
            elif time_period == '90d':
                start_date = end_date - timedelta(days=90)
            elif time_period == '1y':
                start_date = end_date - timedelta(days=365)
            else:  # 'all'
                start_date = datetime.min

            # Get total claims count
            total_claims = self.session.query(func.count(Claims.id)).scalar()
            
            # Get claims in date range
            recent_claims = self.session.query(func.count(Claims.id))\
                .filter(Claims.created_at >= start_date)\
                .scalar()

            # Get average settlement time
            avg_settlement_time = self.session.query(
                func.avg(Claims.settlement_date - Claims.created_at)
            ).filter(Claims.settlement_date.isnot(None)).scalar()

            # Get success rate (claims with settlements)
            success_rate = self.session.query(
                func.count(Claims.id).filter(Claims.settlement_date.isnot(None)) * 100.0 / 
                func.count(Claims.id)
            ).scalar()

            return {
                'total_claims': total_claims,
                'recent_claims': recent_claims,
                'avg_settlement_time': avg_settlement_time,
                'success_rate': success_rate
            }
        except Exception as e:
            logger.error(f"Error getting claims statistics: {str(e)}")
            raise

    @handle_error
    def get_claims_by_status(self) -> List[Dict[str, Any]]:
        """Get claims count grouped by status"""
        try:
            status_counts = self.session.query(
                Claims.status,
                func.count(Claims.id)
            ).group_by(Claims.status).all()

            return [{'status': status, 'count': count} 
                   for status, count in status_counts]
        except Exception as e:
            logger.error(f"Error getting claims by status: {str(e)}")
            raise

    @handle_error
    def get_monthly_claims_trend(self) -> List[Dict[str, Any]]:
        """Get monthly claims trend for the last 12 months"""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=365)

            monthly_claims = self.session.query(
                func.strftime('%Y-%m', Claims.created_at).label('month'),
                func.count(Claims.id).label('count')
            ).filter(
                Claims.created_at >= start_date
            ).group_by('month').order_by('month').all()

            return [{'month': month, 'count': count} 
                   for month, count in monthly_claims]
        except Exception as e:
            logger.error(f"Error getting monthly claims trend: {str(e)}")
            raise

    @handle_error
    def get_settlement_amounts(self) -> Dict[str, float]:
        """Get settlement amount statistics"""
        try:
            result = self.session.query(
                func.min(Claims.settlement_amount).label('min'),
                func.max(Claims.settlement_amount).label('max'),
                func.avg(Claims.settlement_amount).label('avg')
            ).filter(
                Claims.settlement_amount.isnot(None)
            ).first()

            return {
                'min': result.min,
                'max': result.max,
                'avg': result.avg
            }
        except Exception as e:
            logger.error(f"Error getting settlement amounts: {str(e)}")
            raise

    @handle_error
    def get_claims_by_insurance_company(self) -> List[Dict[str, Any]]:
        """Get claims count grouped by insurance company"""
        try:
            company_counts = self.session.query(
                Claims.insurance_company,
                func.count(Claims.id)
            ).group_by(Claims.insurance_company).all()

            return [{'company': company, 'count': count} 
                   for company, count in company_counts]
        except Exception as e:
            logger.error(f"Error getting claims by insurance company: {str(e)}")
            raise 