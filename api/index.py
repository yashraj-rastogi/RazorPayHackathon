"""
Vercel Serverless Entry Point for RevGuard FastAPI Backend.
"""
import sys
import os
from pathlib import Path

# Ensure the repository root is in sys.path so 'backend' modules are found
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from backend.main import app

# Vercel Python runtime detects the ASGI 'app' object
