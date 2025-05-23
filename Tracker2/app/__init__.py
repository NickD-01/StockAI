# Tracker2/app/__init__.py
from Tracker2.database import init_db

def create_app():
    init_db()
    # Rest van uw app configuratie