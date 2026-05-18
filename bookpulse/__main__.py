"""
BookPulse - Main Entry Point
Allows running the CLI with: python -m bookpulse
"""

from .cli import main
import sys

if __name__ == "__main__":
    sys.exit(main())
