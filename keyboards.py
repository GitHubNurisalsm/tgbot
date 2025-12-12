# keyboards.py - Исправленная версия
from telegram import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

# ===== REPLY КЛАВИАТУРЫ (текстовые кнопки) =====

def get_start_keyboard():
    """Клавиатура для начала (не зарегистрирован)"""
    keyboard = [
        [KeyboardButton("🚀 Регистрация"), KeyboardButton("🔐 Вход")],
        [KeyboardButton("ℹ️ О проекте"), KeyboardButton("❓ FAQ")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)

def get_main_menu_keyboard():
    """Главное меню (зарегистрирован)"""
    keyboard = [
        [KeyboardButton("🙋‍♂️ Предложить помощь"), KeyboardButton("🙏 Попросить помощи")],
        [KeyboardButton("👤 Личный кабинет"), KeyboardButton("⭐ Рейтинг")],
        [KeyboardButton("📋 Активные заявки"), KeyboardButton("📞 Поддержка")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)

def get_back_button():
    """Кнопка "Назад" """
    return ReplyKeyboardMarkup(
        [[KeyboardButton("🔙 Назад")]],
        resize_keyboard=True
    )

def get_confirmation_keyboard():
    """Подтверждение (Да/Нет)"""
    keyboard = [
        [KeyboardButton("✅ Да"), KeyboardButton("❌ Нет")],
        [KeyboardButton("🔙 Назад")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

def get_categories_keyboard():
    """Категории помощи"""
    keyboard = [
        [KeyboardButton("💻 IT и программирование"), KeyboardButton("🎨 Дизайн")],
        [KeyboardButton("📝 Тексты и переводы"), KeyboardButton("📊 Маркетинг")],
        [KeyboardButton("🎓 Обучение"), KeyboardButton("🔧 Разное")],
        [KeyboardButton("🔙 Назад")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

def get_help_keyboard():
    """Клавиатура помощи"""
    keyboard = [
        [KeyboardButton("📖 Инструкция"), KeyboardButton("❓ FAQ")],
        [KeyboardButton("📞 Связаться"), KeyboardButton("🔙 Назад")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

# ===== INLINE КЛАВИАТУРЫ (кнопки в сообщениях) =====

def get_yes_no_keyboard():
    """Inline кнопки Да/Нет"""
    keyboard = [
        [
            InlineKeyboardButton("✅ Да", callback_data="yes"),
            InlineKeyboardButton("❌ Нет", callback_data="no")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_profile_keyboard():
    """Кнопки для профиля"""
    keyboard = [
        [
            InlineKeyboardButton("✏️ Редактировать", callback_data="edit_profile"),
            InlineKeyboardButton("📊 Статистика", callback_data="profile_stats")
        ],
        [InlineKeyboardButton("🔙 В меню", callback_data="back_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)