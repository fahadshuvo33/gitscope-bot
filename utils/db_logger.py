import sqlite3
import datetime
import os

class DatabaseLogger:
    def __init__(self, db_path="logs.db"):
        self.db_path = db_path
        self.init_db()
    
    def init_db(self):
        """Initialize database and create logs table if not exists"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    level TEXT NOT NULL,
                    message TEXT NOT NULL,
                    user_id TEXT,
                    command TEXT
                )
            """)
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Error initializing database: {e}")
    
    def log(self, level, message, user_id=None, command=None):
        """Log a message to the database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            timestamp = datetime.datetime.now().isoformat()
            
            cursor.execute("""
                INSERT INTO logs (timestamp, level, message, user_id, command)
                VALUES (?, ?, ?, ?, ?)
            """, (timestamp, level, message, user_id, command))
            
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Error logging to database: {e}")

# Global logger instance
db_logger = DatabaseLogger()

def log_activity(level, message, user_id=None, command=None):
    """Convenience function to log activity"""
    db_logger.log(level, message, user_id, command)
