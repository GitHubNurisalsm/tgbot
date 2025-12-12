# database_utils.py
"""
Модуль для работы с базой данных (SQLite)
"""
import sqlite3
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Union
from contextlib import contextmanager
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseManager:
    """Менеджер базы данных SQLite"""
    
    def __init__(self, db_path: str = "data/bot_database.db"):
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Инициализирует базу данных и создает таблицы если их нет"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Таблица пользователей
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    language_code TEXT,
                    is_bot INTEGER DEFAULT 0,
                    registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active INTEGER DEFAULT 1,
                    settings TEXT DEFAULT '{}'
                )
            ''')
            
            # Таблица профилей пользователей
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_profiles (
                    profile_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    full_name TEXT,
                    age INTEGER,
                    email TEXT,
                    phone TEXT,
                    bio TEXT,
                    skills TEXT DEFAULT '[]',
                    experience TEXT DEFAULT '{}',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE,
                    UNIQUE(user_id)
                )
            ''')
            
            # Таблица запросов на помощь
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS help_requests (
                    request_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    title TEXT,
                    description TEXT,
                    category TEXT,
                    budget REAL,
                    currency TEXT DEFAULT 'RUB',
                    deadline TIMESTAMP,
                    status TEXT DEFAULT 'open',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    views INTEGER DEFAULT 0,
                    applications_count INTEGER DEFAULT 0,
                    is_active INTEGER DEFAULT 1,
                    tags TEXT DEFAULT '[]',
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            ''')
            
            # Таблица предложений помощи
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS help_offers (
                    offer_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    title TEXT,
                    description TEXT,
                    category TEXT,
                    price REAL,
                    currency TEXT DEFAULT 'RUB',
                    availability TEXT,
                    status TEXT DEFAULT 'active',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    views INTEGER DEFAULT 0,
                    responses_count INTEGER DEFAULT 0,
                    is_active INTEGER DEFAULT 1,
                    tags TEXT DEFAULT '[]',
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            ''')
            
            # Таблица откликов на запросы
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS request_applications (
                    application_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    request_id INTEGER,
                    applicant_id INTEGER,
                    message TEXT,
                    proposed_price REAL,
                    proposed_timeline TEXT,
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active INTEGER DEFAULT 1,
                    FOREIGN KEY (request_id) REFERENCES help_requests (request_id),
                    FOREIGN KEY (applicant_id) REFERENCES users (user_id),
                    UNIQUE(request_id, applicant_id)
                )
            ''')
            
            # Таблица отзывов и рейтингов
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS reviews (
                    review_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    reviewer_id INTEGER,
                    reviewed_id INTEGER,
                    request_id INTEGER,
                    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
                    comment TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_verified INTEGER DEFAULT 0,
                    FOREIGN KEY (reviewer_id) REFERENCES users (user_id),
                    FOREIGN KEY (reviewed_id) REFERENCES users (user_id),
                    FOREIGN KEY (request_id) REFERENCES help_requests (request_id)
                )
            ''')
            
            # Таблица сообщений
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS messages (
                    message_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sender_id INTEGER,
                    receiver_id INTEGER,
                    request_id INTEGER,
                    message_text TEXT,
                    message_type TEXT DEFAULT 'text',
                    is_read INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (sender_id) REFERENCES users (user_id),
                    FOREIGN KEY (receiver_id) REFERENCES users (user_id),
                    FOREIGN KEY (request_id) REFERENCES help_requests (request_id)
                )
            ''')
            
            # Таблица уведомлений
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS notifications (
                    notification_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    notification_type TEXT,
                    title TEXT,
                    message TEXT,
                    data TEXT DEFAULT '{}',
                    is_read INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            ''')
            
            # Таблица сессий пользователей
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_sessions (
                    session_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    state TEXT,
                    data TEXT DEFAULT '{}',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            ''')
            
            # Индексы для ускорения поиска
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_requests_user ON help_requests(user_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_requests_status ON help_requests(status)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_offers_user ON help_offers(user_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_applications_request ON request_applications(request_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_reviews_reviewed ON reviews(reviewed_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_messages_conversation ON messages(sender_id, receiver_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_notifications_user ON notifications(user_id)')
            
            conn.commit()
            logger.info("База данных инициализирована")
    
    @contextmanager
    def _get_connection(self):
        """Контекстный менеджер для получения соединения с БД"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Возвращать строки как словари
        try:
            yield conn
        except sqlite3.Error as e:
            logger.error(f"Ошибка базы данных: {e}")
            conn.rollback()
            raise
        finally:
            conn.close()
    
    # === МЕТОДЫ ДЛЯ РАБОТЫ С ПОЛЬЗОВАТЕЛЯМИ ===
    
    def get_or_create_user(self, user_data: Dict) -> Dict:
        """
        Получает или создает пользователя
        
        Args:
            user_data: Данные пользователя из Telegram
            
        Returns:
            Dict: Данные пользователя из БД
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Проверяем существование пользователя
            cursor.execute(
                'SELECT * FROM users WHERE user_id = ?',
                (user_data['id'],)
            )
            user = cursor.fetchone()
            
            if user:
                # Обновляем last_active
                cursor.execute(
                    'UPDATE users SET last_active = CURRENT_TIMESTAMP WHERE user_id = ?',
                    (user_data['id'],)
                )
                conn.commit()
                return dict(user)
            
            # Создаем нового пользователя
            cursor.execute('''
                INSERT INTO users (
                    user_id, username, first_name, last_name, 
                    language_code, is_bot
                ) VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                user_data['id'],
                user_data.get('username'),
                user_data.get('first_name'),
                user_data.get('last_name'),
                user_data.get('language_code'),
                1 if user_data.get('is_bot') else 0
            ))
            
            conn.commit()
            
            # Получаем созданного пользователя
            cursor.execute(
                'SELECT * FROM users WHERE user_id = ?',
                (user_data['id'],)
            )
            return dict(cursor.fetchone())
    
    def update_user_settings(self, user_id: int, settings: Dict) -> bool:
        """Обновляет настройки пользователя"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'UPDATE users SET settings = ? WHERE user_id = ?',
                (json.dumps(settings), user_id)
            )
            conn.commit()
            return cursor.rowcount > 0
    
    def get_user_settings(self, user_id: int) -> Dict:
        """Получает настройки пользователя"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT settings FROM users WHERE user_id = ?',
                (user_id,)
            )
            row = cursor.fetchone()
            if row and row['settings']:
                return json.loads(row['settings'])
            return {}
    
    # === МЕТОДЫ ДЛЯ РАБОТЫ С ПРОФИЛЯМИ ===
    
    def create_user_profile(self, user_id: int, profile_data: Dict) -> int:
        """Создает профиль пользователя"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Проверяем, есть ли уже профиль
            cursor.execute(
                'SELECT profile_id FROM user_profiles WHERE user_id = ?',
                (user_id,)
            )
            existing = cursor.fetchone()
            
            if existing:
                # Обновляем существующий профиль
                cursor.execute('''
                    UPDATE user_profiles SET
                        full_name = ?,
                        age = ?,
                        email = ?,
                        phone = ?,
                        bio = ?,
                        skills = ?,
                        experience = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = ?
                ''', (
                    profile_data.get('full_name'),
                    profile_data.get('age'),
                    profile_data.get('email'),
                    profile_data.get('phone'),
                    profile_data.get('bio'),
                    json.dumps(profile_data.get('skills', [])),
                    json.dumps(profile_data.get('experience', {})),
                    user_id
                ))
                profile_id = existing['profile_id']
            else:
                # Создаем новый профиль
                cursor.execute('''
                    INSERT INTO user_profiles (
                        user_id, full_name, age, email, phone, bio, skills, experience
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    user_id,
                    profile_data.get('full_name'),
                    profile_data.get('age'),
                    profile_data.get('email'),
                    profile_data.get('phone'),
                    profile_data.get('bio'),
                    json.dumps(profile_data.get('skills', [])),
                    json.dumps(profile_data.get('experience', {}))
                ))
                profile_id = cursor.lastrowid
            
            conn.commit()
            return profile_id
    
    def get_user_profile(self, user_id: int) -> Optional[Dict]:
        """Получает профиль пользователя"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT * FROM user_profiles WHERE user_id = ?',
                (user_id,)
            )
            row = cursor.fetchone()
            if row:
                profile = dict(row)
                # Десериализуем JSON поля
                profile['skills'] = json.loads(profile['skills']) if profile['skills'] else []
                profile['experience'] = json.loads(profile['experience']) if profile['experience'] else {}
                return profile
            return None
    
    # === МЕТОДЫ ДЛЯ ЗАПРОСОВ НА ПОМОЩЬ ===
    
    def create_help_request(self, user_id: int, request_data: Dict) -> int:
        """Создает запрос на помощь"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO help_requests (
                    user_id, title, description, category, 
                    budget, currency, deadline, tags
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                user_id,
                request_data['title'],
                request_data['description'],
                request_data['category'],
                request_data.get('budget'),
                request_data.get('currency', 'RUB'),
                request_data.get('deadline'),
                json.dumps(request_data.get('tags', []))
            ))
            
            request_id = cursor.lastrowid
            conn.commit()
            return request_id
    
    def get_help_request(self, request_id: int) -> Optional[Dict]:
        """Получает запрос на помощь по ID"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT hr.*, u.username, u.first_name
                FROM help_requests hr
                JOIN users u ON hr.user_id = u.user_id
                WHERE hr.request_id = ? AND hr.is_active = 1
            ''', (request_id,))
            
            row = cursor.fetchone()
            if row:
                request = dict(row)
                request['tags'] = json.loads(request['tags']) if request['tags'] else []
                return request
            return None
    
    def get_user_requests(self, user_id: int, limit: int = 50) -> List[Dict]:
        """Получает запросы пользователя"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM help_requests 
                WHERE user_id = ? AND is_active = 1
                ORDER BY created_at DESC
                LIMIT ?
            ''', (user_id, limit))
            
            requests = []
            for row in cursor.fetchall():
                request = dict(row)
                request['tags'] = json.loads(request['tags']) if request['tags'] else []
                requests.append(request)
            
            return requests
    
    def search_requests(self, category: str = None, max_budget: float = None, 
                       limit: int = 20) -> List[Dict]:
        """Поиск запросов по параметрам"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            query = '''
                SELECT hr.*, u.username, u.first_name
                FROM help_requests hr
                JOIN users u ON hr.user_id = u.user_id
                WHERE hr.status = 'open' 
                AND hr.is_active = 1
            '''
            params = []
            
            if category:
                query += ' AND hr.category = ?'
                params.append(category)
            
            if max_budget:
                query += ' AND (hr.budget IS NULL OR hr.budget <= ?)'
                params.append(max_budget)
            
            query += ' ORDER BY hr.created_at DESC LIMIT ?'
            params.append(limit)
            
            cursor.execute(query, params)
            
            requests = []
            for row in cursor.fetchall():
                request = dict(row)
                request['tags'] = json.loads(request['tags']) if request['tags'] else []
                requests.append(request)
            
            return requests
    
    def update_request_status(self, request_id: int, status: str) -> bool:
        """Обновляет статус запроса"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE help_requests 
                SET status = ?, updated_at = CURRENT_TIMESTAMP
                WHERE request_id = ?
            ''', (status, request_id))
            conn.commit()
            return cursor.rowcount > 0
    
    # === МЕТОДЫ ДЛЯ ПРЕДЛОЖЕНИЙ ПОМОЩИ ===
    
    def create_help_offer(self, user_id: int, offer_data: Dict) -> int:
        """Создает предложение помощи"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO help_offers (
                    user_id, title, description, category,
                    price, currency, availability, tags
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                user_id,
                offer_data['title'],
                offer_data['description'],
                offer_data['category'],
                offer_data.get('price'),
                offer_data.get('currency', 'RUB'),
                offer_data.get('availability'),
                json.dumps(offer_data.get('tags', []))
            ))
            
            offer_id = cursor.lastrowid
            conn.commit()
            return offer_id
    
    def get_help_offer(self, offer_id: int) -> Optional[Dict]:
        """Получает предложение помощи по ID"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT ho.*, u.username, u.first_name
                FROM help_offers ho
                JOIN users u ON ho.user_id = u.user_id
                WHERE ho.offer_id = ? AND ho.is_active = 1
            ''', (offer_id,))
            
            row = cursor.fetchone()
            if row:
                offer = dict(row)
                offer['tags'] = json.loads(offer['tags']) if offer['tags'] else []
                return offer
            return None
    
    def get_user_offers(self, user_id: int, limit: int = 50) -> List[Dict]:
        """Получает предложения помощи пользователя"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM help_offers 
                WHERE user_id = ? AND is_active = 1
                ORDER BY created_at DESC
                LIMIT ?
            ''', (user_id, limit))
            
            offers = []
            for row in cursor.fetchall():
                offer = dict(row)
                offer['tags'] = json.loads(offer['tags']) if offer['tags'] else []
                offers.append(offer)
            
            return offers
    
    # === МЕТОДЫ ДЛЯ ОТКЛИКОВ НА ЗАПРОСЫ ===
    
    def create_request_application(self, request_id: int, applicant_id: int, 
                                 application_data: Dict) -> int:
        """Создает отклик на запрос"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Проверяем, не откликался ли уже пользователь
            cursor.execute('''
                SELECT application_id FROM request_applications
                WHERE request_id = ? AND applicant_id = ? AND is_active = 1
            ''', (request_id, applicant_id))
            
            if cursor.fetchone():
                raise ValueError("Вы уже откликались на этот запрос")
            
            cursor.execute('''
                INSERT INTO request_applications (
                    request_id, applicant_id, message,
                    proposed_price, proposed_timeline
                ) VALUES (?, ?, ?, ?, ?)
            ''', (
                request_id,
                applicant_id,
                application_data['message'],
                application_data.get('proposed_price'),
                application_data.get('proposed_timeline')
            ))
            
            application_id = cursor.lastrowid
            
            # Увеличиваем счетчик откликов в запросе
            cursor.execute('''
                UPDATE help_requests 
                SET applications_count = applications_count + 1,
                    updated_at = CURRENT_TIMESTAMP
                WHERE request_id = ?
            ''', (request_id,))
            
            conn.commit()
            return application_id
    
    def get_request_applications(self, request_id: int) -> List[Dict]:
        """Получает отклики на запрос"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT ra.*, u.username, u.first_name
                FROM request_applications ra
                JOIN users u ON ra.applicant_id = u.user_id
                WHERE ra.request_id = ? AND ra.is_active = 1
                ORDER BY ra.created_at DESC
            ''', (request_id,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_user_applications(self, user_id: int) -> List[Dict]:
        """Получает отклики пользователя"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT ra.*, hr.title, hr.category
                FROM request_applications ra
                JOIN help_requests hr ON ra.request_id = hr.request_id
                WHERE ra.applicant_id = ? AND ra.is_active = 1
                ORDER BY ra.created_at DESC
            ''', (user_id,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    # === МЕТОДЫ ДЛЯ ОТЗЫВОВ И РЕЙТИНГОВ ===
    
    def create_review(self, reviewer_id: int, reviewed_id: int, 
                     review_data: Dict) -> int:
        """Создает отзыв"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Проверяем, не оставлял ли уже отзыв
            if review_data.get('request_id'):
                cursor.execute('''
                    SELECT review_id FROM reviews
                    WHERE reviewer_id = ? AND reviewed_id = ? 
                    AND request_id = ?
                ''', (reviewer_id, reviewed_id, review_data['request_id']))
            else:
                cursor.execute('''
                    SELECT review_id FROM reviews
                    WHERE reviewer_id = ? AND reviewed_id = ?
                    AND request_id IS NULL
                ''', (reviewer_id, reviewed_id))
            
            if cursor.fetchone():
                raise ValueError("Вы уже оставляли отзыв этому пользователю")
            
            cursor.execute('''
                INSERT INTO reviews (
                    reviewer_id, reviewed_id, request_id,
                    rating, comment
                ) VALUES (?, ?, ?, ?, ?)
            ''', (
                reviewer_id,
                reviewed_id,
                review_data.get('request_id'),
                review_data['rating'],
                review_data['comment']
            ))
            
            review_id = cursor.lastrowid
            conn.commit()
            return review_id
    
    def get_user_reviews(self, user_id: int, limit: int = 20) -> Dict:
        """Получает отзывы о пользователе и статистику"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Получаем отзывы
            cursor.execute('''
                SELECT r.*, u.username as reviewer_username, 
                       u.first_name as reviewer_first_name
                FROM reviews r
                JOIN users u ON r.reviewer_id = u.user_id
                WHERE r.reviewed_id = ?
                ORDER BY r.created_at DESC
                LIMIT ?
            ''', (user_id, limit))
            
            reviews = [dict(row) for row in cursor.fetchall()]
            
            # Получаем статистику
            cursor.execute('''
                SELECT 
                    COUNT(*) as total_reviews,
                    AVG(rating) as average_rating,
                    SUM(CASE WHEN rating >= 4 THEN 1 ELSE 0 END) as positive_reviews,
                    SUM(CASE WHEN rating <= 2 THEN 1 ELSE 0 END) as negative_reviews
                FROM reviews
                WHERE reviewed_id = ?
            ''', (user_id,))
            
            stats = dict(cursor.fetchone())
            stats['average_rating'] = round(stats['average_rating'] or 0, 2)
            
            return {
                'reviews': reviews,
                'stats': stats
            }
    
    def get_user_rating_stats(self, user_id: int) -> Dict:
        """Получает статистику рейтинга пользователя"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT 
                    COUNT(*) as completed_requests,
                    (SELECT COUNT(*) FROM request_applications 
                     WHERE applicant_id = ? AND status = 'accepted') as accepted_applications,
                    (SELECT COUNT(DISTINCT category) FROM help_requests 
                     WHERE user_id = ?) as categories_count
                FROM help_requests
                WHERE user_id = ? AND status = 'completed'
            ''', (user_id, user_id, user_id))
            
            stats = dict(cursor.fetchone())
            
            # Рассчитываем уровень
            completed = stats['completed_requests'] or 0
            stats['level'] = self._calculate_level(completed)
            stats['experience'] = self._calculate_experience(completed)
            
            return stats
    
    def _calculate_level(self, completed_tasks: int) -> int:
        """Рассчитывает уровень пользователя"""
        if completed_tasks == 0:
            return 1
        import math
        level = int(math.log2(completed_tasks + 1)) + 1
        return min(level, 50)
    
    def _calculate_experience(self, completed_tasks: int) -> int:
        """Рассчитывает опыт пользователя"""
        current_level = self._calculate_level(completed_tasks)
        tasks_for_current = 2 ** (current_level - 1) - 1
        tasks_for_next = 2 ** current_level - 1
        
        if tasks_for_next == tasks_for_current:
            return 100
        
        progress = (completed_tasks - tasks_for_current) / (tasks_for_next - tasks_for_current)
        return int(progress * 100)
    
    # === МЕТОДЫ ДЛЯ СООБЩЕНИЙ ===
    
    def create_message(self, sender_id: int, receiver_id: int, 
                      message_data: Dict) -> int:
        """Создает сообщение"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO messages (
                    sender_id, receiver_id, request_id,
                    message_text, message_type
                ) VALUES (?, ?, ?, ?, ?)
            ''', (
                sender_id,
                receiver_id,
                message_data.get('request_id'),
                message_data['message_text'],
                message_data.get('message_type', 'text')
            ))
            
            message_id = cursor.lastrowid
            conn.commit()
            return message_id
    
    def get_conversation_messages(self, user1_id: int, user2_id: int, 
                                 limit: int = 50) -> List[Dict]:
        """Получает сообщения между двумя пользователями"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT m.*, 
                       s.username as sender_username,
                       r.username as receiver_username
                FROM messages m
                JOIN users s ON m.sender_id = s.user_id
                JOIN users r ON m.receiver_id = r.user_id
                WHERE (m.sender_id = ? AND m.receiver_id = ?)
                   OR (m.sender_id = ? AND m.receiver_id = ?)
                ORDER BY m.created_at ASC
                LIMIT ?
            ''', (user1_id, user2_id, user2_id, user1_id, limit))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def mark_messages_as_read(self, user_id: int, sender_id: int) -> int:
        """Отмечает сообщения как прочитанные"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE messages 
                SET is_read = 1
                WHERE receiver_id = ? AND sender_id = ? AND is_read = 0
            ''', (user_id, sender_id))
            conn.commit()
            return cursor.rowcount
    
    # === МЕТОДЫ ДЛЯ УВЕДОМЛЕНИЙ ===
    
    def create_notification(self, user_id: int, notification_data: Dict) -> int:
        """Создает уведомление"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO notifications (
                    user_id, notification_type, title, message, data
                ) VALUES (?, ?, ?, ?, ?)
            ''', (
                user_id,
                notification_data['notification_type'],
                notification_data['title'],
                notification_data['message'],
                json.dumps(notification_data.get('data', {}))
            ))
            
            notification_id = cursor.lastrowid
            conn.commit()
            return notification_id
    
    def get_unread_notifications(self, user_id: int, limit: int = 20) -> List[Dict]:
        """Получает непрочитанные уведомления"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM notifications
                WHERE user_id = ? AND is_read = 0
                ORDER BY created_at DESC
                LIMIT ?
            ''', (user_id, limit))
            
            notifications = []
            for row in cursor.fetchall():
                notification = dict(row)
                notification['data'] = json.loads(notification['data']) if notification['data'] else {}
                notifications.append(notification)
            
            return notifications
    
    def mark_notification_as_read(self, notification_id: int) -> bool:
        """Отмечает уведомление как прочитанное"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE notifications SET is_read = 1
                WHERE notification_id = ?
            ''', (notification_id,))
            conn.commit()
            return cursor.rowcount > 0
    
    # === МЕТОДЫ ДЛЯ СЕССИЙ ===
    
    def save_user_session(self, user_id: int, state: str, session_data: Dict) -> int:
        """Сохраняет сессию пользователя"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Удаляем старые сессии
            cursor.execute('''
                DELETE FROM user_sessions 
                WHERE user_id = ? OR expires_at < CURRENT_TIMESTAMP
            ''', (user_id,))
            
            # Создаем новую сессию
            expires_at = datetime.now() + timedelta(hours=24)
            
            cursor.execute('''
                INSERT INTO user_sessions (
                    user_id, state, data, expires_at
                ) VALUES (?, ?, ?, ?)
            ''', (
                user_id,
                state,
                json.dumps(session_data),
                expires_at.isoformat()
            ))
            
            session_id = cursor.lastrowid
            conn.commit()
            return session_id
    
    def get_user_session(self, user_id: int) -> Optional[Dict]:
        """Получает активную сессию пользователя"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM user_sessions
                WHERE user_id = ? AND expires_at > CURRENT_TIMESTAMP
                ORDER BY created_at DESC
                LIMIT 1
            ''', (user_id,))
            
            row = cursor.fetchone()
            if row:
                session = dict(row)
                session['data'] = json.loads(session['data']) if session['data'] else {}
                return session
            return None
    
    def delete_user_session(self, user_id: int) -> bool:
        """Удаляет сессию пользователя"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM user_sessions WHERE user_id = ?', (user_id,))
            conn.commit()
            return cursor.rowcount > 0
    
    # === СТАТИСТИЧЕСКИЕ МЕТОДЫ ===
    
    def get_system_stats(self) -> Dict:
        """Получает статистику системы"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            stats = {}
            
            # Количество пользователей
            cursor.execute('SELECT COUNT(*) as count FROM users WHERE is_active = 1')
            stats['total_users'] = cursor.fetchone()['count']
            
            # Количество активных запросов
            cursor.execute('''
                SELECT COUNT(*) as count FROM help_requests 
                WHERE status = 'open' AND is_active = 1
            ''')
            stats['active_requests'] = cursor.fetchone()['count']
            
            # Количество активных предложений
            cursor.execute('''
                SELECT COUNT(*) as count FROM help_offers 
                WHERE status = 'active' AND is_active = 1
            ''')
            stats['active_offers'] = cursor.fetchone()['count']
            
            # Количество завершенных задач
            cursor.execute('''
                SELECT COUNT(*) as count FROM help_requests 
                WHERE status = 'completed'
            ''')
            stats['completed_requests'] = cursor.fetchone()['count']
            
            # Количество отзывов
            cursor.execute('SELECT COUNT(*) as count FROM reviews')
            stats['total_reviews'] = cursor.fetchone()['count']
            
            return stats
    
    def backup_database(self, backup_path: str = None) -> str:
        """Создает backup базы данных"""
        if backup_path is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = f"data/backups/backup_{timestamp}.db"
        
        os.makedirs(os.path.dirname(backup_path), exist_ok=True)
        
        import shutil
        shutil.copy2(self.db_path, backup_path)
        
        logger.info(f"Backup создан: {backup_path}")
        return backup_path

# Создаем глобальный экземпляр для использования
db_manager = DatabaseManager()