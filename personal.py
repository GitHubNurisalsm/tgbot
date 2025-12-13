# personal.py
"""
Модуль для работы с личными данными пользователя и профилем
"""
import json
import os
import logging
from datetime import datetime
from typing import Dict, Any, Optional

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

from keyboards import get_profile_keyboard, get_main_menu_keyboard
from states import EDIT_NAME, EDIT_AGE, EDIT_EMAIL, EDIT_PHONE  # импортируем состояния

logger = logging.getLogger(__name__)

def _read_user_from_file(telegram_id: str) -> Optional[dict]:
    users_path = os.path.join("data", "users.json")
    if not os.path.exists(users_path):
        return None
    try:
        with open(users_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data.get(str(telegram_id))
    except Exception:
        return None

def _save_user_to_file(telegram_id: str, user_data: dict):
    users_path = os.path.join("data", "users.json")
    os.makedirs(os.path.dirname(users_path), exist_ok=True)
    try:
        existing = {}
        if os.path.exists(users_path):
            with open(users_path, 'r', encoding='utf-8') as f:
                txt = f.read().strip()
                existing = json.loads(txt) if txt else {}
        existing[str(telegram_id)] = user_data
        with open(users_path, 'w', encoding='utf-8') as f:
            json.dump(existing, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Ошибка записи профиля в файл: {e}", exc_info=True)

class UserProfile:
    """Класс для управления профилем пользователя"""
    
    def __init__(self, user_id: int):
        self.user_id = user_id
        self.data_file = f"data/users/{user_id}.json"
        self.profile = self._load_profile()
    
    def _load_profile(self) -> Dict[str, Any]:
        """Загружает профиль пользователя из файла"""
        os.makedirs("data/users", exist_ok=True)
        
        if os.path.exists(self.data_file):
            with open(self.data_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        # Создаем новый профиль
        default_profile = {
            'user_id': self.user_id,
            'name': '',
            'age': None,
            'email': '',
            'phone': '',
            'registration_date': datetime.now().isoformat(),
            'last_active': datetime.now().isoformat(),
            'is_active': True,
            'settings': {
                'notifications': True,
                'language': 'ru',
                'timezone': 'UTC+3'
            }
        }
        
        self._save_profile(default_profile)
        return default_profile
    
    def _save_profile(self, profile: Dict[str, Any]) -> None:
        """Сохраняет профиль пользователя в файл"""
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(profile, f, ensure_ascii=False, indent=2)
    
    def update_field(self, field: str, value: Any) -> None:
        """Обновляет поле в профиле"""
        if field in self.profile:
            self.profile[field] = value
        elif field in self.profile.get('settings', {}):
            self.profile['settings'][field] = value
        
        self.profile['last_active'] = datetime.now().isoformat()
        self._save_profile(self.profile)
    
    def get_profile_text(self) -> str:
        """Возвращает текстовое представление профиля"""
        profile = self.profile
        settings = profile.get('settings', {})
        
        text = f"👤 *Ваш профиль*\n\n"
        text += f"🆔 ID: `{profile['user_id']}`\n"
        
        if profile['name']:
            text += f"👤 Имя: {profile['name']}\n"
        else:
            text += f"👤 Имя: *не указано*\n"
            
        if profile['age']:
            text += f"🎂 Возраст: {profile['age']}\n"
        else:
            text += f"🎂 Возраст: *не указан*\n"
            
        if profile['email']:
            text += f"📧 Email: {profile['email']}\n"
        else:
            text += f"📧 Email: *не указан*\n"
            
        if profile['phone']:
            text += f"📱 Телефон: {profile['phone']}\n"
        else:
            text += f"📱 Телефон: *не указан*\n"
        
        text += f"\n📅 *Дата регистрации:*\n"
        text += f"   {datetime.fromisoformat(profile['registration_date']).strftime('%d.%m.%Y %H:%M')}\n"
        
        text += f"\n⚙️ *Настройки:*\n"
        text += f"   Уведомления: {'✅ Вкл' if settings.get('notifications') else '❌ Выкл'}\n"
        text += f"   Язык: {settings.get('language', 'ru')}\n"
        text += f"   Часовой пояс: {settings.get('timezone', 'UTC+3')}"
        
        return text
    
    def is_complete(self) -> bool:
        """Проверяет, заполнен ли профиль полностью"""
        required_fields = ['name', 'age', 'email']
        return all(self.profile.get(field) for field in required_fields)

# Обработчики команд
async def show_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает личный кабинет — берёт данные из DB или файла"""
    user = update.effective_user
    if not user:
        return

    telegram_id = str(user.id)
    user_data = None
    try:
        from database import db
        if hasattr(db, "get_user_by_telegram_id"):
            user_data = db.get_user_by_telegram_id(int(telegram_id))
    except Exception:
        user_data = None

    if not user_data:
        user_data = _read_user_from_file(telegram_id) or {}

    profile_text = (
        f"👤 Личный кабинет\n\n"
        f"📛 Имя: {user_data.get('full_name', 'Не указано')}\n"
        f"📧 Email: {user_data.get('email', 'Не указан')}\n"
        f"📱 Телефон: {user_data.get('phone', 'Не указан')}\n"
        f"⭐ Рейтинг: {user_data.get('rating', 5.0)}/5.0\n"
        f"🙋 Помогли: {user_data.get('help_offered_count', 0)} раз\n"
        f"🙏 Получили: {user_data.get('help_received_count', 0)} раз\n\n"
        f"Вы можете редактировать профиль кнопкой ниже."
    )
    # Показываем профиль с inline-кнопками для редактирования и главным меню
    await update.message.reply_text(profile_text, reply_markup=get_profile_keyboard())
    await update.message.reply_text("Выберите действие:", reply_markup=get_main_menu_keyboard())

async def handle_profile_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка callback'ов профиля: edit_profile, profile_stats"""
    query = update.callback_query
    if not query or not query.data:
        return
    await query.answer()
    action = query.data

    if action == "edit_profile":
        # Начинаем редактирование - спросим новое имя (как пример)
        await query.message.reply_text("Введите новое имя (Фамилия Имя):")
        context.user_data['edit_field'] = 'full_name'
        return EDIT_NAME
    elif action == "profile_stats":
        user = update.effective_user
        telegram_id = str(user.id)
        # Получаем профиль и показываем статистику
        user_data = None
        try:
            from database import db
            if hasattr(db, "get_user_by_telegram_id"):
                user_data = db.get_user_by_telegram_id(int(telegram_id))
        except Exception:
            user_data = None
        if not user_data:
            user_data = _read_user_from_file(telegram_id) or {}

        stats_text = (
            f"📊 Статистика профиля\n\n"
            f"🙋 Помогли: {user_data.get('help_offered_count', 0)} раз\n"
            f"🙏 Получили: {user_data.get('help_received_count', 0)} раз\n"
            f"⭐ Рейтинг: {user_data.get('rating', 5.0)}/5.0\n"
        )
        await query.message.reply_text(stats_text, reply_markup=get_main_menu_keyboard())
        return None
    else:
        await query.message.reply_text("Неизвестное действие.")
        return None

async def save_edited_field(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Сохраняет редактируемое поле"""
    text = (update.message.text or "").strip()
    if not text:
        await update.message.reply_text("Текст не распознан, попробуйте снова.")
        return EDIT_NAME  # оставим в том же стейте по умолчанию

    telegram_id = str(update.effective_user.id)
    # вытянуть редактируемое поле
    field = context.user_data.get('edit_field', 'full_name')

    # подготовить сохранение
    try:
        from database import db
        if hasattr(db, "create_or_update_user"):
            # получаем существующие данные для обновления
            existing = db.get_user_by_telegram_id(int(telegram_id)) or {}
            existing[field] = text
            db.create_or_update_user(existing)
            await update.message.reply_text("✅ Данные обновлены.", reply_markup=get_main_menu_keyboard())
            context.user_data.pop('edit_field', None)
            return -1
    except Exception:
        # fallback к файлу
        user_data = _read_user_from_file(telegram_id) or {}
        user_data[field] = text
        _save_user_to_file(telegram_id, user_data)
        await update.message.reply_text("✅ Данные обновлены.", reply_markup=get_main_menu_keyboard())
        context.user_data.pop('edit_field', None)
        return -1

async def cancel_edit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отмена редактирования (через /cancel)"""
    context.user_data.pop('edit_field', None)
    await update.message.reply_text("Редактирование отменено.", reply_markup=get_main_menu_keyboard())
    return -1