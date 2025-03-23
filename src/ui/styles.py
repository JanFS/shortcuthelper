def apply_theme(root, theme_name="dark"):
    """Apply the specified theme to the tkinter root window"""
    if theme_name == "dark":
        # Define dark theme colors
        colors = {
            'bg': '#1E1E1E',  # Dark background
            'fg': 'white',    # Light text
            'accent': '#0078D7',  # Blue accent
            'highlight': '#3D7ABB',
            'dark_accent': '#005A9E',
            'light_text': '#CCCCCC'
        }
    else:
        # Define light theme colors
        colors = {
            'bg': '#F0F0F0',  # Light background
            'fg': 'black',    # Dark text
            'accent': '#0078D7',  # Blue accent
            'highlight': '#3D7ABB',
            'dark_accent': '#005A9E',
            'light_text': '#555555'
        }
    
    # Apply the theme colors to the root window
    root.configure(bg=colors['bg'])
    
    # Return the colors dictionary for other components to use
    return colors