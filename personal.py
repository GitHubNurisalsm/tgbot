# personal.py
"""
Модуль для работы с личными данными пользователя и профилем
"""
import json
import os
from datetime import datetime
from typing import Dict, Any, Optional
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from states import EDIT_NAME, EDIT_AGE, EDIT_EMAIL, EDIT_PHONE  # импортируем состояния

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

def get_profile_keyboard():
    """Клавиатура для профиля"""
    keyboard = [
        [
            InlineKeyboardButton("✏️ Изменить имя", callback_data="edit_name"),
            InlineKeyboardButton("✏️ Возраст", callback_data="edit_age")
        ],
        [
            InlineKeyboardButton("✏️ Email", callback_data="edit_email"),
            InlineKeyboardButton("✏️ Телефон", callback_data="edit_phone")
        ],
        [
            InlineKeyboardButton("⚙️ Настройки", callback_data="profile_settings"),
            InlineKeyboardButton("📊 Статистика", callback_data="profile_stats")
        ],
        [
            InlineKeyboardButton("🔙 Назад", callback_data="back_to_menu")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_settings_keyboard():
    """Клавиатура настроек профиля"""
    keyboard = [
        [
            InlineKeyboardButton("🔔 Уведомления", callback_data="toggle_notifications"),
            InlineKeyboardButton("🌐 Язык", callback_data="change_language")
        ],
        [
            InlineKeyboardButton("🕐 Часовой пояс", callback_data="change_timezone"),
            InlineKeyboardButton("🗑️ Удалить данные", callback_data="delete_data")
        ],
        [
            InlineKeyboardButton("🔙 Назад в профиль", callback_data="back_to_profile")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

# Обработчики команд
async def show_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает профиль пользователя"""
    user_id = update.effective_user.id
    profile_manager = UserProfile(user_id)
    
    await update.message.reply_text(
        profile_manager.get_profile_text(),
        reply_markup=get_profile_keyboard(),
        parse_mode='Markdown'
    )

async def handle_profile_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает нажатия кнопок в профиле"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    profile_manager = UserProfile(user_id)
    
    callback_data = query.data
    
    if callback_data == "back_to_menu":
        from menu import get_main_menu_keyboard
        await query.edit_message_text(
            "Главное меню:",
            reply_markup=get_main_menu_keyboard()
        )
        return None
    
    elif callback_data == "back_to_profile":
        await query.edit_message_text(
            profile_manager.get_profile_text(),
            reply_markup=get_profile_keyboard(),
            parse_mode='Markdown'
        )
        return None
    
    elif callback_data == "profile_settings":
        await query.edit_message_text(
            "⚙️ *Настройки профиля*\n\n"
            "Выберите настройку для изменения:",
            reply_markup=get_settings_keyboard(),
            parse_mode='Markdown'
        )
        return None
    
    elif callback_data == "toggle_notifications":
        current = profile_manager.profile['settings']['notifications']
        profile_manager.update_field('notifications', not current)
        
        await query.edit_message_text(
            f"🔔 Уведомления {'включены' if not current else 'выключены'}!",
            reply_markup=get_settings_keyboard()
        )
        return None
    
    elif callback_data.startswith("edit_"):
        field = callback_data.replace("edit_", "")
        field_names = {
            'name': 'имя',
            'age': 'возраст',
            'email': 'email',
            'phone': 'телефон'
        }
        
        context.user_data['editing_field'] = field
        await query.edit_message_text(
            f"Введите новое {field_names[field]}:"
        )
        
        # Возвращаем соответствующее состояние для ConversationHandler
        state_mapping = {
            'name': EDIT_NAME,
            'age': EDIT_AGE,
            'email': EDIT_EMAIL,
            'phone': EDIT_PHONE
        }
        return state_mapping.get(field)

async def save_edited_field(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Сохраняет отредактированное поле"""
    user_id = update.effective_user.id
    profile_manager = UserProfile(user_id)
    
    field = context.user_data.get('editing_field')
    value = update.message.text
    
    if field == 'age':
        try:
            value = int(value)
            if value < 1 or value > 120:
                await update.message.reply_text("Пожалуйста, введите корректный возраст (1-120):")
                return EDIT_AGE
        except ValueError:
            await update.message.reply_text("Пожалуйста, введите число для возраста:")
            return EDIT_AGE
    
    elif field == 'email' and '@' not in value:
        await update.message.reply_text("Пожалуйста, введите корректный email:")
        return EDIT_EMAIL
    
    elif field == 'phone' and not value.replace('+', '').replace(' ', '').replace('-', '').isdigit():
        await update.message.reply_text("Пожалуйста, введите корректный номер телефона:")
        return EDIT_PHONE
    
    profile_manager.update_field(field, value)
    
    await update.message.reply_text(
        f"✅ {field.capitalize()} успешно обновлен!\n\n"
        f"{profile_manager.get_profile_text()}",
        reply_markup=get_profile_keyboard(),
        parse_mode='Markdown'
    )
    
    # Очищаем данные редактирования
    context.user_data.pop('editing_field', None)
    
    # Завершаем редактирование
    from telegram.ext import ConversationHandler
    return ConversationHandler.END

async def cancel_edit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отменяет редактирование"""
    await update.message.reply_text(
        "Редактирование отменено.",
        reply_markup=get_profile_keyboard()
    )
    
    # Очищаем данные редактирования
    context.user_data.pop('editing_field', None)
    
    from telegram.ext import ConversationHandler
    return ConversationHandler.END