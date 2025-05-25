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
    QComboBox, QFrame, QGridLayout, QSizePolicy,
    QTableWidget, QTableWidgetItem
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QColor

# Initialize PLOTLY_AVAILABLE at module level
PLOTLY_AVAILABLE = False

try:
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    from PySide6.QtWebEngineWidgets import QWebEngineView
    PLOTLY_AVAILABLE = True
except ImportError:
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
            try:
                chart = QWebEngineView()
                chart.setMinimumHeight(300)
            except Exception as e:
                logger.warning(f"Failed to create QWebEngineView: {str(e)}")
                chart = self._create_table_widget()
        else:
            chart = self._create_table_widget()
        
        layout.addWidget(chart)
        container.chart = chart
        return container

    def _create_table_widget(self) -> QTableWidget:
        """Create a table widget for basic visualization"""
        table = QTableWidget()
        table.setMinimumHeight(300)
        table.setColumnCount(2)
        table.setHorizontalHeaderLabels(["Category", "Value"])
        table.horizontalHeader().setStretchLastSection(True)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.setAlternatingRowColors(True)
        return table

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
            if isinstance(avg_time, float):
                self.stats_cards['Avg Settlement Time'].value_label.setText(f"{int(avg_time)} days")
            else:
                days = avg_time.days
                self.stats_cards['Avg Settlement Time'].value_label.setText(f"{days} days")
        else:
            self.stats_cards['Avg Settlement Time'].value_label.setText("N/A")

    def update_status_chart(self):
        """Update claims by status chart"""
        try:
            status_data = self.analytics_controller.get_claims_by_status()
            
            if PLOTLY_AVAILABLE and isinstance(self.status_chart.chart, QWebEngineView):
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
                
                self.status_chart.chart.setHtml(fig.to_html(include_plotlyjs='cdn'))
            else:
                # Update table widget
                table = self.status_chart.chart
                table.setRowCount(len(status_data))
                for i, data in enumerate(status_data):
                    table.setItem(i, 0, QTableWidgetItem(str(data['status'])))
                    table.setItem(i, 1, QTableWidgetItem(str(data['count'])))
                table.resizeColumnsToContents()

        except Exception as e:
            logger.error(f"Error updating status chart: {str(e)}")

    def update_trend_chart(self):
        """Update monthly claims trend chart"""
        try:
            trend_data = self.analytics_controller.get_monthly_claims_trend()
            
            if PLOTLY_AVAILABLE and isinstance(self.trend_chart.chart, QWebEngineView):
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
                
                self.trend_chart.chart.setHtml(fig.to_html(include_plotlyjs='cdn'))
            else:
                # Update table widget
                table = self.trend_chart.chart
                table.setRowCount(len(trend_data))
                for i, data in enumerate(trend_data):
                    table.setItem(i, 0, QTableWidgetItem(str(data['month'])))
                    table.setItem(i, 1, QTableWidgetItem(str(data['count'])))
                table.resizeColumnsToContents()

        except Exception as e:
            logger.error(f"Error updating trend chart: {str(e)}")

    def update_amounts_chart(self):
        """Update settlement amounts chart"""
        try:
            amounts_data = self.analytics_controller.get_settlement_amounts()
            
            if PLOTLY_AVAILABLE and isinstance(self.amounts_chart.chart, QWebEngineView):
                fig = go.Figure(data=[
                    go.Bar(
                        x=['Min', 'Max', 'Average'],
                        y=[amounts_data['min'], amounts_data['max'], amounts_data['avg']]
                    )
                ])
                
                fig.update_layout(
                    title="Settlement Amounts",
                    xaxis_title="Metric",
                    yaxis_title="Amount",
                    height=300
                )
                
                self.amounts_chart.chart.setHtml(fig.to_html(include_plotlyjs='cdn'))
            else:
                # Update table widget
                table = self.amounts_chart.chart
                table.setRowCount(3)
                metrics = ['Min', 'Max', 'Average']
                values = [amounts_data['min'], amounts_data['max'], amounts_data['avg']]
                for i, (metric, value) in enumerate(zip(metrics, values)):
                    table.setItem(i, 0, QTableWidgetItem(metric))
                    table.setItem(i, 1, QTableWidgetItem(f"${value:,.2f}"))
                table.resizeColumnsToContents()

        except Exception as e:
            logger.error(f"Error updating amounts chart: {str(e)}")

    def update_companies_chart(self):
        """Update claims by insurance company chart"""
        try:
            company_data = self.analytics_controller.get_claims_by_insurance_company()
            
            if PLOTLY_AVAILABLE and isinstance(self.companies_chart.chart, QWebEngineView):
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
                
                self.companies_chart.chart.setHtml(fig.to_html(include_plotlyjs='cdn'))
            else:
                # Update table widget
                table = self.companies_chart.chart
                table.setRowCount(len(company_data))
                for i, data in enumerate(company_data):
                    table.setItem(i, 0, QTableWidgetItem(str(data['company'])))
                    table.setItem(i, 1, QTableWidgetItem(str(data['count'])))
                table.resizeColumnsToContents()

        except Exception as e:
            logger.error(f"Error updating companies chart: {str(e)}")

    def on_time_period_changed(self, period: str):
        """Handle time period selection change"""
        self.refresh_data() 