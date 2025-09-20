# admin/activity.py
import sqlite3
import datetime
import os
import logging

logger = logging.getLogger(__name__)

class ActivityTracker:
    def __init__(self, db_path="admin.db"):
        self.db_path = db_path
        self.init_db()
    
    def init_db(self):
        """Initialize database with both logs and reports tables"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create logs table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
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
                    timestamp TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()
            conn.close()
            logger.info("Admin database initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
    
    def log(self, level, message, user_id=None, command=None, module=None):
        """Log a message to the database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            timestamp = datetime.datetime.now().isoformat()
            
            cursor.execute("""
                INSERT INTO logs (timestamp, level, message, user_id, command, module)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (timestamp, level, message, user_id, command, module))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Error logging to database: {e}")

# Global tracker instance
activity_tracker = ActivityTracker()

def log_activity(level, message, user_id=None, command=None, module=None):
    """Convenience function to log activity"""
    activity_tracker.log(level, message, user_id, command, module)