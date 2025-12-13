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
        [KeyboardButton("✅ Начать регистрацию")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

def get_back_to_menu_keyboard():
    """Простая кнопка возврата в меню убрана (функцию оставляю, но без кнопки)"""
    keyboard = []
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

def get_confirmation_keyboard():
    """Клавиатура подтверждения"""
    keyboard = [
        [KeyboardButton("✅ Да"), KeyboardButton("❌ Нет")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

def get_profile_keyboard():
    """Клавиатура профиля - убрал кнопку 'Назад в меню'"""
    keyboard = [
        [KeyboardButton("✏️ Редактировать профиль"), KeyboardButton("📊 Статистика")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

def get_settings_keyboard():
    """Клавиатура настроек - убрал кнопку 'Назад в меню'"""
    keyboard = [
        [KeyboardButton("🔔 Уведомления"), KeyboardButton("🌐 Язык")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

def get_help_keyboard():
    """Клавиатура помощи"""
    keyboard = [
        [KeyboardButton("📖 Инструкция"), KeyboardButton("❓ FAQ")],
        [KeyboardButton("📞 Связаться")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

# Функции для проверки, какая кнопка была нажата
def is_back_to_menu(text: str) -> bool:
    """Проверяет, была ли команда возврата в меню"""
    # Без текстовой кнопки "🔙 Назад" — поддерживаем только другие варианты (например, команды)
    return text in ["Меню", "Вернуться в меню", "/menu"]

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

def is_offer(text: str) -> bool:
    """Проверяет, нажата ли кнопка 'Предложить помощь'"""
    t = (text or "").lower()
    return "предлож" in t and "помощ" in t

def is_need_help(text: str) -> bool:
    """Проверяет, нажата ли кнопка 'Попросить помощи' / 'Создать запрос'"""
    t = (text or "").lower()
    return "попрос" in t or "создать запрос" in t or "искат" in t or "запрос" in t

def is_requests(text: str) -> bool:
    """Проверяет, нажата ли кнопка 'Активные заявки'"""
    t = (text or "").lower()
    return "актив" in t or "заяв" in t