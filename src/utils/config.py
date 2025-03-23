import os
import json

class ConfigManager:
    def __init__(self):
        self.config_dir = os.path.join(os.path.expanduser("~"), ".shortcut_helper")
        self.config_file = os.path.join(self.config_dir, "config.json")
        self.shortcuts_file = os.path.join(self.config_dir, "shortcuts.json")
        
        # Create config directory if it doesn't exist
        if not os.path.exists(self.config_dir):
            os.makedirs(self.config_dir)
            
        # Load or create configuration
        self.config = self.load_config()
        
    def load_config(self):
        """Load configuration from file"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except Exception:
                return self.get_default_config()
        else:
            # Create default config
            config = self.get_default_config()
            self.save_config(config)
            return config
            
    def get_default_config(self):
        """Get default configuration"""
        return {
            "hotkey": "ctrl+shift+space",
            "theme": "dark",
            "window_width": 600,
            "window_height": 500,
            "show_window_frame": True,
            "opacity": 0.95
        }
        
    def save_config(self, config=None):
        """Save configuration to file"""
        if config is None:
            config = self.config
            
        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=2)
            
    def get_shortcuts(self):
        """Load shortcuts from file"""
        if os.path.exists(self.shortcuts_file):
            try:
                with open(self.shortcuts_file, 'r') as f:
                    return json.load(f)
            except Exception:
                return None
        else:
            return None
            
    def save_shortcuts(self, shortcuts):
        """Save shortcuts to file"""
        with open(self.shortcuts_file, 'w') as f:
            json.dump(shortcuts, f, indent=2)
            
    def get_theme(self):
        """Get current theme"""
        return self.config.get("theme", "dark")