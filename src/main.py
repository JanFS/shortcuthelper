import sys
from src.app import ShortcutHelperApp

def main():
    app = ShortcutHelperApp()
    app.run()
    return 0

if __name__ == "__main__":
    sys.exit(main())