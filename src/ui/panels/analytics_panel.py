#!/usr/bin/env python3
"""
Analytics Dashboard Panel
Displays claims statistics and analytics in a visual format
"""

import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QComboBox, QFrame, QGridLayout, QSizePolicy
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QColor

try:
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    from PySide6.QtWebEngineWidgets import QWebEngineView
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False
    logging.warning("Plotly not available, using basic charts")

logger = logging.getLogger(__name__)

class AnalyticsPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.analytics_controller = None
        self.setup_ui()
        
        # Set up refresh timer (every 5 minutes)
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.refresh_data)
        self.refresh_timer.start(300000)  # 300000 ms = 5 minutes

    def setup_ui(self):
        """Set up the user interface"""
        layout = QVBoxLayout(self)
        
        # Time period selector
        time_selector = QHBoxLayout()
        time_label = QLabel("Time Period:")
        self.time_combo = QComboBox()
        self.time_combo.addItems(['Last 7 Days', 'Last 30 Days', 'Last 90 Days', 'Last Year', 'All Time'])
        self.time_combo.currentTextChanged.connect(self.on_time_period_changed)
        time_selector.addWidget(time_label)
        time_selector.addWidget(self.time_combo)
        time_selector.addStretch()
        layout.addLayout(time_selector)

        # Statistics cards
        stats_layout = QHBoxLayout()
        self.stats_cards = {}
        for stat in ['Total Claims', 'Recent Claims', 'Success Rate', 'Avg Settlement Time']:
            card = self.create_stat_card(stat)
            stats_layout.addWidget(card)
            self.stats_cards[stat] = card
        layout.addLayout(stats_layout)

        # Charts
        charts_layout = QGridLayout()
        
        # Claims by Status
        self.status_chart = self.create_chart_widget("Claims by Status")
        charts_layout.addWidget(self.status_chart, 0, 0)
        
        # Monthly Trend
        self.trend_chart = self.create_chart_widget("Monthly Claims Trend")
        charts_layout.addWidget(self.trend_chart, 0, 1)
        
        # Settlement Amounts
        self.amounts_chart = self.create_chart_widget("Settlement Amounts")
        charts_layout.addWidget(self.amounts_chart, 1, 0)
        
        # Insurance Companies
        self.companies_chart = self.create_chart_widget("Claims by Insurance Company")
        charts_layout.addWidget(self.companies_chart, 1, 1)
        
        layout.addLayout(charts_layout)

    def create_stat_card(self, title: str) -> QFrame:
        """Create a statistics card widget"""
        card = QFrame()
        card.setFrameStyle(QFrame.StyledPanel)
        card.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 8px;
                border: 1px solid #ddd;
            }
        """)
        
        layout = QVBoxLayout(card)
        
        # Title
        title_label = QLabel(title)
        title_label.setStyleSheet("color: #666; font-size: 14px;")
        layout.addWidget(title_label)
        
        # Value
        value_label = QLabel("--")
        value_label.setStyleSheet("color: #333; font-size: 24px; font-weight: bold;")
        layout.addWidget(value_label)
        
        card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        card.setMinimumHeight(100)
        
        # Store reference to value label
        card.value_label = value_label
        
        return card

    def create_chart_widget(self, title: str) -> QWidget:
        """Create a chart widget with title"""
        container = QWidget()
        layout = QVBoxLayout(container)
        
        # Title
        title_label = QLabel(title)
        title_label.setStyleSheet("color: #333; font-size: 16px; font-weight: bold;")
        layout.addWidget(title_label)
        
        # Chart area
        if PLOTLY_AVAILABLE:
            chart = QWebEngineView()
            chart.setMinimumHeight(300)
        else:
            chart = QLabel("Chart visualization not available")
            chart.setStyleSheet("color: #666;")
            chart.setAlignment(Qt.AlignCenter)
            chart.setMinimumHeight(300)
        
        layout.addWidget(chart)
        container.chart = chart
        return container

    def set_analytics_controller(self, controller):
        """Set the analytics controller and refresh data"""
        self.analytics_controller = controller
        self.refresh_data()

    def refresh_data(self):
        """Refresh all analytics data"""
        if not self.analytics_controller:
            return

        try:
            # Get time period
            time_period = self.time_combo.currentText().lower().replace(' ', '')
            time_map = {
                'last7days': '7d',
                'last30days': '30d',
                'last90days': '90d',
                'lastyear': '1y',
                'alltime': 'all'
            }
            period = time_map.get(time_period, '30d')

            # Get statistics
            stats = self.analytics_controller.get_claims_statistics(period)
            self.update_stat_cards(stats)

            # Get and update charts
            self.update_status_chart()
            self.update_trend_chart()
            self.update_amounts_chart()
            self.update_companies_chart()

        except Exception as e:
            logger.error(f"Error refreshing analytics data: {str(e)}")

    def update_stat_cards(self, stats: Dict[str, Any]):
        """Update statistics cards with new data"""
        self.stats_cards['Total Claims'].value_label.setText(str(stats['total_claims']))
        self.stats_cards['Recent Claims'].value_label.setText(str(stats['recent_claims']))
        self.stats_cards['Success Rate'].value_label.setText(f"{stats['success_rate']:.1f}%")
        
        # Format average settlement time
        avg_time = stats['avg_settlement_time']
        if avg_time:
            days = avg_time.days
            self.stats_cards['Avg Settlement Time'].value_label.setText(f"{days} days")
        else:
            self.stats_cards['Avg Settlement Time'].value_label.setText("N/A")

    def update_status_chart(self):
        """Update claims by status chart"""
        if not PLOTLY_AVAILABLE:
            return

        try:
            status_data = self.analytics_controller.get_claims_by_status()
            
            fig = go.Figure(data=[
                go.Pie(
                    labels=[d['status'] for d in status_data],
                    values=[d['count'] for d in status_data],
                    hole=.3
                )
            ])
            
            fig.update_layout(
                title="Claims by Status",
                showlegend=True,
                height=300
            )
            
            self.status_chart.setHtml(fig.to_html(include_plotlyjs='cdn'))

        except Exception as e:
            logger.error(f"Error updating status chart: {str(e)}")

    def update_trend_chart(self):
        """Update monthly claims trend chart"""
        if not PLOTLY_AVAILABLE:
            return

        try:
            trend_data = self.analytics_controller.get_monthly_claims_trend()
            
            fig = go.Figure(data=[
                go.Bar(
                    x=[d['month'] for d in trend_data],
                    y=[d['count'] for d in trend_data]
                )
            ])
            
            fig.update_layout(
                title="Monthly Claims Trend",
                xaxis_title="Month",
                yaxis_title="Number of Claims",
                height=300
            )
            
            self.trend_chart.setHtml(fig.to_html(include_plotlyjs='cdn'))

        except Exception as e:
            logger.error(f"Error updating trend chart: {str(e)}")

    def update_amounts_chart(self):
        """Update settlement amounts chart"""
        if not PLOTLY_AVAILABLE:
            return

        try:
            amounts = self.analytics_controller.get_settlement_amounts()
            
            fig = go.Figure(data=[
                go.Bar(
                    x=['Min', 'Max', 'Average'],
                    y=[amounts['min'], amounts['max'], amounts['avg']],
                    text=[f"${v:,.2f}" for v in [amounts['min'], amounts['max'], amounts['avg']]],
                    textposition='auto',
                )
            ])
            
            fig.update_layout(
                title="Settlement Amounts",
                yaxis_title="Amount ($)",
                height=300
            )
            
            self.amounts_chart.setHtml(fig.to_html(include_plotlyjs='cdn'))

        except Exception as e:
            logger.error(f"Error updating amounts chart: {str(e)}")

    def update_companies_chart(self):
        """Update claims by insurance company chart"""
        if not PLOTLY_AVAILABLE:
            return

        try:
            company_data = self.analytics_controller.get_claims_by_insurance_company()
            
            fig = go.Figure(data=[
                go.Bar(
                    x=[d['company'] for d in company_data],
                    y=[d['count'] for d in company_data]
                )
            ])
            
            fig.update_layout(
                title="Claims by Insurance Company",
                xaxis_title="Company",
                yaxis_title="Number of Claims",
                height=300
            )
            
            self.companies_chart.setHtml(fig.to_html(include_plotlyjs='cdn'))

        except Exception as e:
            logger.error(f"Error updating companies chart: {str(e)}")

    def on_time_period_changed(self, period: str):
        """Handle time period selection change"""
        self.refresh_data() 