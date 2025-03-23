import os
import json

def load_default_shortcuts():
    """Load shortcuts from JSON files or use built-in defaults"""
    
    # Path to the shortcuts data directory
    data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "default_shortcuts")
    
    # Check if the directory exists, create it if it doesn't
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    
    # Dictionary to store all shortcuts
    shortcuts_db = {}
    
    # List of known applications and their JSON files
    app_files = {
        "Code.exe": "vscode.json",
        "chrome.exe": "chrome.json",
        "explorer.exe": "explorer.json"
    }
    
    # Try to load shortcuts from JSON files
    for app_name, file_name in app_files.items():
        file_path = os.path.join(data_dir, file_name)
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    app_data = json.load(f)
                    # Check if the file contains the right structure
                    if app_name in app_data:
                        shortcuts_db[app_name] = app_data[app_name]
                        print(f"Loaded {len(app_data[app_name])} shortcuts for {app_name}")
                    else:
                        # If the JSON doesn't have the app name as a key, assume the whole file is for that app
                        shortcuts_db[app_name] = app_data
                        print(f"Loaded {len(app_data)} shortcuts for {app_name}")
            except Exception as e:
                print(f"Error loading shortcuts from {file_path}: {e}")
    
    # If no shortcuts were loaded from files, use built-in defaults
    if not shortcuts_db:
        print("No shortcut files found, using built-in defaults")
        shortcuts_db = {
            # VSCode shortcuts (simplified)
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
            
            # Brave shortcuts
            "brave.exe": [
                {"description": "New Tab", "keys": "Ctrl+T", "category": "Tabs", "detail": "Open a new browser tab"},
                {"description": "Close Tab", "keys": "Ctrl+W", "category": "Tabs", "detail": "Close the current browser tab"},
                {"description": "Reopen Closed Tab", "keys": "Ctrl+Shift+T", "category": "Tabs", "detail": "Restore the most recently closed tab"}
            ],
            
            # Explorer shortcuts
            "explorer.exe": [
                {"description": "New Folder", "keys": "Ctrl+Shift+N", "category": "File Management", "detail": "Create a new folder in the current location"},
                {"description": "Rename Item", "keys": "F2", "category": "File Management", "detail": "Rename the selected file or folder"}
            ]
        }
    
    print(f"Loaded shortcuts for {len(shortcuts_db)} applications")
    return shortcuts_db

def load_shortcuts_from_file(file_path):
    """Load shortcuts from a JSON file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading shortcuts from {file_path}: {e}")
        return {}