# offer_help.py
"""
Модуль для системы предложения помощи и поиска помощников
"""
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes

# Константы состояний для ConversationHandler
OFFER_HELP_CATEGORY, OFFER_HELP_DESCRIPTION, OFFER_HELP_CONTACTS = range(3)
NEED_HELP_CATEGORY, NEED_HELP_DESCRIPTION, NEED_HELP_BUDGET = range(3, 6)
SEARCH_HELPERS_CATEGORY = 6

class HelpSystem:
    """Класс для управления системой помощи"""
    
    def __init__(self):
        self.offers_file = "data/help_offers.json"
        self.requests_file = "data/help_requests.json"
        self._init_data_files()
    
    def _init_data_files(self):
        """Инициализирует файлы данных, если их нет"""
        os.makedirs("data", exist_ok=True)
        
        if not os.path.exists(self.offers_file):
            with open(self.offers_file, 'w', encoding='utf-8') as f:
                json.dump([], f, ensure_ascii=False)
        
        if not os.path.exists(self.requests_file):
            with open(self.requests_file, 'w', encoding='utf-8') as f:
                json.dump([], f, ensure_ascii=False)
    
    def save_help_offer(self, user_id: int, username: str, category: str, 
                       description: str, contacts: str, tags: List[str] = None):
        """Сохраняет предложение помощи"""
        with open(self.offers_file, 'r', encoding='utf-8') as f:
            offers = json.load(f)
        
        offer = {
            'id': len(offers) + 1,
            'user_id': user_id,
            'username': username,
            'category': category,
            'description': description,
            'contacts': contacts,
            'tags': tags or [],
            'created_at': datetime.now().isoformat(),
            'is_active': True,
            'rating': 0,
            'completed_requests': 0
        }
        
        offers.append(offer)
        
        with open(self.offers_file, 'w', encoding='utf-8') as f:
            json.dump(offers, f, ensure_ascii=False, indent=2)
        
        return offer['id']
    
    def save_help_request(self, user_id: int, username: str, category: str,
                         description: str, budget: str = "Не указан"):
        """Сохраняет запрос на помощь"""
        with open(self.requests_file, 'r', encoding='utf-8') as f:
            requests = json.load(f)
        
        request = {
            'id': len(requests) + 1,
            'user_id': user_id,
            'username': username,
            'category': category,
            'description': description,
            'budget': budget,
            'created_at': datetime.now().isoformat(),
            'is_active': True,
            'status': 'new',  # new, in_progress, completed, cancelled
            'applicants': []  # user_ids of helpers who applied
        }
        
        requests.append(request)
        
        with open(self.requests_file, 'w', encoding='utf-8') as f:
            json.dump(requests, f, ensure_ascii=False, indent=2)
        
        return request['id']
    
    def get_offers_by_category(self, category: str, limit: int = 10) -> List[Dict]:
        """Получает предложения помощи по категории"""
        with open(self.offers_file, 'r', encoding='utf-8') as f:
            offers = json.load(f)
        
        filtered = [
            offer for offer in offers 
            if offer['category'] == category and offer['is_active']
        ]
        
        # Сортируем по рейтингу и дате
        filtered.sort(key=lambda x: (x['rating'], x['created_at']), reverse=True)
        
        return filtered[:limit]
    
    def get_user_offers(self, user_id: int) -> List[Dict]:
        """Получает предложения помощи пользователя"""
        with open(self.offers_file, 'r', encoding='utf-8') as f:
            offers = json.load(f)
        
        return [offer for offer in offers if offer['user_id'] == user_id]
    
    def get_user_requests(self, user_id: int) -> List[Dict]:
        """Получает запросы на помощь пользователя"""
        with open(self.requests_file, 'r', encoding='utf-8') as f:
            requests = json.load(f)
        
        return [request for request in requests if request['user_id'] == user_id]

# Создаем глобальный экземпляр системы помощи
help_system = HelpSystem()

# Категории помощи
HELP_CATEGORIES = {
    "it": "💻 IT и программирование",
    "design": "🎨 Дизайн и графика",
    "other": "🔧 Другое"
}

# Клавиатуры
def get_help_main_keyboard():
    """Основная клавиатура раздела помощи"""
    keyboard = [
        [KeyboardButton("🤝 Предложить помощь"), KeyboardButton("🆘 Нужна помощь")],
        [KeyboardButton("🔍 Найти помощников"), KeyboardButton("📋 Мои предложения")],
        [KeyboardButton("📄 Мои запросы"), KeyboardButton("⭐ Рейтинг помощников")],
        [KeyboardButton("🔙 Назад")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)

def get_categories_keyboard():
    """Клавиатура с категориями помощи"""
    keyboard = []
    categories = list(HELP_CATEGORIES.values())
    
    # Разбиваем на пары кнопок
    for i in range(0, len(categories), 2):
        row = categories[i:i+2]
        keyboard.append([KeyboardButton(cat) for cat in row])
    
    keyboard.append([KeyboardButton("🔙 Назад")])
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

def get_offer_keyboard(offer_id: int):
    """Inline-клавиатура для предложения помощи"""
    keyboard = [
        [
            InlineKeyboardButton("📨 Откликнуться", callback_data=f"respond_offer_{offer_id}"),
            InlineKeyboardButton("⭐ Оценить", callback_data=f"rate_offer_{offer_id}")
        ],
        [
            InlineKeyboardButton("👤 Профиль", callback_data=f"view_profile_offer_{offer_id}"),
            InlineKeyboardButton("🚫 Пожаловаться", callback_data=f"report_offer_{offer_id}")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

# Обработчики команд
async def show_help_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает меню помощи"""
    await update.message.reply_text(
        "🤝 *Помощь и взаимопомощь*\n\n"
        "Здесь вы можете:\n"
        "• Предложить свою помощь другим\n"
        "• Найти помощь для своих задач\n"
        "• Найти исполнителей для проектов\n\n"
        "Выберите действие:",
        reply_markup=get_help_main_keyboard(),
        parse_mode='Markdown'
    )

async def start_offer_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начинает процесс предложения помощи"""
    await update.message.reply_text(
        "🎉 *Предложение помощи*\n\n"
        "Выберите категорию, в которой можете помочь:",
        reply_markup=get_categories_keyboard(),
        parse_mode='Markdown'
    )
    return OFFER_HELP_CATEGORY

async def process_offer_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает выбор категории для предложения помощи"""
    category_name = update.message.text
    category_key = None
    
    # Находим ключ категории по названию
    for key, value in HELP_CATEGORIES.items():
        if value == category_name:
            category_key = key
            break
    
    if not category_key:
        await update.message.reply_text(
            "Пожалуйста, выберите категорию из списка:",
            reply_markup=get_categories_keyboard()
        )
        return OFFER_HELP_CATEGORY
    
    context.user_data['offer_category'] = category_key
    context.user_data['offer_category_name'] = category_name
    
    await update.message.reply_text(
        f"📝 *Категория: {category_name}*\n\n"
        "Теперь опишите, какую именно помощь вы можете оказать:\n"
        "• Ваши навыки и опыт\n"
        "• Примеры работ (если есть)\n"
        "• Время, которое можете уделить\n"
        "• Формат помощи (онлайн, офлайн)\n\n"
        "*Важно:* Будьте конкретны и честны!",
        parse_mode='Markdown',
        reply_markup=ReplyKeyboardMarkup([["🔙 Назад"]], resize_keyboard=True)
    )
    return OFFER_HELP_DESCRIPTION

async def process_offer_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает описание помощи"""
    if update.message.text == "🔙 Назад":
        await update.message.reply_text(
            "Выберите категорию:",
            reply_markup=get_categories_keyboard()
        )
        return OFFER_HELP_CATEGORY
    
    context.user_data['offer_description'] = update.message.text
    
    await update.message.reply_text(
        "📞 *Контактная информация*\n\n"
        "Как с вами можно связаться?\n"
        "• Telegram username\n"
        "• Email\n"
        "• Номер телефона (по желанию)\n"
        "• Другие способы связи\n\n"
        "*Примечание:* Эти данные будут видны только тем, "
        "кто откликнется на ваше предложение.",
        parse_mode='Markdown',
        reply_markup=ReplyKeyboardMarkup([["🔙 Назад"]], resize_keyboard=True)
    )
    return OFFER_HELP_CONTACTS

async def process_offer_contacts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Завершает создание предложения помощи"""
    if update.message.text == "🔙 Назад":
        await update.message.reply_text(
            "Опишите вашу помощь:",
            reply_markup=ReplyKeyboardMarkup([["🔙 Назад"]], resize_keyboard=True)
        )
        return OFFER_HELP_DESCRIPTION
    
    user = update.effective_user
    contacts = update.message.text
    
    # Сохраняем предложение в offers.json
    offer_id = help_system.save_help_offer(
        user_id=user.id,
        username=user.username or user.first_name,
        category=context.user_data['offer_category_name'],
        description=context.user_data['offer_description'],
        contacts=contacts,
        tags=[context.user_data['offer_category']]
    )
    
    # Импортим request_system и создаем запись в help_requests (чтобы попасть в "📋 Активные заявки")
    try:
        from need_help import request_system
        # Преобразуем категорию в понятный формат и создаём аналогичный запрос (is_offer=True)
        request_id = request_system.save_request(
            user_id=user.id,
            username=user.username or user.first_name,
            category=context.user_data['offer_category_name'],
            description=context.user_data['offer_description'],
            budget="Не указан",
            deadline="Не указан",
            contacts=contacts,
            is_offer=True,
            related_offer_id=offer_id  # связь между offer и request
        )
    except Exception:
        request_id = None
    
    # Очищаем временные данные
    context.user_data.clear()
    
    created_text = (
        f"✅ *Предложение помощи опубликовано!*\n\n"
        f"🎯 Категория: {context.user_data.get('offer_category_name', '')}\n"
        f"🆔 ID предложения: #{offer_id}\n"
    )
    if request_id:
        created_text += f"🆔 Оно также добавлено в список активных заявок: #{request_id}\n\n"
    
    created_text += "Теперь другие пользователи смогут найти ваше предложение и откликнуться!"
    
    await update.message.reply_text(
        created_text,
        parse_mode='Markdown',
        reply_markup=get_help_main_keyboard()
    )
    
    from telegram.ext import ConversationHandler
    return ConversationHandler.END

async def search_helpers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начинает поиск помощников"""
    await update.message.reply_text(
        "🔍 *Поиск помощников*\n\n"
        "Выберите категорию для поиска:",
        reply_markup=get_categories_keyboard(),
        parse_mode='Markdown'
    )
    return SEARCH_HELPERS_CATEGORY

async def show_helpers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает помощников в выбранной категории"""
    category_name = update.message.text
    
    # Проверяем, что категория валидна
    if category_name not in HELP_CATEGORIES.values():
        await update.message.reply_text(
            "Пожалуйста, выберите категорию из списка:",
            reply_markup=get_categories_keyboard()
        )
        return SEARCH_HELPERS_CATEGORY
    
    # Находим ключ категории
    category_key = None
    for key, value in HELP_CATEGORIES.items():
        if value == category_name:
            category_key = key
            break
    
    # Получаем предложения
    offers = help_system.get_offers_by_category(category_name)
    
    if not offers:
        await update.message.reply_text(
            f"😔 В категории *{category_name}* пока нет активных предложений.\n\n"
            f"Попробуйте:\n"
            f"• Выбрать другую категорию\n"
            f"• Опубликовать свой запрос на помощь\n"
            f"• Зайти позже",
            parse_mode='Markdown',
            reply_markup=get_help_main_keyboard()
        )
        from telegram.ext import ConversationHandler
        return ConversationHandler.END
    
    await update.message.reply_text(
        f"🔍 *Найдено предложений: {len(offers)}*\n\n"
        f"Категория: {category_name}\n"
        f"Для просмотра деталей нажмите на кнопку под предложением.",
        parse_mode='Markdown',
        reply_markup=get_help_main_keyboard()
    )
    
    # Показываем первые 3 предложения
    for i, offer in enumerate(offers[:3], 1):
        offer_text = (
            f"📋 *Предложение #{offer['id']}*\n"
            f"👤 {offer['username']}\n"
            f"⭐ Рейтинг: {offer['rating']}/5\n"
            f"✅ Выполнено: {offer['completed_requests']}\n\n"
            f"{offer['description'][:200]}...\n\n"
            f"📅 Опубликовано: "
            f"{datetime.fromisoformat(offer['created_at']).strftime('%d.%m.%Y')}"
        )
        
        await update.message.reply_text(
            offer_text,
            reply_markup=get_offer_keyboard(offer['id']),
            parse_mode='Markdown'
        )
    
    if len(offers) > 3:
        await update.message.reply_text(
            f"И еще {len(offers) - 3} предложений...\n"
            f"Используйте поиск снова для просмотра остальных.",
            reply_markup=get_help_main_keyboard()
        )
    
    from telegram.ext import ConversationHandler
    return ConversationHandler.END

async def show_my_offers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает предложения помощи пользователя"""
    user_id = update.effective_user.id
    offers = help_system.get_user_offers(user_id)
    
    if not offers:
        await update.message.reply_text(
            "📭 *У вас пока нет предложений помощи*\n\n"
            "Хотите предложить свою помощь? Нажмите '🤝 Предложить помощь'",
            parse_mode='Markdown',
            reply_markup=get_help_main_keyboard()
        )
        return
    
    await update.message.reply_text(
        f"📋 *Ваши предложения помощи: {len(offers)}*\n\n"
        "👇 Выберите предложение для просмотра:",
        parse_mode='Markdown'
    )
    
    for offer in offers:
        status = "✅ Активно" if offer['is_active'] else "⏸️ Неактивно"
        
        offer_text = (
            f"📋 *Предложение #{offer['id']}*\n"
            f"🎯 Категория: {offer['category']}\n"
            f"📅 {datetime.fromisoformat(offer['created_at']).strftime('%d.%m.%Y')}\n"
            f"⭐ Рейтинг: {offer['rating']}\n"
            f"✅ Выполнено: {offer['completed_requests']}\n"
            f"📊 Статус: {status}\n\n"
            f"📝 Описание:\n{offer['description'][:150]}..."
        )
        
        keyboard = [
            [
                InlineKeyboardButton(
                    "✅ Активировать" if not offer['is_active'] else "⏸️ Деактивировать",
                    callback_data=f"toggle_offer_{offer['id']}"
                ),
                InlineKeyboardButton("✏️ Редактировать", callback_data=f"edit_offer_{offer['id']}")
            ],
            [
                InlineKeyboardButton("🗑️ Удалить", callback_data=f"delete_offer_{offer['id']}"),
                InlineKeyboardButton("📊 Статистика", callback_data=f"stats_offer_{offer['id']}")
            ]
        ]
        
        await update.message.reply_text(
            offer_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )

async def cancel_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отменяет процесс помощи"""
    await update.message.reply_text(
        "Действие отменено.",
        reply_markup=get_help_main_keyboard()
    )
    
    # Очищаем временные данные
    context.user_data.clear()
    
    from telegram.ext import ConversationHandler
    return ConversationHandler.END

# Обработчик callback-запросов
async def handle_help_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает нажатия inline-кнопок"""
    query = update.callback_query
    await query.answer()
    
    callback_data = query.data
    
    if callback_data.startswith("respond_offer_"):
        offer_id = int(callback_data.replace("respond_offer_", ""))
        await query.edit_message_text(
            f"📨 *Отклик на предложение #{offer_id}*\n\n"
            "Чтобы откликнуться, свяжитесь с автором предложения напрямую "
            "по указанным им контактам.\n\n"
            "*Совет:* Будьте вежливы и конкретны в своем обращении!",
            parse_mode='Markdown'
        )
    
    elif callback_data.startswith("toggle_offer_"):
        offer_id = int(callback_data.replace("toggle_offer_", ""))
        # Здесь нужно добавить логику переключения статуса предложения
        await query.edit_message_text(
            f"✅ Статус предложения #{offer_id} изменен!",
            parse_mode='Markdown'
        )