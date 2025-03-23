import os
import json
from src.shortcuts.loader import load_default_shortcuts

class ShortcutManager:
    def __init__(self, config):
        print("Initializing ShortcutManager")
        self.config = config
        self.shortcuts_db = {}
        self.load_shortcuts()
        print(f"Loaded {len(self.shortcuts_db)} applications with shortcuts")
        for app in self.shortcuts_db:
            print(f" - {app}: {len(self.shortcuts_db[app])} shortcuts")
        
    def load_shortcuts(self):
        """Load shortcuts from files"""
        # Load from user config
        user_shortcuts = self.config.get_shortcuts()
        if user_shortcuts:
            self.shortcuts_db.update(user_shortcuts)
        else:
            # Load default shortcuts
            self.shortcuts_db = load_default_shortcuts()
            self.save_shortcuts()
            
    def save_shortcuts(self):
        """Save shortcuts to config"""
        self.config.save_shortcuts(self.shortcuts_db)
        
    def get_shortcuts_for_app(self, app_name):
        """Get shortcuts for a specific application"""
        if not app_name:
            return []
            
        shortcuts = self.shortcuts_db.get(app_name, [])
        print(f"Found {len(shortcuts)} shortcuts for {app_name}")
        return shortcuts