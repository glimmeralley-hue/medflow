"""Configuration management for MedFlow application."""

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional
from .exceptions import ConfigurationError


class Config:
    """Configuration manager for MedFlow application."""
    
    DEFAULT_CONFIG = {
        "database": {
            "path": "~/.medflow/medflow.db",
            "backup_enabled": True,
            "backup_retention": 5,
            "wal_mode": True
        },
        "ui": {
            "theme": "light",
            "window_width": 1400,
            "window_height": 900,
            "remember_window_state": True
        },
        "timer": {
            "default_work_minutes": 25,
            "default_break_minutes": 5,
            "auto_start_breaks": False
        },
        "notifications": {
            "enabled": True,
            "sound_enabled": True,
            "reminder_minutes": 15
        },
        "logging": {
            "level": "INFO",
            "log_to_file": True,
            "log_file": "~/.medflow/medflow.log"
        }
    }
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize configuration manager.
        
        Args:
            config_path: Path to configuration file. If None, uses default location.
        """
        if config_path:
            self.config_path = Path(config_path)
        else:
            self.config_path = Path.home() / ".medflow" / "config.json"
        
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        self._config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file or create default."""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    user_config = json.load(f)
                # Merge with defaults
                return self._merge_configs(self.DEFAULT_CONFIG, user_config)
            except (json.JSONDecodeError, IOError) as e:
                raise ConfigurationError(f"Failed to load config: {e}") from e
        else:
            # Create default config
            self._save_config(self.DEFAULT_CONFIG)
            return self.DEFAULT_CONFIG.copy()
    
    def _merge_configs(self, default: Dict, user: Dict) -> Dict:
        """Recursively merge user config with default config."""
        result = default.copy()
        for key, value in user.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value
        return result
    
    def _save_config(self, config: Dict[str, Any]) -> None:
        """Save configuration to file."""
        try:
            with open(self.config_path, 'w') as f:
                json.dump(config, f, indent=2)
        except IOError as e:
            raise ConfigurationError(f"Failed to save config: {e}") from e
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Get configuration value by dot-separated path.
        
        Args:
            key_path: Dot-separated path (e.g., 'database.path')
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        keys = key_path.split('.')
        value = self._config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    def set(self, key_path: str, value: Any) -> None:
        """
        Set configuration value by dot-separated path.
        
        Args:
            key_path: Dot-separated path (e.g., 'database.path')
            value: Value to set
        """
        keys = key_path.split('.')
        config = self._config
        
        # Navigate to parent of target key
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]
        
        # Set the value
        config[keys[-1]] = value
        
        # Save to file
        self._save_config(self._config)
    
    def save(self) -> None:
        """Save current configuration to file."""
        self._save_config(self._config)
    
    def reset_to_defaults(self) -> None:
        """Reset configuration to default values."""
        self._config = self.DEFAULT_CONFIG.copy()
        self._save_config(self._config)


# Global configuration instance
_config_instance: Optional[Config] = None


def get_config() -> Config:
    """
    Get the global configuration instance.
    
    Returns:
        Config instance
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = Config()
    return _config_instance


def set_config_path(config_path: str) -> None:
    """
    Set a custom configuration path.
    
    Args:
        config_path: Path to configuration file
    """
    global _config_instance
    _config_instance = Config(config_path)
