"""
Feature flag system for controlling feature availability.
Allows for easy enabling/disabling of features without code changes.
"""

import os
import json
import logging
from typing import Dict, Any, Optional, List

logger = logging.getLogger("monday_uploader.feature_flags")

# Default feature flags configuration
DEFAULT_FLAGS = {
    # Core features
    "settlement_calculator_enabled": True,
    "analytics_dashboard_enabled": False,
    "document_ocr_enabled": False,
    "timeline_visualization_enabled": False,
    
    # Client management features
    "client_portal_enabled": False,
    "client_updates_enabled": False,
    "client_onboarding_enabled": False,
    
    # Field operations features
    "map_integration_enabled": False,
    "voice_notes_enabled": False,
    
    # Regulatory features
    "policy_analysis_enabled": False,
    "compliance_checklist_enabled": False,
    "deadline_tracker_enabled": False,
    
    # Technical features
    "cloud_sync_enabled": False,
    "ai_assistant_enabled": False,
    "weather_tracking_enabled": True  # Already implemented in base app
}

class FeatureFlags:
    """
    Feature flag management system.
    Controls which features are enabled/disabled at runtime.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the feature flag system.
        
        Args:
            config_path: Optional path to feature flags JSON file
        """
        self.flags = DEFAULT_FLAGS.copy()
        self.config_path = config_path or os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "config",
            "feature_flags.json"
        )
        
        # Load configuration if exists
        self._load_config()
        
        logger.info(f"Feature flags initialized with {len(self.flags)} flags")
    
    def _load_config(self) -> None:
        """Load configuration from file if it exists."""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                    
                # Update flags with loaded configuration
                self.flags.update(config)
                logger.info(f"Loaded feature flags from {self.config_path}")
            else:
                # Create default configuration file
                self._save_config()
                logger.info(f"Created default feature flags at {self.config_path}")
                
        except Exception as e:
            logger.error(f"Error loading feature flags: {str(e)}")
            # Continue with default flags on error
    
    def _save_config(self) -> None:
        """Save current configuration to file."""
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            
            with open(self.config_path, 'w') as f:
                json.dump(self.flags, f, indent=4)
                
            logger.info(f"Saved feature flags to {self.config_path}")
            
        except Exception as e:
            logger.error(f"Error saving feature flags: {str(e)}")
    
    def is_enabled(self, feature_name: str) -> bool:
        """
        Check if a feature is enabled.
        
        Args:
            feature_name: Name of the feature flag
            
        Returns:
            True if feature is enabled, False otherwise
        """
        # Return False for unknown features
        return self.flags.get(feature_name, False)
    
    def set_enabled(self, feature_name: str, enabled: bool) -> None:
        """
        Enable or disable a feature.
        
        Args:
            feature_name: Name of the feature flag
            enabled: Whether to enable the feature
        """
        if feature_name in self.flags:
            self.flags[feature_name] = enabled
            self._save_config()
            logger.info(f"Feature '{feature_name}' {'enabled' if enabled else 'disabled'}")
        else:
            logger.warning(f"Attempted to set unknown feature flag: {feature_name}")
    
    def get_enabled_features(self) -> List[str]:
        """
        Get a list of all enabled features.
        
        Returns:
            List of enabled feature names
        """
        return [name for name, enabled in self.flags.items() if enabled]
    
    def get_disabled_features(self) -> List[str]:
        """
        Get a list of all disabled features.
        
        Returns:
            List of disabled feature names
        """
        return [name for name, enabled in self.flags.items() if not enabled]
    
    def reset_to_defaults(self) -> None:
        """Reset all feature flags to their default values."""
        self.flags = DEFAULT_FLAGS.copy()
        self._save_config()
        logger.info("Feature flags reset to defaults")

# Global instance for easy import
feature_flags = FeatureFlags()

def is_feature_enabled(feature_name: str) -> bool:
    """
    Utility function to check if a feature is enabled.
    
    Args:
        feature_name: Name of the feature flag
        
    Returns:
        True if feature is enabled, False otherwise
    """
    return feature_flags.is_enabled(feature_name) 