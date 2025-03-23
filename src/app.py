import tkinter as tk
from src.ui.main_window import MainWindow
from src.shortcuts.manager import ShortcutManager
from src.utils.config import ConfigManager

class ShortcutHelperApp:
    def __init__(self):
        print("Initializing ShortcutHelperApp")
        # Initialize configuration
        self.config = ConfigManager()
        
        # Initialize shortcut database
        self.shortcuts = ShortcutManager(self.config)
        
        # Create main window
        self.root = tk.Tk()
        self.window = MainWindow(self.root, self.shortcuts, self.config)
        
    def run(self):
        """Run the application"""
        self.window.setup()
        self.root.mainloop()