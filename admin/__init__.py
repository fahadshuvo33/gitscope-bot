# admin/__init__.py
import os
import sqlite3
import logging

logger = logging.getLogger(__name__)

# Admin username from environment
ADMIN_TELEGRAM_USERNAME = os.getenv("ADMIN_TELEGRAM_USERNAME")
ADMIN_GITHUB_USERNAME = os.getenv("ADMIN_GITHUB_USERNAME")

def is_admin_telegram(username: str) -> bool:
    """Check if user is admin"""
    if not username or not ADMIN_TELEGRAM_USERNAME:
        return False
    return username.lower() == ADMIN_TELEGRAM_USERNAME.lower()

def is_admin_github(username: str) -> bool:
    """Check if user is admin"""
    if not username or not ADMIN_GITHUB_USERNAME:
        return False
    return username.lower() == ADMIN_GITHUB_USERNAME.lower()

def init_admin_db():
    """Initialize admin database with both logs and reports tables"""
    try:
        conn = sqlite3.connect('admin.db')
        cursor = conn.cursor()
        
        # Create logs table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                level TEXT NOT NULL,
                message TEXT NOT NULL,
                user_id TEXT,
                command TEXT,
                module TEXT
            )
        """)
        
        # Create reports table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                username TEXT,
                message TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            )
        """)
        
        conn.commit()
        conn.close()
        logger.info("Admin database initialized")
    except Exception as e:
        logger.error(f"Error initializing admin database: {e}")

# Initialize database when module is imported
init_admin_db()