"""Работа с базой данных SQLite"""
import sqlite3
import logging
import os

logger = logging.getLogger(__name__)


class Database:
    """Менеджер базы данных"""
    
    def __init__(self, db_name: str = "data/bot.db"):
        self.db_name = db_name
        os.makedirs(os.path.dirname(db_name), exist_ok=True)
        self.init_database()
    
    def get_connection(self):
        """Получить соединение"""
        conn = sqlite3.connect(self.db_name, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_database(self):
        """Инициализация БД"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Таблица пользователей
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER UNIQUE NOT NULL,
                full_name TEXT NOT NULL,
                phone TEXT,
                email TEXT UNIQUE,
                password_hash TEXT NOT NULL,
                rating REAL DEFAULT 5.0,
                help_offered_count INTEGER DEFAULT 0,
                help_received_count INTEGER DEFAULT 0,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            
            # Таблица заявок
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                category TEXT NOT NULL,
                status TEXT DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
            ''')
            
            # Таблица предложений помощи
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS offers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                category TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                contacts TEXT NOT NULL,
                status TEXT DEFAULT 'active',
                views INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
            ''')
            
            conn.commit()
            logger.info("✅ База данных инициализирована")
    
    def create_user(self, telegram_id: int, full_name: str, phone: str, 
                   email: str, password_hash: str):
        """Создать пользователя"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                INSERT INTO users (telegram_id, full_name, phone, email, password_hash)
                VALUES (?, ?, ?, ?, ?)
                ''', (telegram_id, full_name, phone, email, password_hash))
                conn.commit()
                return cursor.lastrowid
        except sqlite3.IntegrityError as e:
            logger.error(f"❌ Ошибка при создании пользователя: {e}")
            return None
    
    def get_user_by_telegram_id(self, telegram_id: int):
        """Получить пользователя по Telegram ID"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE telegram_id = ?', (telegram_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_user_by_email(self, email: str):
        """Получить пользователя по email"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE email = ?', (email.lower(),))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_user_by_phone(self, phone: str):
        """Получить пользователя по номеру"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE phone = ?', (phone,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def update_user(self, user_id: int, **kwargs):
        """Обновить пользователя"""
        if not kwargs:
            return False
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                set_clause = ', '.join([f"{key} = ?" for key in kwargs.keys()])
                query = f'UPDATE users SET {set_clause} WHERE id = ?'
                values = list(kwargs.values()) + [user_id]
                
                cursor.execute(query, values)
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"❌ Ошибка обновления: {e}")
            return False
    
    def get_statistics(self):
        """Получить статистику"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            stats = {}
            
            cursor.execute('SELECT COUNT(*) as count FROM users WHERE is_active = 1')
            stats['total_users'] = cursor.fetchone()['count']
            
            cursor.execute('SELECT COUNT(*) as count FROM requests WHERE status = "active"')
            stats['active_requests'] = cursor.fetchone()['count']
            
            cursor.execute('SELECT COUNT(*) as count FROM requests WHERE status = "completed"')
            stats['completed_requests'] = cursor.fetchone()['count']
            
            return stats


# Глобальный экземпляр
db = Database()