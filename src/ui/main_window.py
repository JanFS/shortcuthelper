import tkinter as tk
import keyboard
import win32gui
import win32process
import psutil
from tkinter import ttk
from src.ui.styles import apply_theme

class MainWindow:
    def __init__(self, root, shortcut_manager, config):
        self.root = root
        self.shortcuts = shortcut_manager
        self.config = config
        
    def setup(self):
        print("Setting up main window...")
        """Set up the main window"""
        # Apply theme
        apply_theme(self.root, self.config.get_theme())
        
        # Window properties
        self.root.title("Keyboard Shortcuts")
        # ... rest of window setup
        
        # Create UI components
        self.create_search_bar()
        self.create_shortcut_tree()
        # ... other UI components

        # Register hotkey
        keyboard.add_hotkey('ctrl+shift+space', self.toggle_overlay)
        
        # Get initial shortcuts
        self.update_shortcuts()
        
    def create_search_bar(self):
        # ... search bar implementation
        pass

    def create_shortcut_tree(self):
        print("Creating shortcut tree...")
        
        # Create a frame for the tree
        frame = ttk.Frame(self.root)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create a Treeview for displaying shortcuts
        self.tree = ttk.Treeview(
            frame, 
            columns=("shortcut", "description"), 
            show="tree headings"
        )
        
        # Configure the Treeview
        self.tree.heading("#0", text="Action")
        self.tree.column("#0", width=200)
        self.tree.heading("shortcut", text="Shortcut")
        self.tree.column("shortcut", width=150)
        self.tree.heading("description", text="Description")
        self.tree.column("description", width=250)
        
        # Create scrollbar
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack Treeview and scrollbar
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        print("Shortcut tree created")

    def update_shortcuts(self):
        # Get active window process
        process_name = self.get_active_window_process()
        if process_name:
            self.display_shortcuts(process_name)

    def get_active_window_process(self):
        """Get the process name of the active window"""
        try:
            # Get handle of active window
            hwnd = win32gui.GetForegroundWindow()
            
            # Get process ID from window handle
            _, process_id = win32process.GetWindowThreadProcessId(hwnd)
            
            # Get process name from process ID
            process = psutil.Process(process_id)
            print(f"Active process: {process.name()}")
            return process.name()
        except Exception as e:
            print(f"Error getting active window process: {e}")
            return None
        
    def toggle_overlay(self):
        print("Toggle overlay called")
        """Toggle the visibility of the shortcut overlay"""
        if self.root.state() == 'normal':
            self.hide_overlay()
        else:
            self.show_overlay()
            
    def toggle_overlay(self):
        """Toggle the visibility of the shortcut overlay"""
        if self.root.state() == 'normal':
            self.hide_overlay()
        else:
            self.show_overlay()
            
    def show_overlay(self):
        """Show the shortcut overlay"""
        # Get active window process
        process_name = self.get_active_window_process()
        
        # Update shortcuts display
        if process_name:
            self.display_shortcuts(process_name)
        
        # Show the window
        self.root.deiconify()
        self.root.attributes('-alpha', 0.9)
        self.root.lift()
        
    def hide_overlay(self):
        """Hide the overlay"""
        self.root.withdraw()

    def display_shortcuts(self, process_name):
        """Display shortcuts for the active application"""
        print(f"Displaying shortcuts for: {process_name}")
        
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        shortcuts = self.shortcuts.get_shortcuts_for_app(process_name)
        print(f"Found {len(shortcuts)} shortcuts for {process_name}")
        
        if not shortcuts:
            self.tree.insert("", "end", text=f"No shortcuts for {process_name}", values=("", ""))
            return
        
        # Group shortcuts by category
        categories = {}
        for shortcut in shortcuts:
            category = shortcut.get("category", "General")
            if category not in categories:
                categories[category] = []
            categories[category].append(shortcut)
        
        # Add categories and shortcuts to the tree
        for category, cat_shortcuts in categories.items():
            print(f"Adding category: {category} with {len(cat_shortcuts)} shortcuts")
            category_id = self.tree.insert("", "end", text=category, values=("", ""))
            
            for shortcut in cat_shortcuts:
                self.tree.insert(
                    category_id, 
                    "end", 
                    text=shortcut["description"], 
                    values=(shortcut["keys"], shortcut.get("detail", ""))
                )