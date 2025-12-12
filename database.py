# database.py
import sqlite3

class Database:
    def __init__(self, db_name='volunteers.db'):
        self.conn = sqlite3.connect(db_name, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.create_tables()
    
    def create_tables(self):
        # Упрощенная таблица пользователей
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER UNIQUE,
            login TEXT UNIQUE,
            password TEXT,
            full_name TEXT,
            phone TEXT,
            email TEXT,
            birth_date TEXT,
            rating REAL DEFAULT 5.0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        self.conn.commit()
    
    def user_exists(self, telegram_id):
        self.cursor.execute('SELECT id FROM users WHERE telegram_id = ?', (telegram_id,))
        return self.cursor.fetchone() is not None
    
    def close(self):
        self.conn.close()