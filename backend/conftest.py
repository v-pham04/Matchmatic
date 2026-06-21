import sys
import os

# Add the backend/ folder to Python's path so pytest can find the 'app' package
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))