import sys
import os

# Expose the client's preprocessor cleanly to the core intelligence layer
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from client.preprocessor import build_analysis_context
