import sys
import json
import os
from pathlib import Path
import psutil
import keyboard
import ctypes
from ctypes import wintypes
import win32gui
import win32process

try:
    import tkinter as tk
    from tkinter import ttk
except ImportError:
    print("Tkinter not found. Please install it.")
    sys.exit(1)

# Constants
SHORTCUT_TRIGGER = 'ctrl+shift+space'  # Hotkey to toggle the overlay
FADE_STEP = 0.05  # How much to decrease opacity each step
FADE_DELAY = 50  # Milliseconds between each fade step
# No auto-fade timer anymore
CONFIG_FILENAME = 'shortcuts.json'

class ShortcutHelper:
    def __init__(self):
        # Create the main window but don't show it yet
        self.root = tk.Tk()
        self.root.withdraw()  # Hide the main window
        
        # Set window properties
        self.root.title("Keyboard Shortcuts")
        self.root.attributes('-topmost', True)  # Always on top
        self.root.overrideredirect(False)  # Show window decorations for now (can be toggled)
        self.root.attributes('-alpha', 0.95)  # Slightly transparent
        
        # Calculate window position (top-right corner with padding)
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        window_width = 600  # Wider to accommodate descriptions
        window_height = 500
        x_position = screen_width - window_width - 20
        y_position = 100
        self.root.geometry(f"{window_width}x{window_height}+{x_position}+{y_position}")
        
        # Set modern dark theme colors
        bg_color = '#1E1E1E'  # Dark background
        accent_color = '#0078D7'  # Blue accent (Windows-like)
        
        # Set background color
        self.root.configure(bg=bg_color)
        
        # Add keyboard navigation
        self.root.bind('<Escape>', lambda e: self.hide_overlay())
        self.root.bind('<F1>', lambda e: self.show_help())
        
        # Store theme colors for consistent use
        self.colors = {
            'bg': bg_color,
            'fg': 'white',
            'accent': accent_color,
            'highlight': '#3D7ABB',
            'dark_accent': '#005A9E',
            'light_text': '#CCCCCC'
        }
        
        # Initialize UI elements
        self.create_ui()
        
        # Load shortcut database
        self.shortcuts_db = self.load_shortcuts()
        
        # Register global hotkey
        keyboard.add_hotkey(SHORTCUT_TRIGGER, self.show_overlay)
        
        # Create system tray icon
        self.create_tray_icon()
        
    def create_ui(self):
        """Create the UI elements for the overlay"""
        # Main frame with padding
        main_frame = tk.Frame(self.root, bg=self.colors['bg'])
        main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # Add a search frame at the top
        search_frame = tk.Frame(main_frame, bg=self.colors['bg'])
        search_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Search label
        search_label = tk.Label(
            search_frame,
            text="Search:",
            font=("Segoe UI", 10),
            fg=self.colors['fg'],
            bg=self.colors['bg']
        )
        search_label.pack(side=tk.LEFT, padx=(0, 5))
        
        # Search entry
        self.search_var = tk.StringVar()
        self.search_entry = tk.Entry(
            search_frame,
            textvariable=self.search_var,
            font=("Segoe UI", 10),
            bg="#2D2D2D",
            fg=self.colors['fg'],
            insertbackground=self.colors['fg'],  # Cursor color
            relief=tk.FLAT,
            highlightthickness=1,
            highlightcolor=self.colors['accent'],
            highlightbackground="#555555"
        )
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=3)
        
        # Bind search functionality
        self.search_var.trace_add("write", self.filter_shortcuts)
        self.search_entry.bind("<Escape>", lambda e: self.clear_search())
        
        # Add keyboard shortcut for search focus
        self.root.bind("<Control-f>", lambda e: self.search_entry.focus_set())
        

        # App name subtitle (will be updated dynamically)
        self.app_name_label = tk.Label(
            title_frame, 
            text="", 
            font=("Segoe UI", 10, "italic"),
            fg=self.colors['light_text'], 
            bg=self.colors['bg']
        )
        self.app_name_label.pack()
        
        # Create frame for shortcuts with tabs
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        # Create the shortcuts tab
        self.shortcuts_frame = ttk.Frame(notebook)
        notebook.add(self.shortcuts_frame, text="Shortcuts")
        
        # Create a help tab
        self.help_frame = ttk.Frame(notebook)
        notebook.add(self.help_frame, text="Help")
        
        # Configure keyboard navigation for tabs
        notebook.bind("<Control-Tab>", lambda e: notebook.select(notebook.index("current") + 1 
                                                  if notebook.index("current") < notebook.index("end") - 1 
                                                  else 0))
        notebook.bind("<Control-Shift-Tab>", lambda e: notebook.select(notebook.index("current") - 1 
                                                       if notebook.index("current") > 0 
                                                       else notebook.index("end") - 1))
        
        # Create a Treeview for displaying shortcuts
        self.tree = ttk.Treeview(
            self.shortcuts_frame, 
            columns=("shortcut", "description"), 
            show="tree headings", 
            height=15,
            selectmode="browse"  # Allow single selection for keyboard navigation
        )
        
        # Configure the Treeview
        self.tree.heading("#0", text="Action")
        self.tree.column("#0", width=200, anchor="w")
        self.tree.heading("shortcut", text="Shortcut")
        self.tree.column("shortcut", width=150, anchor="center")
        self.tree.heading("description", text="Description")
        self.tree.column("description", width=250)
        
        # Create scrollbar
        yscrollbar = ttk.Scrollbar(self.shortcuts_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=yscrollbar.set)
        
        # Pack Treeview and scrollbar
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        yscrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Add keyboard navigation for the tree
        self.tree.bind("<Up>", lambda e: self.tree.focus(self.tree.prev(self.tree.focus())) 
                      if self.tree.prev(self.tree.focus()) else None)
        self.tree.bind("<Down>", lambda e: self.tree.focus(self.tree.next(self.tree.focus())) 
                        if self.tree.next(self.tree.focus()) else None)
        self.tree.bind("<Left>", lambda e: self.tree.item(self.tree.focus(), open=False))
        self.tree.bind("<Right>", lambda e: self.tree.item(self.tree.focus(), open=True))
        
        # Configure style for dark theme
        style = ttk.Style()
        
        # Try to use a theme that supports customization
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass  # Use default theme if "clam" is not available
        
        # Configure Treeview colors
        style.configure(
            "Treeview", 
            background="#2D2D2D", 
            foreground="white", 
            fieldbackground="#2D2D2D",
            rowheight=25  # Taller rows for better readability
        )
        style.configure(
            "Treeview.Heading", 
            background="#3E3E3E", 
            foreground="white",
            font=("Segoe UI", 9, "bold")
        )
        style.map(
            "Treeview", 
            background=[('selected', self.colors['highlight'])],
            foreground=[('selected', 'white')]
        )
        
        # Add help content
        help_content = tk.Text(
            self.help_frame,
            wrap=tk.WORD,
            bg="#2D2D2D",
            fg="white",
            font=("Segoe UI", 10),
            padx=10,
            pady=10,
            relief=tk.FLAT
        )
        help_content.pack(fill=tk.BOTH, expand=True)
        
        # Help text
        help_text = """
Keyboard Shortcut Helper

This tool helps you learn keyboard shortcuts for different applications.

KEYBOARD NAVIGATION:
- Press Ctrl+Shift+Space to show/hide this window
- Press Ctrl+F to search for shortcuts
- Use Up/Down arrows to navigate the list
- Use Left/Right arrows to collapse/expand categories
- Press Escape to hide the window
- Press Ctrl+Tab / Ctrl+Shift+Tab to switch tabs

SEARCH TIPS:
- Search by action (e.g., "save")
- Search by key (e.g., "ctrl+s")
- Search by category (e.g., "editing")

This tool will help you become more productive by reducing dependency on the mouse.
        """
        help_content.insert(tk.END, help_text)
        help_content.config(state=tk.DISABLED)  # Make it read-only
        
        # Bottom buttons frame
        buttons_frame = tk.Frame(main_frame, bg=self.colors['bg'])
        buttons_frame.pack(fill=tk.X, pady=(10, 0))
        
        # Button style
        style.configure(
            "Accent.TButton", 
            background=self.colors['accent'],
            foreground="white",
            padding=6
        )
        style.map(
            "Accent.TButton",
            background=[('active', self.colors['dark_accent'])],
            relief=[('pressed', 'sunken')]
        )
    
    def load_shortcuts(self):
        """Load shortcuts from JSON file or create default database if not exists"""
        # Determine config directory
        config_dir = os.path.join(os.path.expanduser("~"), ".shortcut_helper")
        
        # Create directory if it doesn't exist
        if not os.path.exists(config_dir):
            os.makedirs(config_dir)
        
        config_path = os.path.join(config_dir, CONFIG_FILENAME)
        
        # If config file doesn't exist, create default
        if not os.path.exists(config_path):
                            # Default shortcuts
            default_shortcuts = {
                # VSCode shortcuts
                "Code.exe": [
                    {"description": "Show Command Palette", "keys": "Ctrl+Shift+P", "category": "General", "detail": "Access all commands in VS Code"},
                    {"description": "Quick Open, Go to File", "keys": "Ctrl+P", "category": "General", "detail": "Search and open files in the current project"},
                    {"description": "New File", "keys": "Ctrl+N", "category": "General", "detail": "Create a new file in the editor"},
                    {"description": "Save", "keys": "Ctrl+S", "category": "General", "detail": "Save the current file"},
                    {"description": "Save As", "keys": "Ctrl+Shift+S", "category": "General", "detail": "Save the current file with a new name"},
                    {"description": "Close Editor", "keys": "Ctrl+W", "category": "General", "detail": "Close the current editor tab"},
                    {"description": "Zen Mode", "keys": "Ctrl+K Z", "category": "General", "detail": "Toggle distraction-free full-screen mode"},
                    {"description": "Cut Line", "keys": "Ctrl+X", "category": "Editing", "detail": "Cut the current line or selection"},
                    {"description": "Copy Line", "keys": "Ctrl+C", "category": "Editing", "detail": "Copy the current line or selection"},
                    {"description": "Move Line Up/Down", "keys": "Alt+↑/↓", "category": "Editing", "detail": "Move current line or selection up or down"},
                    {"description": "Copy Line Up/Down", "keys": "Shift+Alt+↑/↓", "category": "Editing", "detail": "Duplicate current line or selection above or below"},
                    {"description": "Delete Line", "keys": "Ctrl+Shift+K", "category": "Editing", "detail": "Delete the current line completely"},
                    {"description": "Insert Line Below", "keys": "Ctrl+Enter", "category": "Editing", "detail": "Insert a new line below the current line"},
                    {"description": "Insert Line Above", "keys": "Ctrl+Shift+Enter", "category": "Editing", "detail": "Insert a new line above the current line"},
                    {"description": "Select Current Line", "keys": "Ctrl+L", "category": "Editing", "detail": "Select the entire current line"},
                    {"description": "Find", "keys": "Ctrl+F", "category": "Search", "detail": "Find text in the current file"},
                    {"description": "Replace", "keys": "Ctrl+H", "category": "Search", "detail": "Find and replace text in the current file"},
                    {"description": "Find Next", "keys": "F3", "category": "Search", "detail": "Jump to the next match"},
                    {"description": "Find Previous", "keys": "Shift+F3", "category": "Search", "detail": "Jump to the previous match"},
                    {"description": "Toggle Comment", "keys": "Ctrl+/", "category": "Coding", "detail": "Comment or uncomment the current line or selection"},
                    {"description": "Trigger Suggestion", "keys": "Ctrl+Space", "category": "Coding", "detail": "Show code completion suggestions"},
                    {"description": "Format Document", "keys": "Shift+Alt+F", "category": "Coding", "detail": "Format the entire document according to language rules"},
                    {"description": "Go to Definition", "keys": "F12", "category": "Coding", "detail": "Jump to the definition of the symbol under cursor"},
                    {"description": "Peek Definition", "keys": "Alt+F12", "category": "Coding", "detail": "Show definition inline without leaving current position"},
                    {"description": "Open Terminal", "keys": "Ctrl+`", "category": "Terminal", "detail": "Show or hide the integrated terminal"},
                    {"description": "Split Editor", "keys": "Ctrl+\\", "category": "Window", "detail": "Split the editor to show files side by side"},
                    {"description": "Navigate Editors", "keys": "Ctrl+Tab", "category": "Window", "detail": "Cycle through open editors"},
                    {"description": "Focus Explorer", "keys": "Ctrl+Shift+E", "category": "Navigation", "detail": "Focus the file explorer view"},
                    {"description": "Focus Search", "keys": "Ctrl+Shift+F", "category": "Navigation", "detail": "Focus the search view"},
                    {"description": "Focus Source Control", "keys": "Ctrl+Shift+G", "category": "Navigation", "detail": "Focus the git/source control view"}
                ],
                
                # Chrome shortcuts
                "chrome.exe": [
                    {"description": "New Tab", "keys": "Ctrl+T", "category": "Tabs", "detail": "Open a new browser tab"},
                    {"description": "Close Tab", "keys": "Ctrl+W", "category": "Tabs", "detail": "Close the current browser tab"},
                    {"description": "Reopen Closed Tab", "keys": "Ctrl+Shift+T", "category": "Tabs", "detail": "Restore the most recently closed tab"},
                    {"description": "Next Tab", "keys": "Ctrl+Tab", "category": "Tabs", "detail": "Switch to the next tab to the right"},
                    {"description": "Previous Tab", "keys": "Ctrl+Shift+Tab", "category": "Tabs", "detail": "Switch to the previous tab to the left"},
                    {"description": "Select Specific Tab", "keys": "Ctrl+1..8", "category": "Tabs", "detail": "Switch to a specific tab by number"},
                    {"description": "Last Tab", "keys": "Ctrl+9", "category": "Tabs", "detail": "Switch to the last tab"},
                    {"description": "Address Bar", "keys": "Ctrl+L", "category": "Navigation", "detail": "Focus and select the URL in the address bar"},
                    {"description": "Refresh", "keys": "F5 / Ctrl+R", "category": "Navigation", "detail": "Reload the current page"},
                    {"description": "Hard Refresh", "keys": "Ctrl+F5 / Ctrl+Shift+R", "category": "Navigation", "detail": "Reload the page ignoring cached content"},
                    {"description": "Back", "keys": "Alt+Left", "category": "Navigation", "detail": "Go back to the previous page in history"},
                    {"description": "Forward", "keys": "Alt+Right", "category": "Navigation", "detail": "Go forward to the next page in history"},
                    {"description": "Home", "keys": "Alt+Home", "category": "Navigation", "detail": "Open your homepage"},
                    {"description": "Find in Page", "keys": "Ctrl+F", "category": "Page", "detail": "Search for text within the current page"},
                    {"description": "Find Next", "keys": "F3", "category": "Page", "detail": "Find the next match for your search"},
                    {"description": "Print", "keys": "Ctrl+P", "category": "Page", "detail": "Print the current page"},
                    {"description": "Save Page", "keys": "Ctrl+S", "category": "Page", "detail": "Save the current page to disk"},
                    {"description": "Zoom In", "keys": "Ctrl++", "category": "View", "detail": "Increase the page zoom level"},
                    {"description": "Zoom Out", "keys": "Ctrl+-", "category": "View", "detail": "Decrease the page zoom level"},
                    {"description": "Reset Zoom", "keys": "Ctrl+0", "category": "View", "detail": "Reset to the default zoom level"},
                    {"description": "Developer Tools", "keys": "F12 / Ctrl+Shift+I", "category": "Developer", "detail": "Open the Chrome Developer Tools"},
                    {"description": "View Source", "keys": "Ctrl+U", "category": "Developer", "detail": "View the source code of the current page"}
                ],
                
                # Explorer shortcuts
                "explorer.exe": [
                    {"description": "New Folder", "keys": "Ctrl+Shift+N", "category": "File Management", "detail": "Create a new folder in the current location"},
                    {"description": "Rename Item", "keys": "F2", "category": "File Management", "detail": "Rename the selected file or folder"},
                    {"description": "Delete to Recycle Bin", "keys": "Delete", "category": "File Management", "detail": "Move selected items to the Recycle Bin"},
                    {"description": "Permanent Delete", "keys": "Shift+Delete", "category": "File Management", "detail": "Delete selected items permanently (bypass Recycle Bin)"},
                    {"description": "Copy Item", "keys": "Ctrl+C", "category": "File Management", "detail": "Copy selected files or folders"},
                    {"description": "Cut Item", "keys": "Ctrl+X", "category": "File Management", "detail": "Cut selected files or folders for moving"},
                    {"description": "Paste Item", "keys": "Ctrl+V", "category": "File Management", "detail": "Paste copied or cut files or folders"},
                    {"description": "Copy Path", "keys": "Shift+Right Click > Copy Path", "category": "File Management", "detail": "Copy the full path of selected items to clipboard"},
                    {"description": "Properties", "keys": "Alt+Enter", "category": "File Management", "detail": "Show properties of selected items"},
                    {"description": "Select All", "keys": "Ctrl+A", "category": "Selection", "detail": "Select all items in the current view"},
                    {"description": "Invert Selection", "keys": "Ctrl+Space", "category": "Selection", "detail": "Invert the current selection"},
                    {"description": "Navigate Up", "keys": "Alt+↑", "category": "Navigation", "detail": "Go up one level to the parent folder"},
                    {"description": "Back", "keys": "Alt+←", "category": "Navigation", "detail": "Go back to previous location"},
                    {"description": "Forward", "keys": "Alt+→", "category": "Navigation", "detail": "Go forward to next location"},
                    {"description": "Quick Access", "keys": "Alt+D", "category": "Navigation", "detail": "Focus the address bar"},
                    {"description": "Refresh", "keys": "F5", "category": "View", "detail": "Refresh the current view"},
                    {"description": "Change View", "keys": "Ctrl+Shift+1..6", "category": "View", "detail": "Switch between different view modes"},
                    {"description": "Open Command Prompt", "keys": "Shift+Right Click > Open Command Window", "category": "Tools", "detail": "Open command prompt at current location"},
                    {"description": "Search", "keys": "F3 or Ctrl+F", "category": "Search", "detail": "Start search in current folder"}
                ],
                
                # Add other applications like Word, Excel, PowerPoint, etc.
                "WINWORD.EXE": [
                    {"description": "New Document", "keys": "Ctrl+N", "category": "Document", "detail": "Create a new document"},
                    {"description": "Open Document", "keys": "Ctrl+O", "category": "Document", "detail": "Open an existing document"},
                    {"description": "Save", "keys": "Ctrl+S", "category": "Document", "detail": "Save the current document"},
                    {"description": "Save As", "keys": "F12", "category": "Document", "detail": "Save with a new name or format"},
                    {"description": "Print", "keys": "Ctrl+P", "category": "Document", "detail": "Print the current document"},
                    {"description": "Cut", "keys": "Ctrl+X", "category": "Editing", "detail": "Cut selected text to clipboard"},
                    {"description": "Copy", "keys": "Ctrl+C", "category": "Editing", "detail": "Copy selected text to clipboard"},
                    {"description": "Paste", "keys": "Ctrl+V", "category": "Editing", "detail": "Paste from clipboard"},
                    {"description": "Undo", "keys": "Ctrl+Z", "category": "Editing", "detail": "Undo last action"},
                    {"description": "Redo", "keys": "Ctrl+Y", "category": "Editing", "detail": "Redo last undone action"},
                    {"description": "Find", "keys": "Ctrl+F", "category": "Navigation", "detail": "Find text in the document"},
                    {"description": "Replace", "keys": "Ctrl+H", "category": "Navigation", "detail": "Find and replace text"},
                    {"description": "Go To", "keys": "Ctrl+G", "category": "Navigation", "detail": "Go to a specific page or section"},
                    {"description": "Bold", "keys": "Ctrl+B", "category": "Formatting", "detail": "Make selected text bold"},
                    {"description": "Italic", "keys": "Ctrl+I", "category": "Formatting", "detail": "Make selected text italic"},
                    {"description": "Underline", "keys": "Ctrl+U", "category": "Formatting", "detail": "Underline selected text"}
                ]
            }
            
            # Write default shortcuts to file
            with open(config_path, 'w') as f:
                json.dump(default_shortcuts, f, indent=2)
            
            return default_shortcuts
        
        # Load existing shortcuts
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            print(f"Error loading shortcuts from {config_path}")
            return {}
    
    def get_active_window_process(self):
        """Get the process name of the currently active window"""
        try:
            # Get handle of active window
            hwnd = win32gui.GetForegroundWindow()
            
            # Get process ID from window handle
            _, process_id = win32process.GetWindowThreadProcessId(hwnd)
            
            # Get process name from process ID
            process = psutil.Process(process_id)
            return process.name()
        except Exception as e:
            print(f"Error getting active window process: {e}")
            return None
    
    def display_shortcuts(self, process_name):
        """Display shortcuts for the active application"""
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Update app name in the UI
        friendly_name = process_name.replace(".exe", "").capitalize()
        self.app_name_label.config(text=f"Current Application: {friendly_name}")
        
        # Check if we have shortcuts for this process
        if process_name in self.shortcuts_db:
            shortcuts = self.shortcuts_db[process_name]
            
            # Group shortcuts by category
            categories = {}
            for shortcut in shortcuts:
                category = shortcut.get("category", "General")
                if category not in categories:
                    categories[category] = []
                categories[category].append(shortcut)
            
            # Add categories and shortcuts to the tree
            for category, shortcuts in categories.items():
                # Add category as parent
                category_id = self.tree.insert("", "end", text=category, values=("", ""))
                
                # Add shortcuts under the category
                for shortcut in shortcuts:
                    # Get description or empty string if not available
                    description = shortcut.get("detail", "")
                    
                    self.tree.insert(
                        category_id, 
                        "end", 
                        text=shortcut["description"], 
                        values=(shortcut["keys"], description)
                    )
                
                # Expand the category
                self.tree.item(category_id, open=True)
                
            # Set focus to the first item for keyboard navigation
            if self.tree.get_children():
                first_category = self.tree.get_children()[0]
                self.tree.focus(first_category)
                self.tree.selection_set(first_category)
                
        else:
            # No shortcuts available
            no_shortcuts_id = self.tree.insert("", "end", text=f"No shortcuts available for {process_name}", values=("", ""))
            self.tree.focus(no_shortcuts_id)
            self.tree.selection_set(no_shortcuts_id)
    
    def show_overlay(self):
        """Toggle the shortcut overlay for the current application"""
        # If already visible, hide it
        if self.root.state() == 'normal':
            self.hide_overlay()
            return
            
        # Get the active window process
        process_name = self.get_active_window_process()
        
        # Update shortcuts display
        if process_name:
            self.display_shortcuts(process_name)
        
        # Show the window
        self.root.deiconify()
        self.root.attributes('-alpha', 0.9)
        self.root.lift()
    
    # Fade functions removed since we're using toggle functionality
    
    def hide_overlay(self):
        """Hide the overlay"""
        self.root.withdraw()
    
    def create_tray_icon(self):
        """Create a system tray icon (Windows only)"""
        try:
            import pystray
            from PIL import Image, ImageDraw
            
            # Create a simple icon
            icon_size = 64
            icon_image = Image.new('RGB', (icon_size, icon_size), color=(0, 0, 0))
            d = ImageDraw.Draw(icon_image)
            
            # Draw 'K' for keyboard
            d.text((20, 10), "K", fill=(255, 255, 255))
            
            # Create a menu
            menu = pystray.Menu(
                pystray.MenuItem("Show Shortcuts", self.show_overlay),
                pystray.MenuItem("Exit", self.exit_app)
            )
            
            # Create the tray icon
            self.icon = pystray.Icon("ShortcutHelper", icon_image, "Shortcut Helper", menu)
            
            # Run the icon in a separate thread
            import threading
            self.icon_thread = threading.Thread(target=self.icon.run)
            self.icon_thread.daemon = True
            self.icon_thread.start()
            
        except ImportError:
            print("pystray or PIL not found. System tray icon will not be available.")
    
    def exit_app(self):
        """Exit the application cleanly"""
        if hasattr(self, 'icon'):
            self.icon.stop()
        self.root.quit()
        sys.exit(0)
    
    def run(self):
        """Run the application"""
        print(f"Shortcut Helper running. Press {SHORTCUT_TRIGGER} to show shortcuts.")
        self.root.mainloop()


if __name__ == "__main__":
    # Check if running on Windows
    if sys.platform != 'win32':
        print("This application is designed for Windows only.")
        sys.exit(1)
    
    # Set process DPI awareness (Windows 8.1+)
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except AttributeError:
        # Windows 8.0 and below
        ctypes.windll.user32.SetProcessDPIAware()
    
    # Create and run the application
    app = ShortcutHelper()
    app.run()