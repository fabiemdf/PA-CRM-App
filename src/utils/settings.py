"""
Settings utilities for the Monday Uploader application.
"""

import os
import json
import logging
from typing import Dict, Any, Optional

# Get logger
logger = logging.getLogger("monday_uploader.settings")

# Constants
SETTINGS_FILE = "settings.json"
DEFAULT_SETTINGS = {
    "api_key": "",
    "auto_sync": False,
    "sync_interval": 300,  # seconds
    "log_level": "INFO",
    "name": "",
    "company": "",
    "position": "",
    "theme": "system",  # system, light, dark
    "default_board": "",
    "locale": "en_US",
    "date_format": "yyyy-MM-dd",
    "time_format": "HH:mm",
    "max_items_per_page": 100,
    "show_news_feed": True,
    "show_map": True
}

def get_settings_path() -> str:
    """
    Get the path to the settings file.
    
    Returns:
        Path to the settings file
    """
    # Get the application directory
    app_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    return os.path.join(app_dir, SETTINGS_FILE)

def load_settings() -> Dict[str, Any]:
    """
    Load settings from the settings file.
    
    Returns:
        Dictionary containing the settings
    """
    settings_path = get_settings_path()
    
    # Check if settings file exists
    if not os.path.exists(settings_path):
        logger.info(f"Settings file not found at: {settings_path}. Using default settings.")
        return DEFAULT_SETTINGS.copy()
    
    try:
        # Load settings from file
        with open(settings_path, "r") as f:
            settings = json.load(f)
            
        # Merge with default settings to ensure all keys are present
        merged_settings = DEFAULT_SETTINGS.copy()
        merged_settings.update(settings)
        
        logger.info(f"Settings loaded from: {settings_path}")
        return merged_settings
        
    except Exception as e:
        logger.error(f"Failed to load settings: {str(e)}")
        return DEFAULT_SETTINGS.copy()

def save_settings(settings: Dict[str, Any]) -> bool:
    """
    Save settings to the settings file.
    
    Args:
        settings: Dictionary containing the settings
        
    Returns:
        True if successful, False otherwise
    """
    settings_path = get_settings_path()
    
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(settings_path), exist_ok=True)
        
        # Save settings to file
        with open(settings_path, "w") as f:
            json.dump(settings, f, indent=4)
            
        logger.info(f"Settings saved to: {settings_path}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to save settings: {str(e)}")
        return False

def get_setting(key: str, default: Any = None) -> Any:
    """
    Get a specific setting value.
    
    Args:
        key: Setting key
        default: Default value if the key is not found
        
    Returns:
        Setting value or default
    """
    settings = load_settings()
    return settings.get(key, default)

def set_setting(key: str, value: Any) -> bool:
    """
    Set a specific setting value.
    
    Args:
        key: Setting key
        value: Setting value
        
    Returns:
        True if successful, False otherwise
    """
    settings = load_settings()
    settings[key] = value
    return save_settings(settings)

def reset_settings() -> bool:
    """
    Reset settings to default.
    
    Returns:
        True if successful, False otherwise
    """
    return save_settings(DEFAULT_SETTINGS.copy()) 