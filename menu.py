# menu.py
from telegram import ReplyKeyboardMarkup, KeyboardButton

def get_main_menu_keyboard():
    """Основное меню бота"""
    keyboard = [
        [KeyboardButton("📝 Регистрация"), KeyboardButton("ℹ️ О проекте")],
        [KeyboardButton("❓ Помощь"), KeyboardButton("📞 Поддержка")],
        [KeyboardButton("👤 Профиль"), KeyboardButton("⚙️ Настройки")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)

def get_registration_keyboard():
    """Клавиатура для регистрации"""
    keyboard = [
        [KeyboardButton("✅ Начать регистрацию")],
        [KeyboardButton("🔙 Назад в меню")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

def get_back_to_menu_keyboard():
    """Простая кнопка возврата в меню"""
    keyboard = [
        [KeyboardButton("🔙 Назад")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

def get_confirmation_keyboard():
    """Клавиатура подтверждения"""
    keyboard = [
        [KeyboardButton("✅ Да"), KeyboardButton("❌ Нет")],
        [KeyboardButton("🔙 Назад в меню")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

def get_profile_keyboard():
    """Клавиатура профиля"""
    keyboard = [
        [KeyboardButton("✏️ Редактировать профиль"), KeyboardButton("📊 Статистика")],
        [KeyboardButton("🔙 Назад в меню")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

def get_settings_keyboard():
    """Клавиатура настроек"""
    keyboard = [
        [KeyboardButton("🔔 Уведомления"), KeyboardButton("🌐 Язык")],
        [KeyboardButton("🔙 Назад в меню")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

def get_help_keyboard():
    """Клавиатура помощи"""
    keyboard = [
        [KeyboardButton("📖 Инструкция"), KeyboardButton("❓ FAQ")],
        [KeyboardButton("📞 Связаться"), KeyboardButton("🔙 Назад в меню")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

def get_contact_keyboard():
    """Клавиатура с контактами"""
    keyboard = [
        [KeyboardButton("📧 Email"), KeyboardButton("📱 Телефон")],
        [KeyboardButton("🌐 Веб-сайт"), KeyboardButton("🔙 Назад в меню")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

# Функции для проверки, какая кнопка была нажата
def is_back_to_menu(text: str) -> bool:
    """Проверяет, нажата ли кнопка возврата в меню"""
    return text in ["🔙 Назад", "🔙 Назад в меню", "Назад", "Вернуться в меню", "Меню"]

def is_registration(text: str) -> bool:
    """Проверяет, нажата ли кнопка регистрации"""
    return text in ["📝 Регистрация", "Регистрация", "Зарегистрироваться"]

def is_about(text: str) -> bool:
    """Проверяет, нажата ли кнопка 'О проекте'"""
    return text in ["ℹ️ О проекте", "О проекте", "0 проекте"]

def is_help(text: str) -> bool:
    """Проверяет, нажата ли кнопка помощи"""
    return text in ["❓ Помощь", "Помощь", "Помощь проекту"]

def is_support(text: str) -> bool:
    """Проверяет, нажата ли кнопка поддержки"""
    return text in ["📞 Поддержка", "Поддержка", "Контакты"]

def is_profile(text: str) -> bool:
    """Проверяет, нажата ли кнопка профиля"""
    return text in ["👤 Профиль", "Профиль", "Мой профиль"]

def is_settings(text: str) -> bool:
    """Проверяет, нажата ли кнопка настроек"""
    return text in ["⚙️ Настройки", "Настройки"]