# Tracker2/app/__init__.py
from .database import init_db

def create_app():
    init_db()
    # Rest van uw app configuratie