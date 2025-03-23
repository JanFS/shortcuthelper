import os
import json

def load_default_shortcuts():
    """Load default shortcuts for various applications"""
    
    # This provides default shortcuts when JSON files aren't available yet
    default_shortcuts = {
        # VSCode shortcuts
        "Code.exe": [
            {"description": "Show Command Palette", "keys": "Ctrl+Shift+P", "category": "General", "detail": "Access all commands in VS Code"},
            {"description": "Quick Open", "keys": "Ctrl+P", "category": "General", "detail": "Search and open files in the current project"},
            {"description": "New File", "keys": "Ctrl+N", "category": "General", "detail": "Create a new file in the editor"},
            {"description": "Save", "keys": "Ctrl+S", "category": "General", "detail": "Save the current file"},
            {"description": "Save As", "keys": "Ctrl+Shift+S", "category": "General", "detail": "Save the current file with a new name"}
        ],
        
        # Chrome shortcuts
        "chrome.exe": [
            {"description": "New Tab", "keys": "Ctrl+T", "category": "Tabs", "detail": "Open a new browser tab"},
            {"description": "Close Tab", "keys": "Ctrl+W", "category": "Tabs", "detail": "Close the current browser tab"},
            {"description": "Reopen Closed Tab", "keys": "Ctrl+Shift+T", "category": "Tabs", "detail": "Restore the most recently closed tab"}
        ],
        
        # Add a generic entry for whatever application is currently active
        "explorer.exe": [
            {"description": "New Folder", "keys": "Ctrl+Shift+N", "category": "File Management", "detail": "Create a new folder in the current location"},
            {"description": "Rename Item", "keys": "F2", "category": "File Management", "detail": "Rename the selected file or folder"}
        ]
    }
    
    # TODO: In a full implementation, load these from JSON files if they exist
    
    print(f"Loaded {len(default_shortcuts)} applications with shortcuts")
    return default_shortcuts

# You could also add a function to load shortcuts from JSON files in a more advanced implementation
def load_shortcuts_from_file(file_path):
    """Load shortcuts from a JSON file"""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading shortcuts from {file_path}: {e}")
        return {}