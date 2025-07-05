import sys
import os

# Add project dir to path if needed
sys.path.insert(0, os.path.dirname(__file__))

# Import Flask app as WSGI application
from server import app as application