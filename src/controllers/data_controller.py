print("Loaded DataController from:", __file__)

"""
Data controller for managing Monday.com items.
"""

import logging
import random
import json
import requests
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from models.database import Claim, Client, PublicAdjuster, Employee, Note, BoardData, WeatherFeed, Board, BoardView, init_db
import pandas as pd
import xml.etree.ElementTree as ET
from urllib.parse import urlparse
from sqlalchemy.orm import Session

# Get logger
logger = logging.getLogger("monday_uploader.data_controller")

class DataController:
    """
    Controller for managing Monday.com board items.
    """
    
    def __init__(self, db_path: str = None, parent=None, *args, **kwargs):
        self.engine = init_db(db_path) if db_path else None
        self._mock_items = {}  # Cache for mock items
        self.parent = parent
        
        # Define board mapping
        self.board_map = {
            "Claims": "8903072880",
            "Clients": "8903072881",
            "Public Adjusters": "8903072882",
            "Employees": "8903072883",
            "Notes": "8903072884",
            "Weather Reports": "8903072885",
            "Tasks": "8903072886",
            "Leads": "8903072887",
            "Documents": "8903072888",
            "Damage Estimates": "8903072889"
        }
        
        logger.info("Data controller initialized")
    
    def get_board_name(self, board_id: str) -> Optional[str]:
        """
        Get the name of a board from its ID.
        
        Args:
            board_id: Board ID
            
        Returns:
            Board name or None if not found
        """
        for name, id in self.board_map.items():
            if id == board_id:
                return name
        return None
    
    def load_board_items(self, board_id: str) -> List[Dict[str, Any]]:
        """
        Load items for a board.
        
        Args:
            board_id: Board ID
            
        Returns:
            List of items
        """
        try:
            # Check the board type
            board_name = self.get_board_name(board_id)
            logger.info(f"Loading items for board: {board_name} (ID: {board_id})")
            
            # First check if we have generic board data
            board_data = self.load_board_data_from_database(board_id)
            if board_data:
                return board_data
                
            # For backward compatibility, check specialized models
            # Handle Claims board
            if board_name == "Claims":
                try:
                    # Check if we have data in the database
                    claims = self.load_claims_from_database(board_id)
                    if claims:
                        logger.info(f"Found {len(claims)} claims in database")
                        return claims
                except Exception as e:
                    logger.error(f"Error loading claims: {str(e)}")
                    return []
            
            # Handle Clients board
            elif board_name == "Clients":
                # Check if we have data in the database
                clients = self.load_clients_from_database(board_id)
                if clients:
                    # If clients exist in database, load them
                    return clients
            
            # Handle Public Adjusters board
            elif board_name == "Public Adjusters":
                # Check if we have data in the database
                adjusters = self.load_public_adjusters_from_database(board_id)
                if adjusters:
                    # If public adjusters exist in database, load them
                    return adjusters
            
            # Handle Employees board
            elif board_name == "Employees":
                # Check if we have data in the database
                employees = self.load_employees_from_database(board_id)
                if employees:
                    # If employees exist in database, load them
                    return employees
            
            # Handle Notes board
            elif board_name == "Notes":
                # Check if we have data in the database
                notes = self.load_notes_from_database(board_id)
                if notes:
                    # If notes exist in database, load them
                    return notes
            
            # Handle Weather Feeds board
            elif board_name == "Weather Reports":
                # Check if we have data in the database
                weather_feeds = self.load_weather_feeds_from_database()
                if weather_feeds:
                    # If weather feeds exist in database, load them
                    return weather_feeds
                else:
                    # If no data in database, fetch it
                    return self.fetch_and_store_weather_feeds()
            
            # For other boards or if no data in database, use mock data
            if board_id not in self._mock_items:
                self._mock_items[board_id] = self._generate_mock_items(board_id)
                
            logger.info(f"Loaded {len(self._mock_items[board_id])} items for board {board_id}")
            return self._mock_items[board_id]
        except Exception as e:
            logger.error(f"Error loading board items: {str(e)}")
            return []
    
    def fetch_and_store_weather_feeds(self) -> List[Dict[str, Any]]:
        """
        Fetch weather feeds from various sources and store them in the database.
        
        Returns:
            List of weather feed items
        """
        try:
            # Clear existing weather feeds
            with Session(self.engine) as session:
                session.query(WeatherFeed).delete()
            
            # List to store all fetched feeds
            all_feeds = []
            
            # Fetch NOAA weather feeds
            noaa_feeds = self.fetch_noaa_feeds()
            all_feeds.extend(noaa_feeds)
            
            # Fetch hurricane center feeds
            hurricane_feeds = self.fetch_hurricane_center_feeds()
            all_feeds.extend(hurricane_feeds)
            
            # Fetch weather.gov alerts
            weather_gov_feeds = self.fetch_weather_gov_alerts()
            all_feeds.extend(weather_gov_feeds)
            
            # Commit to database
            session.commit()
            
            # Return as items for display
            return self.load_weather_feeds_from_database()
        except Exception as e:
            logger.error(f"Error fetching weather feeds: {str(e)}")
            with Session(self.engine) as session:
                session.rollback()
            return []
    
    def fetch_noaa_feeds(self) -> List[WeatherFeed]:
        """
        Fetch and parse NOAA RSS feeds.
        
        Returns:
            List of WeatherFeed instances
        """
        try:
            # NOAA RSS feed URLs
            feed_urls = [
                "https://www.weather.gov/xml/current_obs/all_xml.zip",
                "https://www.nhc.noaa.gov/index-at.xml",
                "https://www.weather.gov/alerts/rss.php",
            ]
            
            feeds = []
            
            # For demonstration purposes (in a real app, we'd actually fetch these feeds)
            feed_data = [
                {"title": "Tropical Storm Warning for Southeast Coast", "content": "A tropical storm warning has been issued for coastal areas...", "url": "https://www.nhc.noaa.gov/text/example1.shtml", "pub_date": datetime.now()},
                {"title": "Hurricane Watch - Atlantic Basin", "content": "A hurricane watch is in effect for the following areas...", "url": "https://www.nhc.noaa.gov/text/example2.shtml", "pub_date": datetime.now() - timedelta(hours=2)},
                {"title": "Severe Weather Alert - Thunderstorms", "content": "Severe thunderstorms are expected in the following counties...", "url": "https://www.weather.gov/alerts/example1.php", "pub_date": datetime.now() - timedelta(hours=5)},
                {"title": "Flash Flood Warning", "content": "Flash flooding is occurring or imminent in the following areas...", "url": "https://www.weather.gov/alerts/example2.php", "pub_date": datetime.now() - timedelta(hours=1)},
            ]
            
            with Session(self.engine) as session:
                for item in feed_data:
                    feed = WeatherFeed(
                        source="NOAA",
                        feed_type="Weather Alert",
                        title=item["title"],
                        content=item["content"],
                        url=item["url"],
                        pub_date=item["pub_date"],
                        severity="Warning",
                        location="Southeast United States"
                    )
                    session.add(feed)
                    feeds.append(feed)
            
            return feeds
        except Exception as e:
            logger.error(f"Error fetching NOAA feeds: {str(e)}")
            return []
    
    def fetch_hurricane_center_feeds(self) -> List[WeatherFeed]:
        """
        Fetch and parse National Hurricane Center RSS feeds.
        
        Returns:
            List of WeatherFeed instances
        """
        try:
            # NHC RSS feed URLs
            feed_urls = [
                "https://www.nhc.noaa.gov/index-at.xml",
                "https://www.nhc.noaa.gov/index-ep.xml",
            ]
            
            feeds = []
            
            # For demonstration purposes (in a real app, we'd actually fetch these feeds)
            feed_data = [
                {"title": "Hurricane Maria Advisory #28", "content": "Hurricane Maria continues to move northward away from the coast...", "url": "https://www.nhc.noaa.gov/text/example3.shtml", "pub_date": datetime.now() - timedelta(days=1)},
                {"title": "Tropical Storm Lee Discussion #15", "content": "Tropical Storm Lee is expected to strengthen in the next 48 hours...", "url": "https://www.nhc.noaa.gov/text/example4.shtml", "pub_date": datetime.now() - timedelta(hours=12)},
                {"title": "5-Day Tropical Weather Outlook", "content": "A tropical wave is expected to move off the west coast of Africa...", "url": "https://www.nhc.noaa.gov/text/example5.shtml", "pub_date": datetime.now() - timedelta(hours=6)},
            ]
            
            with Session(self.engine) as session:
                for item in feed_data:
                    feed = WeatherFeed(
                        source="National Hurricane Center",
                        feed_type="Hurricane",
                        title=item["title"],
                        content=item["content"],
                        url=item["url"],
                        pub_date=item["pub_date"],
                        severity="Advisory",
                        location="Atlantic Basin"
                    )
                    session.add(feed)
                    feeds.append(feed)
            
            return feeds
        except Exception as e:
            logger.error(f"Error fetching Hurricane Center feeds: {str(e)}")
            return []
    
    def fetch_weather_gov_alerts(self) -> List[WeatherFeed]:
        """
        Fetch and parse weather.gov alerts.
        
        Returns:
            List of WeatherFeed instances
        """
        try:
            # Weather.gov alert feed URL
            feed_url = "https://www.weather.gov/alerts/rss.php"
            
            feeds = []
            
            # For demonstration purposes (in a real app, we'd actually fetch these feeds)
            feed_data = [
                {"title": "Tornado Warning", "content": "The National Weather Service has issued a tornado warning for...", "url": "https://www.weather.gov/alerts/example6.php", "pub_date": datetime.now(), "severity": "Warning", "location": "Central Oklahoma"},
                {"title": "Winter Storm Watch", "content": "A winter storm watch is in effect for the following areas...", "url": "https://www.weather.gov/alerts/example7.php", "pub_date": datetime.now() - timedelta(hours=3), "severity": "Watch", "location": "Northern New England"},
                {"title": "Coastal Flood Advisory", "content": "A coastal flood advisory remains in effect until...", "url": "https://www.weather.gov/alerts/example8.php", "pub_date": datetime.now() - timedelta(hours=8), "severity": "Advisory", "location": "Gulf Coast"},
            ]
            
            with Session(self.engine) as session:
                for item in feed_data:
                    feed = WeatherFeed(
                        source="Weather.gov",
                        feed_type="Weather Alert",
                        title=item["title"],
                        content=item["content"],
                        url=item["url"],
                        pub_date=item["pub_date"],
                        severity=item["severity"],
                        location=item["location"]
                    )
                    session.add(feed)
                    feeds.append(feed)
            
            return feeds
        except Exception as e:
            logger.error(f"Error fetching Weather.gov alerts: {str(e)}")
            return []
    
    def load_weather_feeds_from_database(self) -> List[Dict[str, Any]]:
        """
        Load weather feeds from the database.
        
        Returns:
            List of weather feed items
        """
        try:
            # Query weather feeds from database
            with Session(self.engine) as session:
                weather_feeds = session.query(WeatherFeed).order_by(WeatherFeed.pub_date.desc()).all()
            
            # Convert to items format
            items = []
            for i, feed in enumerate(weather_feeds):
                # Format the publication date
                pub_date_str = feed.pub_date.strftime("%Y-%m-%d %H:%M") if feed.pub_date else "Unknown"
                
                # Create item for UI display
                item = {
                    "id": f"weather_{i}",
                    "name": feed.title,
                    "source": feed.source,
                    "feed_type": feed.feed_type,
                    "content": feed.content,
                    "url": feed.url,
                    "pub_date": pub_date_str,
                    "location": feed.location,
                    "severity": feed.severity,
                    "created_at": feed.created_at.strftime("%Y-%m-%d")
                }
                
                items.append(item)
            
            # Cache items
            weather_board_id = None
            for name, id in self.board_map.items():
                if name == "Weather Reports":
                    weather_board_id = id
                    break
            
            if weather_board_id:
                self._mock_items[weather_board_id] = items
            
            logger.info(f"Loaded {len(items)} weather feeds from database")
            return items
        except Exception as e:
            logger.error(f"Error loading weather feeds from database: {str(e)}")
            return []
    
    def _generate_mock_items(self, board_id: str) -> List[Dict[str, Any]]:
        """Generate mock items for a board."""
        board_name = self.get_board_name(board_id) or "Unknown"
        
        # Get current date for reference
        now = datetime.now()
        
        # Status values based on board type
        status_options = {
            "Claims": ["New", "In Progress", "Approved", "Denied", "Closed"],
            "Clients": ["Active", "Inactive", "Lead", "Former"],
            "Tasks": ["Not Started", "In Progress", "Completed", "Blocked"],
            "Leads": ["New", "Contacted", "Qualified", "Unqualified"],
            "Documents": ["Draft", "In Review", "Approved", "Published"],
            "Damage Estimates": ["Draft", "Submitted", "Approved", "Denied"],
        }
        
        # Generate 5-15 random items
        items = []
        num_items = random.randint(5, 15)
        
        statuses = status_options.get(board_name, ["New", "In Progress", "Completed"])
        
        for i in range(num_items):
            item = {
                "id": f"{board_id}_{i}",
                "name": f"{board_name} Item {i+1}",
                "status": random.choice(statuses),
                "created_at": (now - timedelta(days=random.randint(0, 30))).strftime("%Y-%m-%d"),
                "owner": f"User {random.randint(1, 5)}"
            }
            
            # Add board-specific fields
            if board_name == "Claims":
                item.update({
                    "claim_number": f"CLM-{random.randint(1000, 9999)}",
                    "client": f"Client {random.randint(1, 10)}",
                    "amount": f"${random.randint(1000, 100000)}"
                })
            elif board_name == "Clients":
                item.update({
                    "company": f"Company {random.randint(1, 10)}",
                    "email": f"client{i}@example.com",
                    "phone": f"555-{random.randint(100, 999)}-{random.randint(1000, 9999)}"
                })
            elif board_name == "Tasks":
                item.update({
                    "due_date": (now + timedelta(days=random.randint(1, 30))).strftime("%Y-%m-%d"),
                    "priority": random.choice(["High", "Medium", "Low"]),
                    "assigned_to": f"User {random.randint(1, 5)}"
                })
            
            items.append(item)
        
        return items
    
    def create_item(self, board_id: str, item_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Create a new item.
        
        Args:
            board_id: Board ID
            item_data: Item data
            
        Returns:
            Created item or None if failed
        """
        try:
            # Ensure we have mock items for this board
            if board_id not in self._mock_items:
                self._mock_items[board_id] = self._generate_mock_items(board_id)
            
            # Generate new item ID
            item_id = f"{board_id}_{len(self._mock_items[board_id])}"
            
            # Create new item
            new_item = {
                "id": item_id,
                "created_at": datetime.now().strftime("%Y-%m-%d"),
                **item_data
            }
            
            # Add to mock items
            self._mock_items[board_id].append(new_item)
            
            logger.info(f"Created new item: {new_item['name']}")
            return new_item
        except Exception as e:
            logger.error(f"Error creating item: {str(e)}")
            return None
    
    def update_item(self, board_id: str, item_id: str, item_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Update an existing item.
        
        Args:
            board_id: Board ID
            item_id: Item ID
            item_data: Updated item data
            
        Returns:
            Updated item or None if failed
        """
        try:
            # Check if we have mock items for this board
            if board_id not in self._mock_items:
                return None
            
            # Find item with matching ID
            for i, item in enumerate(self._mock_items[board_id]):
                if item["id"] == item_id:
                    # Update items in memory
                    self._mock_items[board_id][i] = item_data
                    
                    # Get the board name
                    board_name = self.get_board_name(board_id) or "Unknown"
                    logger.info(f"Updating item {item_id} in board {board_name}")
                    
                    # Extract index from item_id (format should be board_id_index)
                    db_index = None
                    if "_" in item_id:
                        parts = item_id.split("_")
                        if len(parts) > 1:
                            try:
                                db_index = int(parts[-1])  # Get the last part as the index
                                logger.info(f"Extracted index {db_index} from item_id {item_id}")
                            except (ValueError, IndexError):
                                logger.warning(f"Could not extract index from item_id {item_id}")
                    
                    # If we're using the database, update the record
                    try:
                        # Determine which model to use based on board name
                        updated = False
                        
                        # Handle specialized models first
                        if board_name == "Claims":
                            # Get all claims for this board
                            with Session(self.engine) as session:
                                claims = session.query(Claim).filter_by(board_id=board_id).all()
                                logger.info(f"Found {len(claims)} claims for board {board_id}")
                                
                                # Try to find the claim by index
                                if db_index is not None and 0 <= db_index < len(claims):
                                    claim = claims[db_index]
                                    # Update fields
                                    claim.name = item_data.get("name", claim.name)
                                    claim.claim_number = item_data.get("claim_number", claim.claim_number)
                                    claim.person = item_data.get("owner", claim.person)
                                    claim.claim_status = item_data.get("claim_status", claim.claim_status)
                                    claim.client = item_data.get("insured", claim.client)
                                    claim.email = item_data.get("email", claim.email)
                                    claim.status = item_data.get("status", claim.status)
                                    
                                    # Save additional data as JSON
                                    additional_data = {k: v for k, v in item_data.items() 
                                                     if k not in ["id", "created_at", "name", "claim_number", 
                                                                 "owner", "claim_status", "insured", "email", "status"]}
                                    claim.additional_data = json.dumps(additional_data)
                                    
                                    session.commit()
                                    logger.info(f"Updated claim in database: {claim.name}")
                                    updated = True
                                    
                        elif board_name == "Clients":
                            # Get all clients for this board
                            with Session(self.engine) as session:
                                clients = session.query(Client).filter_by(board_id=board_id).all()
                                logger.info(f"Found {len(clients)} clients for board {board_id}")
                                
                                # Try to find the client by index
                                if db_index is not None and 0 <= db_index < len(clients):
                                    client = clients[db_index]
                                    # Update fields
                                    client.name = item_data.get("name", client.name)
                                    client.company = item_data.get("company", client.company)
                                    client.email = item_data.get("email", client.email)
                                    client.phone = item_data.get("phone", client.phone)
                                    client.status = item_data.get("status", client.status)
                                    client.contact_person = item_data.get("owner", client.contact_person)
                                    
                                    # Save additional data as JSON
                                    additional_data = {k: v for k, v in item_data.items() 
                                                     if k not in ["id", "created_at", "name", "company", 
                                                                 "email", "phone", "status", "owner"]}
                                    client.additional_data = json.dumps(additional_data)
                                    
                                    session.commit()
                                    logger.info(f"Updated client in database: {client.name}")
                                    updated = True
                                    
                        elif board_name == "Public Adjusters":
                            # Get all public adjusters for this board
                            with Session(self.engine) as session:
                                adjusters = session.query(PublicAdjuster).filter_by(board_id=board_id).all()
                                logger.info(f"Found {len(adjusters)} public adjusters for board {board_id}")
                                
                                # Try to find the adjuster by index
                                if db_index is not None and 0 <= db_index < len(adjusters):
                                    adjuster = adjusters[db_index]
                                    # Update fields
                                    adjuster.name = item_data.get("name", adjuster.name)
                                    adjuster.company = item_data.get("company", adjuster.company)
                                    adjuster.email = item_data.get("email", adjuster.email)
                                    adjuster.phone = item_data.get("phone", adjuster.phone)
                                    adjuster.status = item_data.get("status", adjuster.status)
                                    adjuster.license = item_data.get("license", adjuster.license)
                                    adjuster.state = item_data.get("state", adjuster.state)
                                    
                                    # Save additional data as JSON
                                    additional_data = {k: v for k, v in item_data.items() 
                                                     if k not in ["id", "created_at", "name", "company", 
                                                                 "email", "phone", "status", "license", "state"]}
                                    adjuster.additional_data = json.dumps(additional_data)
                                    
                                    session.commit()
                                    logger.info(f"Updated public adjuster in database: {adjuster.name}")
                                    updated = True
                                    
                        elif board_name == "Employees":
                            # Get all employees for this board
                            with Session(self.engine) as session:
                                employees = session.query(Employee).filter_by(board_id=board_id).all()
                                logger.info(f"Found {len(employees)} employees for board {board_id}")
                                
                                # Try to find the employee by index
                                if db_index is not None and 0 <= db_index < len(employees):
                                    employee = employees[db_index]
                                    # Update fields
                                    employee.name = item_data.get("name", employee.name)
                                    employee.position = item_data.get("position", employee.position)
                                    employee.email = item_data.get("email", employee.email)
                                    employee.phone = item_data.get("phone", employee.phone)
                                    employee.status = item_data.get("status", employee.status)
                                    employee.department = item_data.get("department", employee.department)
                                    employee.hire_date = item_data.get("hire_date", employee.hire_date)
                                    
                                    # Save additional data as JSON
                                    additional_data = {k: v for k, v in item_data.items() 
                                                     if k not in ["id", "created_at", "name", "position", 
                                                                 "email", "phone", "status", "department", "hire_date"]}
                                    employee.additional_data = json.dumps(additional_data)
                                    
                                    session.commit()
                                    logger.info(f"Updated employee in database: {employee.name}")
                                    updated = True
                                    
                        elif board_name == "Notes":
                            # Get all notes for this board
                            with Session(self.engine) as session:
                                notes = session.query(Note).filter_by(board_id=board_id).all()
                                logger.info(f"Found {len(notes)} notes for board {board_id}")
                                
                                # Try to find the note by index
                                if db_index is not None and 0 <= db_index < len(notes):
                                    note = notes[db_index]
                                    # Update fields
                                    note.title = item_data.get("name", note.title)
                                    note.content = item_data.get("content", note.content)
                                    note.client = item_data.get("client", note.client)
                                    note.status = item_data.get("status", note.status)
                                    note.category = item_data.get("category", note.category)
                                    note.created_by = item_data.get("owner", note.created_by)
                                    note.due_date = item_data.get("due_date", note.due_date)
                                    
                                    # Save additional data as JSON
                                    additional_data = {k: v for k, v in item_data.items() 
                                                     if k not in ["id", "created_at", "name", "content", 
                                                                 "client", "status", "category", "owner", "due_date"]}
                                    note.additional_data = json.dumps(additional_data)
                                    
                                    session.commit()
                                    logger.info(f"Updated note in database: {note.title}")
                                    updated = True
                        
                        # If we couldn't update a specific model, try the generic BoardData model
                        if not updated:
                            # Get all BoardData records for this board
                            with Session(self.engine) as session:
                                board_records = session.query(BoardData).filter_by(board_id=board_id).all()
                                logger.info(f"Found {len(board_records)} BoardData records for board {board_id}")
                                
                                board_data = None
                                
                                # Try to find by index if we extracted it
                                if db_index is not None and 0 <= db_index < len(board_records):
                                    board_data = board_records[db_index]
                                    logger.info(f"Found record by index: {board_data.id}")
                                
                                # If not found by index, try by name
                                if not board_data:
                                    for record in board_records:
                                        if record.name == item_data.get("name", ""):
                                            board_data = record
                                            logger.info(f"Found record by name: {board_data.id}")
                                            break
                                
                                # If still not found, create a new record
                                if not board_data:
                                    logger.info(f"Creating new BoardData record for item {item_data.get('name')}")
                                    board_data = BoardData(
                                        board_id=board_id,
                                        board_name=board_name,
                                        name=item_data.get("name", f"Item {len(board_records)}")
                                    )
                                    session.add(board_data)
                                
                                # Update the record data
                                if board_data:
                                    # Update name
                                    board_data.name = item_data.get("name", board_data.name)
                                    
                                    # Convert item data to JSON string
                                    data_dict = {k: v for k, v in item_data.items() if k not in ["id", "created_at"]}
                                    board_data.data = json.dumps(data_dict)
                                    
                                    # Commit changes
                                    session.commit()
                                    logger.info(f"Updated generic board data in database: {item_data.get('name')}")
                                    
                    except Exception as e:
                        logger.error(f"Error updating item in database: {str(e)}")
                        with Session(self.engine) as session:
                            session.rollback()
                        
                    return item_data
            
            logger.warning(f"Item with ID {item_id} not found in board {board_id}")
            return None
        except Exception as e:
            logger.error(f"Error updating item: {str(e)}")
            return None
    
    def delete_item(self, board_id: str, item_id: str) -> bool:
        """
        Delete an item.
        
        Args:
            board_id: Board ID
            item_id: Item ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Check if we have mock items for this board
            if board_id not in self._mock_items:
                return False
            
            # Find item with matching ID
            for i, item in enumerate(self._mock_items[board_id]):
                if item["id"] == item_id:
                    # Remove item
                    del self._mock_items[board_id][i]
                    logger.info(f"Deleted item: {item_id}")
                    return True
            
            return False
        except Exception as e:
            logger.error(f"Error deleting item: {str(e)}")
            return False
    
    def import_excel_data_for_board(self, board_name: str, data_items: List[List[Any]]) -> bool:
        """
        Import data from an Excel file for any board.
        
        Args:
            board_name: Name of the board
            data_items: List of data rows from the Excel file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Find the board ID
            board_id = None
            for name, id in self.board_map.items():
                if name == board_name:
                    board_id = id
                    break
            
            if not board_id:
                logger.error(f"{board_name} board not found")
                return False
            
            # Get column headers from the first row
            headers = []
            if data_items and len(data_items) > 0:
                headers = [str(h) if h is not None and not pd.isna(h) else f"Column_{i}" for i, h in enumerate(data_items[0])]
            
            # Clear existing data for this board from the database
            with Session(self.engine) as session:
                session.query(BoardData).filter_by(board_id=board_id).delete()
            
            # Convert Excel data to items and store in database
            items = []
            for i, row in enumerate(data_items):
                if i == 0:  # Skip header row
                    continue
                
                # Skip empty rows
                if not row or len(row) < 1:
                    continue
                
                # Extract primary display field (first column)
                # Handle NaN values, which are not allowed
                if pd.isna(row[0]) or row[0] is None or str(row[0]).strip() == "":
                    name = f"{board_name} Item {i}"
                else:
                    name = str(row[0])
                
                # Create a dictionary for all fields
                row_data = {}
                for j, value in enumerate(row):
                    if j < len(headers):
                        header = headers[j]
                        row_data[header] = str(value) if value is not None and not pd.isna(value) else ""
                
                # Create database record
                board_data = BoardData(
                    board_id=board_id,
                    board_name=board_name,
                    name=name,
                    data=json.dumps(row_data)
                )
                session.add(board_data)
                
                # Create item for UI display
                item = {
                    "id": f"{board_id}_{i}",
                    "name": name,
                    "created_at": datetime.now().strftime("%Y-%m-%d")
                }
                
                # Add all fields from the Excel file to the item
                for key, value in row_data.items():
                    item[key] = value
                
                items.append(item)
            
            # Commit changes to database
            session.commit()
            
            # Replace mock items with imported data
            self._mock_items[board_id] = items
            
            logger.info(f"Imported {len(items)} items for {board_name} board")
            return True
            
        except Exception as e:
            logger.error(f"Error importing {board_name} Excel data: {str(e)}")
            # Rollback in case of error
            with Session(self.engine) as session:
                session.rollback()
            return False
    
    def load_board_data_from_database(self, board_id: str) -> List[Dict[str, Any]]:
        """
        Load data from the database for any board.
        
        Args:
            board_id: Board ID
            
        Returns:
            List of board items
        """
        try:
            # Get the board name
            board_name = self.get_board_name(board_id) or "Unknown"
            
            # Query board data from database
            with Session(self.engine) as session:
                board_data_list = session.query(BoardData).filter_by(board_id=board_id).all()
            
            # Convert to items format
            items = []
            for i, bd in enumerate(board_data_list):
                # Create base item
                item = {
                    "id": f"{board_id}_{i}",
                    "name": bd.name,
                    "created_at": bd.created_at.strftime("%Y-%m-%d")
                }
                
                # Add all fields from the JSON data
                if bd.data:
                    try:
                        data = json.loads(bd.data)
                        for key, value in data.items():
                            item[key] = value
                    except:
                        pass
                
                items.append(item)
            
            # Cache items
            self._mock_items[board_id] = items
            
            logger.info(f"Loaded {len(items)} items from database for {board_name} board")
            return items
        except Exception as e:
            logger.error(f"Error loading data from database for board {board_id}: {str(e)}")
            return []
    
    def safe_float(self, val):
        try:
            if val is None or val == 'N/A':
                return 0.0
            return float(val)
        except Exception:
            return 0.0

    def load_claims_from_database(self, board_id: str) -> List[Dict[str, Any]]:
        """
        Load claims from the database for a specific board.
        
        Args:
            board_id: Board ID
            
        Returns:
            List of claim items
        """
        try:
            # Query claims from database
            with Session(self.engine) as session:
                claims = session.query(Claim).filter_by(board_id=board_id).all()
            
            # Convert to items format
            items = []
            for i, claim in enumerate(claims):
                try:
                    # Create item dictionary with all non-date fields first
                    item = {
                        "id": f"{board_id}_{i}",
                        "name": claim.name or "N/A",
                        "status": claim.status or "New",
                        "owner": claim.person or "Unassigned",
                        "claim_number": claim.claim_number or "N/A",
                        "person": claim.person or "N/A",
                        "claim_status": claim.claim_status or "N/A",
                        "client": claim.client or "N/A",
                        "email": claim.email or "N/A",
                        "file_number": claim.file_number or "N/A",
                        "policy_number": claim.policy_number or "N/A",
                        "dup_claim_number": claim.dup_claim_number or "N/A",
                        "loss_type": claim.loss_type or "N/A",
                        "claim_location": claim.claim_location or "N/A",
                        "claim_address": claim.claim_address or "N/A",
                        "insured_amount": self.safe_float(claim.insured_amount),
                        "initial_offer": self.safe_float(claim.initial_offer),
                        "final_settlement": self.safe_float(claim.final_settlement),
                        "pa_fee_percent": self.safe_float(claim.pa_fee_percent),
                        "pa_fee_amount": self.safe_float(claim.pa_fee_amount),
                        "insurance_company": claim.insurance_company or "N/A",
                        "insurance_adjuster": claim.insurance_adjuster or "N/A",
                        "notes": claim.notes or "N/A",
                        "loss_title": claim.loss_title or "N/A",
                        "adjuster_initials": claim.adjuster_initials or "N/A",
                        "claim_street": claim.claim_street or "N/A",
                        "claim_city": claim.claim_city or "N/A",
                        "loss_description": claim.loss_description or "N/A",
                        "insurance_companies": claim.insurance_companies or "N/A",
                        "insurance_representatives": claim.insurance_representatives or "N/A",
                        "treaty_year": claim.treaty_year or "N/A",
                        "treaty_type": claim.treaty_type or "N/A",
                        "loss_prov_state": claim.loss_prov_state or "N/A",
                        "reserve": self.safe_float(claim.reserve)
                    }
                    
                    # Skip all date fields for now
                    date_fields = [
                        'received_on', 'loss_date', 'claim_filed_date', 'last_activity',
                        'deadline_date', 'stat_limitation', 'first_contact', 'next_rpt_due'
                    ]
                    for field in date_fields:
                        item[field] = "N/A"
                    
                    # Add any additional data
                    if claim.additional_data:
                        try:
                            additional_data = json.loads(claim.additional_data)
                            # Skip date fields in additional data
                            for key, value in additional_data.items():
                                if not any(date_term in key.lower() for date_term in ['date', 'due', 'time']):
                                    item[key] = value
                        except json.JSONDecodeError:
                            logger.warning(f"Could not parse additional data for claim {claim.id}")
                    
                    items.append(item)
                except Exception as e:
                    logger.error(f"Error processing claim {i}: {str(e)}")
                    continue
            
            # Cache items
            self._mock_items[board_id] = items
            
            logger.info(f"Loaded {len(items)} claims from database for board {board_id}")
            return items
        except Exception as e:
            logger.error(f"Error loading claims from database: {str(e)}")
            return []
    
    def load_clients_from_database(self, board_id: str) -> List[Dict[str, Any]]:
        """
        Load clients from the database for a specific board.
        
        Args:
            board_id: Board ID
            
        Returns:
            List of client items
        """
        try:
            # Query clients from database
            with Session(self.engine) as session:
                clients = session.query(Client).filter_by(board_id=board_id).all()
            
            # Convert to items format
            items = []
            for i, client in enumerate(clients):
                # Create base item
                item = {
                    "id": f"{board_id}_{i}",
                    "name": client.name,
                    "company": client.company,
                    "email": client.email,
                    "phone": client.phone,
                    "status": client.status,
                    "owner": client.contact_person,
                    "created_at": client.created_at.strftime("%Y-%m-%d"),
                }
                
                # Add additional data if available
                if client.additional_data:
                    try:
                        additional_data = json.loads(client.additional_data)
                        for key, value in additional_data.items():
                            item[key] = value
                    except:
                        pass
                
                items.append(item)
            
            # Cache items
            self._mock_items[board_id] = items
            
            logger.info(f"Loaded {len(items)} clients from database for board {board_id}")
            return items
        except Exception as e:
            logger.error(f"Error loading clients from database: {str(e)}")
            return []
    
    def load_public_adjusters_from_database(self, board_id: str) -> List[Dict[str, Any]]:
        """
        Load public adjusters from the database for a specific board.
        
        Args:
            board_id: Board ID
            
        Returns:
            List of public adjuster items
        """
        try:
            # Query public adjusters from database
            with Session(self.engine) as session:
                adjusters = session.query(PublicAdjuster).filter_by(board_id=board_id).all()
            
            # Convert to items format
            items = []
            for i, adjuster in enumerate(adjusters):
                # Create base item
                item = {
                    "id": f"{board_id}_{i}",
                    "name": adjuster.name,
                    "company": adjuster.company,
                    "email": adjuster.email,
                    "phone": adjuster.phone,
                    "status": adjuster.status,
                    "license": adjuster.license,
                    "state": adjuster.state,
                    "created_at": adjuster.created_at.strftime("%Y-%m-%d"),
                }
                
                # Add additional data if available
                if adjuster.additional_data:
                    try:
                        additional_data = json.loads(adjuster.additional_data)
                        for key, value in additional_data.items():
                            item[key] = value
                    except:
                        pass
                
                items.append(item)
            
            # Cache items
            self._mock_items[board_id] = items
            
            logger.info(f"Loaded {len(items)} public adjusters from database for board {board_id}")
            return items
        except Exception as e:
            logger.error(f"Error loading public adjusters from database: {str(e)}")
            return []
    
    def load_employees_from_database(self, board_id: str) -> List[Dict[str, Any]]:
        """
        Load employees from the database for a specific board.
        
        Args:
            board_id: Board ID
            
        Returns:
            List of employee items
        """
        try:
            # Query employees from database
            with Session(self.engine) as session:
                employees = session.query(Employee).filter_by(board_id=board_id).all()
            
            # Convert to items format
            items = []
            for i, employee in enumerate(employees):
                # Create base item
                item = {
                    "id": f"{board_id}_{i}",
                    "name": employee.name,
                    "position": employee.position,
                    "email": employee.email,
                    "phone": employee.phone,
                    "status": employee.status,
                    "department": employee.department,
                    "hire_date": employee.hire_date,
                    "created_at": employee.created_at.strftime("%Y-%m-%d"),
                }
                
                # Add additional data if available
                if employee.additional_data:
                    try:
                        additional_data = json.loads(employee.additional_data)
                        for key, value in additional_data.items():
                            item[key] = value
                    except:
                        pass
                
                items.append(item)
            
            # Cache items
            self._mock_items[board_id] = items
            
            logger.info(f"Loaded {len(items)} employees from database for board {board_id}")
            return items
        except Exception as e:
            logger.error(f"Error loading employees from database: {str(e)}")
            return []
    
    def load_notes_from_database(self, board_id: str) -> List[Dict[str, Any]]:
        """
        Load notes from the database for a specific board.
        
        Args:
            board_id: Board ID
            
        Returns:
            List of note items
        """
        try:
            # Query notes from database
            with Session(self.engine) as session:
                notes = session.query(Note).filter_by(board_id=board_id).all()
            
            # Convert to items format
            items = []
            for i, note in enumerate(notes):
                # Create base item
                item = {
                    "id": f"{board_id}_{i}",
                    "name": note.title,  # Use title as the name for display
                    "content": note.content,
                    "client": note.client,
                    "status": note.status,
                    "category": note.category,
                    "owner": note.created_by,
                    "due_date": note.due_date,
                    "created_at": note.created_at.strftime("%Y-%m-%d"),
                }
                
                # Add additional data if available
                if note.additional_data:
                    try:
                        additional_data = json.loads(note.additional_data)
                        for key, value in additional_data.items():
                            item[key] = value
                    except:
                        pass
                
                items.append(item)
            
            # Cache items
            self._mock_items[board_id] = items
            
            logger.info(f"Loaded {len(items)} notes from database for board {board_id}")
            return items
        except Exception as e:
            logger.error(f"Error loading notes from database: {str(e)}")
            return []
    
    def get_board_views(self, board_id: str) -> list[BoardView]:
        """Get all views for a board."""
        try:
            with Session(self.engine) as session:
                return session.query(BoardView).filter(BoardView.board_id == board_id).all()
        except Exception as e:
            logging.error(f"Error getting board views: {str(e)}")
            return []
            
    def create_board_view(self, board_id: str) -> BoardView:
        """Create a new board view."""
        try:
            with Session(self.engine) as session:
                # Get board name for the default view name
                board_name = self.get_board_name(board_id) or "Unknown"
                view = BoardView(
                    board_id=board_id,
                    name=f"Default {board_name} View",  # Add default name
                    is_default=False,
                    column_order=None,
                    hidden_columns=None,
                    column_widths=None
                )
                session.add(view)
                session.commit()
                session.refresh(view)
                return view
        except Exception as e:
            logging.error(f"Error creating board view: {str(e)}")
            raise
            
    def save_board_view(self, view: BoardView):
        """Save a board view."""
        try:
            with Session(self.engine) as session:
                session.merge(view)
                session.commit()
        except Exception as e:
            logging.error(f"Error saving board view: {str(e)}")
            raise
            
    def delete_board_view(self, view_id: int):
        """Delete a board view."""
        try:
            with Session(self.engine) as session:
                view = session.query(BoardView).filter(BoardView.id == view_id).first()
                if view:
                    session.delete(view)
                    session.commit()
        except Exception as e:
            logging.error(f"Error deleting board view: {str(e)}")
            raise 