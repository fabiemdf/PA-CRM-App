"""
Calendar controller for managing calendar events.
"""

import logging
import json
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy import and_, or_
from models.database import CalendarEvent, EventReminder

# Get logger
logger = logging.getLogger("monday_uploader.calendar_controller")

class CalendarController:
    """
    Controller for managing calendar events.
    """
    
    def __init__(self, session):
        """
        Initialize the calendar controller.
        
        Args:
            session: SQLAlchemy session
        """
        self.session = session
        
        logger.info("Calendar controller initialized")
    
    def get_events(self, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """
        Get events for a date range.
        
        Args:
            start_date: Start date
            end_date: End date
            
        Returns:
            List of events
        """
        try:
            # Query events from database
            events = self.session.query(CalendarEvent).filter(
                or_(
                    # Event starts within the range
                    and_(
                        CalendarEvent.start_time >= start_date,
                        CalendarEvent.start_time <= end_date
                    ),
                    # Event ends within the range
                    and_(
                        CalendarEvent.end_time >= start_date,
                        CalendarEvent.end_time <= end_date
                    ),
                    # Event spans the range
                    and_(
                        CalendarEvent.start_time <= start_date,
                        CalendarEvent.end_time >= end_date
                    )
                )
            ).all()
            
            # Convert to dict format
            result = []
            for event in events:
                event_dict = {
                    "id": event.id,
                    "title": event.title,
                    "description": event.description,
                    "start_time": event.start_time,
                    "end_time": event.end_time,
                    "is_all_day": event.is_all_day,
                    "color": event.color,
                    "location": event.location,
                    "event_type": event.event_type,
                    "monday_item_id": event.monday_item_id,
                    "reminders": [
                        {
                            "id": r.id,
                            "reminder_time": r.reminder_time,
                            "is_sent": r.is_sent,
                            "sent_at": r.sent_at
                        } for r in event.reminders
                    ]
                }
                result.append(event_dict)
            
            logger.info(f"Retrieved {len(result)} events for range {start_date} to {end_date}")
            return result
        except Exception as e:
            logger.error(f"Error getting events: {str(e)}")
            return []
    
    def get_event(self, event_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a single event by ID.
        
        Args:
            event_id: Event ID
            
        Returns:
            Event dict or None if not found
        """
        try:
            event = self.session.query(CalendarEvent).filter_by(id=event_id).first()
            if not event:
                return None
            
            event_dict = {
                "id": event.id,
                "title": event.title,
                "description": event.description,
                "start_time": event.start_time,
                "end_time": event.end_time,
                "is_all_day": event.is_all_day,
                "color": event.color,
                "location": event.location,
                "event_type": event.event_type,
                "monday_item_id": event.monday_item_id,
                "reminders": [
                    {
                        "id": r.id,
                        "reminder_time": r.reminder_time,
                        "is_sent": r.is_sent,
                        "sent_at": r.sent_at
                    } for r in event.reminders
                ]
            }
            
            return event_dict
        except Exception as e:
            logger.error(f"Error getting event {event_id}: {str(e)}")
            return None
    
    def create_event(self, event_data: Dict[str, Any]) -> Optional[str]:
        """
        Create a new calendar event.
        
        Args:
            event_data: Event data dict
            
        Returns:
            ID of created event or None if failed
        """
        try:
            # Create new event
            event = CalendarEvent(
                title=event_data.get("title", "Untitled Event"),
                description=event_data.get("description"),
                start_time=event_data.get("start_time"),
                end_time=event_data.get("end_time"),
                is_all_day=event_data.get("is_all_day", False),
                color=event_data.get("color", "#3788d8"),
                location=event_data.get("location"),
                event_type=event_data.get("event_type"),
                monday_item_id=event_data.get("monday_item_id")
            )
            
            # Add to session
            self.session.add(event)
            
            # Add reminders if specified
            reminders = event_data.get("reminders", [])
            for reminder_data in reminders:
                reminder = EventReminder(
                    event=event,
                    reminder_time=reminder_data.get("reminder_time"),
                    is_sent=False
                )
                self.session.add(reminder)
            
            # Commit to database
            self.session.commit()
            
            logger.info(f"Created event: {event.title} (ID: {event.id})")
            return event.id
        except Exception as e:
            logger.error(f"Error creating event: {str(e)}")
            self.session.rollback()
            return None
    
    def update_event(self, event_id: str, event_data: Dict[str, Any]) -> bool:
        """
        Update an existing calendar event.
        
        Args:
            event_id: Event ID
            event_data: Event data dict
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get event
            event = self.session.query(CalendarEvent).filter_by(id=event_id).first()
            if not event:
                logger.warning(f"Event not found: {event_id}")
                return False
            
            # Update fields
            if "title" in event_data:
                event.title = event_data["title"]
            if "description" in event_data:
                event.description = event_data["description"]
            if "start_time" in event_data:
                event.start_time = event_data["start_time"]
            if "end_time" in event_data:
                event.end_time = event_data["end_time"]
            if "is_all_day" in event_data:
                event.is_all_day = event_data["is_all_day"]
            if "color" in event_data:
                event.color = event_data["color"]
            if "location" in event_data:
                event.location = event_data["location"]
            if "event_type" in event_data:
                event.event_type = event_data["event_type"]
            if "monday_item_id" in event_data:
                event.monday_item_id = event_data["monday_item_id"]
            
            # Update reminders if specified
            if "reminders" in event_data:
                # Remove existing reminders
                for reminder in event.reminders:
                    self.session.delete(reminder)
                
                # Add new reminders
                for reminder_data in event_data["reminders"]:
                    reminder = EventReminder(
                        event=event,
                        reminder_time=reminder_data.get("reminder_time"),
                        is_sent=reminder_data.get("is_sent", False),
                        sent_at=reminder_data.get("sent_at")
                    )
                    self.session.add(reminder)
            
            # Commit to database
            self.session.commit()
            
            logger.info(f"Updated event: {event.title} (ID: {event.id})")
            return True
        except Exception as e:
            logger.error(f"Error updating event: {str(e)}")
            self.session.rollback()
            return False
    
    def delete_event(self, event_id: str) -> bool:
        """
        Delete a calendar event.
        
        Args:
            event_id: Event ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get event
            event = self.session.query(CalendarEvent).filter_by(id=event_id).first()
            if not event:
                logger.warning(f"Event not found: {event_id}")
                return False
            
            # Delete event (cascade will delete reminders)
            self.session.delete(event)
            
            # Commit to database
            self.session.commit()
            
            logger.info(f"Deleted event: {event_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting event: {str(e)}")
            self.session.rollback()
            return False
            
    def get_events_by_day(self, day: datetime) -> List[Dict[str, Any]]:
        """
        Get events for a specific day.
        
        Args:
            day: The day to get events for
            
        Returns:
            List of events
        """
        try:
            # Set up start and end of day
            start_of_day = datetime(day.year, day.month, day.day, 0, 0, 0)
            end_of_day = datetime(day.year, day.month, day.day, 23, 59, 59)
            
            # Query events from database
            events = self.session.query(CalendarEvent).filter(
                or_(
                    # Event starts on this day
                    and_(
                        CalendarEvent.start_time >= start_of_day,
                        CalendarEvent.start_time <= end_of_day
                    ),
                    # Event ends on this day
                    and_(
                        CalendarEvent.end_time >= start_of_day,
                        CalendarEvent.end_time <= end_of_day
                    ),
                    # Event spans this day
                    and_(
                        CalendarEvent.start_time <= start_of_day,
                        CalendarEvent.end_time >= end_of_day
                    )
                )
            ).all()
            
            # Convert to dict format
            result = []
            for event in events:
                event_dict = {
                    "id": event.id,
                    "title": event.title,
                    "description": event.description,
                    "start_time": event.start_time,
                    "end_time": event.end_time,
                    "is_all_day": event.is_all_day,
                    "color": event.color,
                    "location": event.location,
                    "event_type": event.event_type,
                    "monday_item_id": event.monday_item_id
                }
                result.append(event_dict)
            
            logger.info(f"Retrieved {len(result)} events for {day.strftime('%Y-%m-%d')}")
            return result
        except Exception as e:
            logger.error(f"Error getting events for day {day}: {str(e)}")
            return []
            
    def import_events_from_items(self, items: List[Dict[str, Any]], board_name: str) -> int:
        """
        Import events from board items that have due dates.
        
        Args:
            items: List of items
            board_name: Name of the board
            
        Returns:
            Number of events created
        """
        try:
            count = 0
            for item in items:
                # Check if item has a due date
                if "due_date" in item and item["due_date"]:
                    try:
                        # Parse due date (expecting format like "2023-05-15")
                        due_date = datetime.strptime(item["due_date"], "%Y-%m-%d")
                        
                        # Create event
                        event_data = {
                            "title": f"{board_name}: {item['name']}",
                            "description": f"Due date for {item['name']} in {board_name} board",
                            "start_time": due_date,
                            "end_time": due_date + timedelta(hours=1),
                            "is_all_day": True,
                            "color": "#ff9900",  # Orange for due dates
                            "event_type": f"{board_name} Due Date",
                            "monday_item_id": item.get("id")
                        }
                        
                        # Create the event
                        if self.create_event(event_data):
                            count += 1
                    except (ValueError, TypeError) as e:
                        logger.warning(f"Invalid date format in item {item['name']}: {e}")
            
            logger.info(f"Created {count} events from {board_name} items")
            return count
        except Exception as e:
            logger.error(f"Error importing events from items: {str(e)}")
            return 0 