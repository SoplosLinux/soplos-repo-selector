#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Soplos Repo Selector 2.0.0 - Advanced Repository Manager

Main application entry point.
"""

import sys
import os
import warnings
from pathlib import Path

# Add the project root to PYTHONPATH
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))
# Suppress accessibility warnings for a cleaner output
warnings.filterwarnings('ignore', '.*Couldn\'t connect to accessibility bus.*', Warning)
warnings.filterwarnings('ignore', '.*Failed to connect to socket.*', Warning)

# Disable accessibility bridge unless explicitly enabled
if not os.environ.get('ENABLE_ACCESSIBILITY'):
    os.environ['NO_AT_BRIDGE'] = '1'
    os.environ['AT_SPI_BUS'] = '0'

def main():
    """Main entry point for Soplos Repo Selector."""
    try:
        # Import and run the application
        # Note: core.application will be implemented in the following step
        from core.application import run_application
        return run_application()
        
    except ImportError as e:
        print(f"Import error: {e}")
        print("Ensure all dependencies are installed:")
        print("  sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-3.0")
        # Temporary fallback for debugging until core is ready
        import traceback
        traceback.print_exc()
        return 1
        
    except Exception as e:
        print(f"Application error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())
