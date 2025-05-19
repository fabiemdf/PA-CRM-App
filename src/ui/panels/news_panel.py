"""
News panel for displaying latest updates and weather feeds.
"""

import logging
from typing import Dict, List, Any, Optional
import json

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTextBrowser,
    QPushButton, QToolBar, QComboBox, QHBoxLayout, 
    QTabWidget, QScrollArea
)
from PySide6.QtCore import Qt, QSize, QUrl
from PySide6.QtGui import QColor, QAction, QIcon

# Get logger
logger = logging.getLogger("monday_uploader.news_panel")

class NewsPanel(QWidget):
    """
    Panel for displaying latest updates and weather feeds.
    """
    
    def __init__(self, parent=None, data_controller=None):
        """
        Initialize the news panel.
        
        Args:
            parent: Parent widget
            data_controller: DataController instance
        """
        super().__init__(parent)
        
        self.data_controller = data_controller
        self.weather_feeds = []
        
        # Setup UI
        self._setup_ui()
        
        logger.info("News panel initialized")
    
    def _setup_ui(self):
        """Setup the user interface."""
        # Create layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Create toolbar
        toolbar = QToolBar()
        toolbar.setIconSize(QSize(16, 16))
        
        # Add toolbar actions
        refresh_btn = QPushButton("Refresh Feeds")
        refresh_btn.clicked.connect(self.refresh)
        toolbar.addWidget(refresh_btn)
        
        # Add filter options
        toolbar.addSeparator()
        toolbar.addWidget(QLabel("Filter by:"))
        
        self.feed_type_filter = QComboBox()
        self.feed_type_filter.addItem("All Feeds")
        self.feed_type_filter.addItem("Hurricane")
        self.feed_type_filter.addItem("Weather Alert")
        self.feed_type_filter.addItem("Storm")
        self.feed_type_filter.currentIndexChanged.connect(self.apply_filters)
        toolbar.addWidget(self.feed_type_filter)
        
        toolbar.addSeparator()
        toolbar.addWidget(QLabel("Source:"))
        
        self.source_filter = QComboBox()
        self.source_filter.addItem("All Sources")
        self.source_filter.addItem("NOAA")
        self.source_filter.addItem("National Hurricane Center")
        self.source_filter.addItem("Weather.gov")
        self.source_filter.currentIndexChanged.connect(self.apply_filters)
        toolbar.addWidget(self.source_filter)
        
        layout.addWidget(toolbar)
        
        # Create tabbed interface
        self.tab_widget = QTabWidget()
        
        # Weather Feed tab
        self.weather_browser = QTextBrowser()
        self.weather_browser.setOpenExternalLinks(True)
        self.tab_widget.addTab(self.weather_browser, "Weather Alerts")
        
        # Application News tab
        self.news_browser = QTextBrowser()
        self.news_browser.setOpenExternalLinks(True)
        self.tab_widget.addTab(self.news_browser, "Application Updates")
        
        layout.addWidget(self.tab_widget)
        
        # Set initial content
        self._load_weather_feeds()
        self._load_news()
        
        self.setLayout(layout)
    
    def refresh(self):
        """Refresh the panel's content."""
        # If data controller is available, fetch new weather feeds
        if self.data_controller:
            try:
                self.weather_feeds = self.data_controller.fetch_and_store_weather_feeds()
                self._display_weather_feeds(self.weather_feeds)
            except Exception as e:
                logger.error(f"Error refreshing weather feeds: {str(e)}")
        
        self._load_news()
    
    def _load_weather_feeds(self):
        """Load weather feeds from the data controller."""
        if self.data_controller:
            try:
                # Get the Weather Reports board ID
                weather_board_id = None
                for board_name, board_id in self.data_controller.board_controller.board_map.items():
                    if board_name == "Weather Reports":
                        weather_board_id = board_id
                        break
                
                if weather_board_id:
                    # Load weather feed items
                    self.weather_feeds = self.data_controller.load_board_items(weather_board_id)
                    self._display_weather_feeds(self.weather_feeds)
            except Exception as e:
                logger.error(f"Error loading weather feeds: {str(e)}")
    
    def _display_weather_feeds(self, feeds: List[Dict[str, Any]]):
        """
        Display weather feeds in the browser.
        
        Args:
            feeds: List of weather feed items
        """
        try:
            # Create HTML content
            html = """
            <html>
            <head>
                <style>
                    body { font-family: Arial, sans-serif; margin: 10px; }
                    .feed-item { 
                        border: 1px solid #ddd; 
                        padding: 10px; 
                        margin-bottom: 15px; 
                        border-radius: 5px;
                    }
                    .feed-title { 
                        font-size: 16px; 
                        font-weight: bold; 
                        margin-bottom: 8px;
                    }
                    .feed-meta { 
                        font-size: 12px; 
                        color: #666; 
                        margin-bottom: 8px;
                    }
                    .feed-content { 
                        font-size: 14px; 
                        margin-bottom: 10px;
                    }
                    .feed-link { 
                        font-size: 12px;
                    }
                    .warning { background-color: #FFEEEE; border-left: 4px solid #FF0000; }
                    .advisory { background-color: #FFFFEE; border-left: 4px solid #FFCC00; }
                    .watch { background-color: #EEEEFF; border-left: 4px solid #0000FF; }
                    .hurricane { background-color: #FFEEEE; border-left: 4px solid #FF0000; }
                </style>
            </head>
            <body>
                <h2>Weather Alerts and Reports</h2>
            """
            
            if not feeds:
                html += "<p>No weather feeds available. Click 'Refresh Feeds' to fetch the latest updates.</p>"
            else:
                for feed in feeds:
                    # Determine CSS class based on severity
                    css_class = ""
                    if "severity" in feed:
                        severity = feed["severity"].lower() if feed["severity"] else ""
                        if "warning" in severity:
                            css_class = "warning"
                        elif "advisory" in severity:
                            css_class = "advisory"
                        elif "watch" in severity:
                            css_class = "watch"
                    
                    if "feed_type" in feed and "hurricane" in feed["feed_type"].lower():
                        css_class = "hurricane"
                    
                    # Create feed item HTML
                    html += f'<div class="feed-item {css_class}">'
                    html += f'<div class="feed-title">{feed["name"]}</div>'
                    
                    # Add metadata
                    meta_parts = []
                    if "source" in feed:
                        meta_parts.append(f"Source: {feed['source']}")
                    if "severity" in feed:
                        meta_parts.append(f"Severity: {feed['severity']}")
                    if "location" in feed:
                        meta_parts.append(f"Location: {feed['location']}")
                    if "pub_date" in feed:
                        meta_parts.append(f"Date: {feed['pub_date']}")
                    
                    html += f'<div class="feed-meta">{" | ".join(meta_parts)}</div>'
                    
                    # Add content
                    if "content" in feed and feed["content"]:
                        html += f'<div class="feed-content">{feed["content"]}</div>'
                    
                    # Add link
                    if "url" in feed and feed["url"]:
                        html += f'<div class="feed-link"><a href="{feed["url"]}" target="_blank">View Full Report</a></div>'
                    
                    html += '</div>'
            
            html += """
            </body>
            </html>
            """
            
            self.weather_browser.setHtml(html)
            logger.info(f"Displayed {len(feeds)} weather feeds")
        except Exception as e:
            logger.error(f"Error displaying weather feeds: {str(e)}")
    
    def apply_filters(self):
        """Apply filters to the weather feeds."""
        try:
            # Get filter values
            feed_type = self.feed_type_filter.currentText()
            source = self.source_filter.currentText()
            
            # Filter feeds
            filtered_feeds = self.weather_feeds
            
            if feed_type != "All Feeds":
                filtered_feeds = [f for f in filtered_feeds if f.get("feed_type") == feed_type]
            
            if source != "All Sources":
                filtered_feeds = [f for f in filtered_feeds if f.get("source") == source]
            
            # Display filtered feeds
            self._display_weather_feeds(filtered_feeds)
            
            logger.info(f"Applied filters: type={feed_type}, source={source}")
        except Exception as e:
            logger.error(f"Error applying filters: {str(e)}")
    
    def _load_news(self):
        """Load application news updates."""
        try:
            # In a real implementation, this would load news from a source
            news_html = """
            <html>
            <head>
                <style>
                    body { font-family: Arial, sans-serif; margin: 10px; }
                    h2 { color: #333; }
                    .item { margin-bottom: 15px; }
                    .title { font-weight: bold; color: #0066cc; }
                    .date { color: #666; font-size: 12px; }
                </style>
            </head>
            <body>
                <h2>Monday Uploader Updates</h2>
                
                <div class="item">
                    <div class="title">New Feature: Weather Reports Feed</div>
                    <div class="date">Today</div>
                    <p>Added NOAA, hurricane, storm and weather reports integration. Stay updated with the latest weather alerts.</p>
                </div>
                
                <div class="item">
                    <div class="title">Improved Excel Import</div>
                    <div class="date">Yesterday</div>
                    <p>Enhanced Excel file import capabilities with better error handling and data validation.</p>
                </div>
                
                <div class="item">
                    <div class="title">Bug Fix: Item Creation</div>
                    <div class="date">Last week</div>
                    <p>Fixed an issue with item creation that was causing occasional errors.</p>
                </div>
                
                <div class="item">
                    <div class="title">UI Improvements</div>
                    <div class="date">Last month</div>
                    <p>Updated the user interface for better usability and a more modern look.</p>
                </div>
            </body>
            </html>
            """
            
            self.news_browser.setHtml(news_html)
            logger.info("Application news loaded")
        except Exception as e:
            logger.error(f"Error loading application news: {str(e)}") 