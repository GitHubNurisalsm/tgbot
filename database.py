"""Работа с базой данных SQLite"""
import sqlite3
import logging
import os
import json
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

DB_PATH = os.getenv("DATABASE_PATH", "data/bot_database.db")
USER_JSON_PATH = os.path.join("data", "users.json")
USER_FILES_TO_CLEAR = [
    USER_JSON_PATH,
    os.path.join("data", "user_ratings.json"),
    os.path.join("data", "user_reviews.json"),
    os.path.join("data", "user_stats.json"),
]


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
        """Получить пользователя по Telegram ID - проверяет и БД, и users.json"""
        telegram_id_str = str(telegram_id)
        logger.info(f"Поиск пользователя с telegram_id: {telegram_id_str}")
        
        # Сначала проверяем users.json
        try:
            if os.path.exists(USER_JSON_PATH):
                with open(USER_JSON_PATH, 'r', encoding='utf-8') as f:
                    txt = f.read().strip()
                    if txt:
                        users_data = json.loads(txt)
                        user_data = users_data.get(telegram_id_str)
                        if user_data:
                            logger.info(f"✅ Пользователь {telegram_id_str} найден в users.json")
                            return user_data
                        else:
                            logger.debug(f"Пользователь {telegram_id_str} не найден в users.json. Доступные ключи: {list(users_data.keys())}")
        except Exception as e:
            logger.error(f"Ошибка чтения users.json: {e}", exc_info=True)
        
        # Если не найдено в файле, проверяем БД
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM users WHERE telegram_id = ?', (telegram_id,))
                row = cursor.fetchone()
                if row:
                    logger.info(f"✅ Пользователь {telegram_id_str} найден в БД")
                    return dict(row)
        except Exception as e:
            logger.error(f"Ошибка проверки БД: {e}", exc_info=True)
        
        logger.warning(f"❌ Пользователь {telegram_id_str} не найден ни в users.json, ни в БД")
        return None
    
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

    def _sqlite_conn(self):
        try:
            return sqlite3.connect(self.db_name)
        except Exception as e:
            logger.debug("SQLite not available: %s", e)
            return None

    def create_or_update_user(self, user_data: Dict[str, Any]) -> bool:
        telegram_id = str(user_data.get('telegram_id') or user_data.get('user_id') or user_data.get('id'))
        if not telegram_id:
            logger.error("create_or_update_user: telegram_id not provided")
            return False

        # Try SQLite upsert
        conn = self._sqlite_conn()
        if conn:
            try:
                cur = conn.cursor()
                # ensure table exists; keep simple schema with telegram_id and data(JSON)
                cur.execute("""CREATE TABLE IF NOT EXISTS users (
                                telegram_id TEXT PRIMARY KEY,
                                data TEXT
                              )""")
                cur.execute("INSERT OR REPLACE INTO users (telegram_id, data) VALUES (?, ?)",
                            (telegram_id, json.dumps(user_data, ensure_ascii=False)))
                conn.commit()
                return True
            except Exception as e:
                logger.debug("SQLite write failed: %s", e)
            finally:
                conn.close()

        # Fallback to file
        os.makedirs(os.path.dirname(USER_JSON_PATH), exist_ok=True)
        try:
            existing = {}
            if os.path.exists(USER_JSON_PATH):
                with open(USER_JSON_PATH, 'r', encoding='utf-8') as f:
                    t = f.read().strip()
                    existing = json.loads(t) if t else {}
            existing[telegram_id] = user_data
            with open(USER_JSON_PATH, 'w', encoding='utf-8') as f:
                json.dump(existing, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            logger.error("Failed to save user to file: %s", e)
            return False

    def clear_all_users(self):
        """Удаляет всех пользователей из БД / файлов — заставляет всех зарегистрированных пройти регистрацию заново"""
        # Clear SQLite users table
        conn = self._sqlite_conn()
        if conn:
            try:
                cur = conn.cursor()
                # if table exists, clear it
                cur.execute("DROP TABLE IF EXISTS users")
                conn.commit()
                logger.info("Cleared SQLite users table")
            except Exception as e:
                logger.warning("Failed to clear SQLite users table: %s", e)
            finally:
                conn.close()

        # Clear several JSON files used to store user data or stats
        for p in USER_FILES_TO_CLEAR:
            try:
                if os.path.exists(p):
                    # For json files, rewrite as empty object {}
                    with open(p, 'w', encoding='utf-8') as f:
                        json.dump({}, f, ensure_ascii=False, indent=2)
                    logger.info("Cleared file: %s", p)
            except Exception as e:
                logger.warning("Failed to clear file %s: %s", p, e)


# Глобальный экземпляр
db = Database()