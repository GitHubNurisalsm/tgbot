# need_help.py
"""
Модуль для системы запросов помощи - пользователи могут просить о помощи
"""
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes
import logging

logger = logging.getLogger(__name__)

# Константы состояний для ConversationHandler
# Явно задаем коды, добавляем REQUEST_CONTACTS
REQUEST_CATEGORY = 10
REQUEST_DESCRIPTION = 11
REQUEST_BUDGET = 12
REQUEST_DEADLINE = 13
REQUEST_CONTACTS = 14
APPLY_FOR_REQUEST = 15
SEND_APPLICATION = 16

class RequestHelpSystem:
    """Класс для управления системой запросов помощи"""
    
    def __init__(self):
        self.requests_file = "data/help_requests.json"
        self.applications_file = "data/help_applications.json"
        self._init_data_files()
    
    def _init_data_files(self):
        """Инициализирует файлы данных, если их нет"""
        os.makedirs("data", exist_ok=True)
        
        if not os.path.exists(self.requests_file):
            with open(self.requests_file, 'w', encoding='utf-8') as f:
                json.dump([], f, ensure_ascii=False)
        
        if not os.path.exists(self.applications_file):
            with open(self.applications_file, 'w', encoding='utf-8') as f:
                json.dump([], f, ensure_ascii=False)
    
    def save_request(self, user_id: int, username: str, category: str, 
                    description: str, budget: str = "Не указан", 
                    deadline: str = "Не указан", contacts: str = None,
                    is_offer: bool = False, related_offer_id: int = None) -> int:
        """Сохраняет запрос на помощь (включая привязку к offer при is_offer=True)"""
        with open(self.requests_file, 'r', encoding='utf-8') as f:
            requests = json.load(f)
        
        request = {
            'id': len(requests) + 1,
            'user_id': user_id,
            'username': username,
            'category': category,
            'description': description,
            'budget': budget,
            'deadline': deadline,
            'contacts': contacts,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'is_active': True,
            'status': 'open',  # open, in_progress, completed, cancelled
            'applications_count': 0,
            'selected_applicant': None,
            'tags': self._extract_tags(description),
            'is_offer': bool(is_offer),
            'related_offer_id': related_offer_id
        }
        
        requests.append(request)
        
        with open(self.requests_file, 'w', encoding='utf-8') as f:
            json.dump(requests, f, ensure_ascii=False, indent=2)
        
        return request['id']
    
    def _extract_tags(self, description: str) -> List[str]:
        """Извлекает теги из описания"""
        common_tags = ['срочно', 'срочный', 'urgent', 'быстро', 'опыт', 
                      'новичок', 'beginner', 'профессионал', 'online', 
                      'онлайн', 'офлайн', 'offline']
        
        tags = []
        words = description.lower().split()
        
        for word in words:
            clean_word = word.strip('.,!?;:')
            if clean_word in common_tags:
                tags.append(clean_word)
        
        return list(set(tags))  # Убираем дубли
    
    def get_requests_by_category(self, category: str, limit: int = 15) -> List[Dict]:
        """Получает запросы по категории"""
        with open(self.requests_file, 'r', encoding='utf-8') as f:
            requests = json.load(f)
        
        filtered = [
            req for req in requests 
            if req['category'] == category and req['is_active'] and req['status'] == 'open'
        ]
        
        # Сортируем по дате (сначала новые)
        filtered.sort(key=lambda x: x['created_at'], reverse=True)
        
        return filtered[:limit]
    
    def get_request_by_id(self, request_id: int) -> Optional[Dict]:
        """Получает запрос по ID"""
        with open(self.requests_file, 'r', encoding='utf-8') as f:
            requests = json.load(f)
        
        for request in requests:
            if request['id'] == request_id:
                return request
        
        return None
    
    def get_user_requests(self, user_id: int) -> List[Dict]:
        """Получает запросы пользователя"""
        with open(self.requests_file, 'r', encoding='utf-8') as f:
            requests = json.load(f)
        
        return [req for req in requests if req['user_id'] == user_id]
    
    def save_application(self, request_id: int, applicant_id: int, 
                        applicant_username: str, message: str, 
                        price: str = None, timeline: str = None) -> int:
        """Сохраняет заявку на выполнение запроса"""
        with open(self.applications_file, 'r', encoding='utf-8') as f:
            applications = json.load(f)
        
        application = {
            'id': len(applications) + 1,
            'request_id': request_id,
            'applicant_id': applicant_id,
            'applicant_username': applicant_username,
            'message': message,
            'price': price,
            'timeline': timeline,
            'created_at': datetime.now().isoformat(),
            'status': 'pending',  # pending, accepted, rejected
            'is_active': True
        }
        
        applications.append(application)
        
        with open(self.applications_file, 'w', encoding='utf-8') as f:
            json.dump(applications, f, ensure_ascii=False, indent=2)
        
        # Увеличиваем счетчик заявок в запросе
        self._increment_applications_count(request_id)
        
        return application['id']
    
    def _increment_applications_count(self, request_id: int):
        """Увеличивает счетчик заявок для запроса"""
        with open(self.requests_file, 'r', encoding='utf-8') as f:
            requests = json.load(f)
        
        for request in requests:
            if request['id'] == request_id:
                request['applications_count'] += 1
                request['updated_at'] = datetime.now().isoformat()
                break
        
        with open(self.requests_file, 'w', encoding='utf-8') as f:
            json.dump(requests, f, ensure_ascii=False, indent=2)
    
    def get_applications_for_request(self, request_id: int) -> List[Dict]:
        """Получает заявки для запроса"""
        with open(self.applications_file, 'r', encoding='utf-8') as f:
            applications = json.load(f)
        
        return [app for app in applications if app['request_id'] == request_id and app['is_active']]
    
    def get_user_applications(self, user_id: int) -> List[Dict]:
        """Получает заявки пользователя"""
        with open(self.applications_file, 'r', encoding='utf-8') as f:
            applications = json.load(f)
        
        return [app for app in applications if app['applicant_id'] == user_id]
    
    def get_all_active_requests(self, limit: int = 20) -> List[Dict]:
        """Возвращает последние активные запросы (status='open')"""
        with open(self.requests_file, 'r', encoding='utf-8') as f:
            requests = json.load(f)
        
        filtered = [req for req in requests if req.get('is_active', False) and req.get('status') == 'open']
        # сортируем по дате создания (последние первыми)
        filtered.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        return filtered[:limit]

# Создаем глобальный экземпляр системы
request_system = RequestHelpSystem()

# Категории запросов (можно синхронизировать с offer_help.py)
REQUEST_CATEGORIES = {
    "programming": "💻 Программирование",
    "design": "🎨 Дизайн",
    "writing": "📝 Копирайтинг",
    "translation": "🌐 Переводы",
    "marketing": "📊 Маркетинг",
    "consulting": "🗣️ Консультации",
    "tutoring": "🎓 Обучение",
    "other": "🔧 Разное"
}

# Бюджетные диапазоны
BUDGET_OPTIONS = [
    "💰 Бюджет не указан",
    "💵 До 1 000 ₽",
    "💵 1 000 - 5 000 ₽",
    "💵 5 000 - 15 000 ₽",
    "💵 15 000 - 50 000 ₽",
    "💵 50 000 ₽ и более",
    "💵 Договорная цена"
]

# Сроки выполнения
DEADLINE_OPTIONS = [
    "⏰ Срок не важен",
    "⚡ Срочно (до 24 часов)",
    "🚀 До 3 дней",
    "📅 До недели",
    "📅 До 2 недель",
    "📅 До месяца",
    "📅 Более месяца"
]

# Клавиатуры
def get_need_help_main_keyboard():
    """Основная клавиатура раздела 'Нужна помощь'"""
    keyboard = [
        [KeyboardButton("➕ Создать запрос"), KeyboardButton("🔍 Искать запросы")],
        [KeyboardButton("📋 Мои запросы"), KeyboardButton("📨 Мои отклики")],
        [KeyboardButton("⭐ Избранное"), KeyboardButton("🏆 Топ исполнителей")],
        [KeyboardButton("🔙 Назад")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)

def get_request_categories_keyboard():
    """Клавиатура категорий для запросов"""
    keyboard = []
    categories = list(REQUEST_CATEGORIES.values())
    
    for i in range(0, len(categories), 2):
        row = categories[i:i+2]
        keyboard.append([KeyboardButton(cat) for cat in row])
    
    keyboard.append([KeyboardButton("🔙 Назад")])
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

def get_budget_keyboard():
    """Клавиатура выбора бюджета"""
    keyboard = []
    
    for i in range(0, len(BUDGET_OPTIONS), 2):
        row = BUDGET_OPTIONS[i:i+2]
        keyboard.append([KeyboardButton(opt) for opt in row])
    
    keyboard.append([KeyboardButton("🔙 Назад")])
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

def get_deadline_keyboard():
    """Клавиатура выбора срока"""
    keyboard = []
    
    for i in range(0, len(DEADLINE_OPTIONS), 2):
        row = DEADLINE_OPTIONS[i:i+2]
        keyboard.append([KeyboardButton(opt) for opt in row])
    
    keyboard.append([KeyboardButton("🔙 Назад")])
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

def get_request_keyboard(request_id: int, is_owner: bool = False):
    """Inline-клавиатура для запроса"""
    if is_owner:
        keyboard = [
            [
                InlineKeyboardButton("👥 Просмотреть отклики", callback_data=f"view_apps_{request_id}"),
                InlineKeyboardButton("✏️ Редактировать", callback_data=f"edit_req_{request_id}")
            ],
            [
                InlineKeyboardButton("✅ Завершить", callback_data=f"complete_req_{request_id}"),
                InlineKeyboardButton("❌ Отменить", callback_data=f"cancel_req_{request_id}")
            ],
            [
                InlineKeyboardButton("📊 Статистика", callback_data=f"stats_req_{request_id}"),
                InlineKeyboardButton("🔗 Поделиться", callback_data=f"share_req_{request_id}")
            ]
        ]
    else:
        keyboard = [
            [
                InlineKeyboardButton("✋ Откликнуться", callback_data=f"apply_req_{request_id}"),
                InlineKeyboardButton("💬 Написать автору", callback_data=f"message_req_{request_id}")
            ],
            [
                InlineKeyboardButton("⭐ В избранное", callback_data=f"favorite_req_{request_id}"),
                InlineKeyboardButton("⚠️ Пожаловаться", callback_data=f"report_req_{request_id}")
            ],
            [
                InlineKeyboardButton("👤 Профиль автора", callback_data=f"profile_req_{request_id}")
            ]
        ]
    
    return InlineKeyboardMarkup(keyboard)

def get_application_keyboard(application_id: int, request_id: int):
    """Inline-клавиатура для заявки (для автора запроса)"""
    keyboard = [
        [
            InlineKeyboardButton("✅ Принять", callback_data=f"accept_app_{application_id}"),
            InlineKeyboardButton("❌ Отклонить", callback_data=f"reject_app_{application_id}")
        ],
        [
            InlineKeyboardButton("💬 Написать", callback_data=f"message_app_{application_id}"),
            InlineKeyboardButton("📞 Связаться", callback_data=f"contact_app_{application_id}")
        ],
        [
            InlineKeyboardButton("📋 К запросу", callback_data=f"back_to_req_{request_id}")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

# Обработчики команд
async def show_need_help_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает меню 'Нужна помощь'"""
    await update.message.reply_text(
        "🆘 *Нужна помощь?*\n\n"
        "Здесь вы можете:\n"
        "• Создать запрос на помощь\n"
        "• Найти исполнителя для задачи\n"
        "• Просмотреть отклики на ваши запросы\n"
        "• Управлять своими задачами\n\n"
        "Выберите действие:",
        reply_markup=get_need_help_main_keyboard(),
        parse_mode='Markdown'
    )

async def start_create_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начинает создание запроса на помощь"""
    await update.message.reply_text(
        "➕ *Создание запроса на помощь*\n\n"
        "Выберите категорию задачи:",
        reply_markup=get_request_categories_keyboard(),
        parse_mode='Markdown'
    )
    return REQUEST_CATEGORY

async def process_request_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает выбор категории для запроса"""
    # Если мы пришли в состояние из режима поиска — показываем запросы по категории
    if context.user_data.get('search_mode'):
        # Сбрасываем режим поиска и делегируем показ найденных запросов
        context.user_data.pop('search_mode', None)
        return await show_requests_in_category(update, context)
    
    category_name = update.message.text
    
    # Проверяем валидность категории
    if category_name not in REQUEST_CATEGORIES.values():
        await update.message.reply_text(
            "Пожалуйста, выберите категорию из списка:",
            reply_markup=get_request_categories_keyboard()
        )
        return REQUEST_CATEGORY
    
    # Находим ключ категории
    category_key = None
    for key, value in REQUEST_CATEGORIES.items():
        if value == category_name:
            category_key = key
            break
    
    context.user_data['request_category'] = category_key
    context.user_data['request_category_name'] = category_name
    
    await update.message.reply_text(
        f"📝 *Категория: {category_name}*\n\n"
        "Теперь подробно опишите вашу задачу:\n\n"
        "*Что нужно сделать?*\n"
        "• Конкретная задача и требования\n"
        "• Объем работы\n"
        "• Технические детали (если нужно)\n"
        "• Примеры или референсы\n\n"
        "*Совет:* Чем подробнее описание, тем лучше отклики!",
        parse_mode='Markdown',
        reply_markup=ReplyKeyboardMarkup([["🔙 Назад"]], resize_keyboard=True)
    )
    return REQUEST_DESCRIPTION

async def process_request_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает описание запроса"""
    if update.message.text == "🔙 Назад":
        await update.message.reply_text(
            "Выберите категорию:",
            reply_markup=get_request_categories_keyboard()
        )
        return REQUEST_CATEGORY
    
    context.user_data['request_description'] = update.message.text
    
    await update.message.reply_text(
        "💰 *Бюджет задачи*\n\n"
        "Укажите бюджет для этой задачи:\n"
        "• Примерная сумма\n"
        "• Диапазон\n"
        "• Или выберите 'Договорная цена'\n\n"
        "Это поможет исполнителям оценить свои возможности.",
        parse_mode='Markdown',
        reply_markup=get_budget_keyboard()
    )
    return REQUEST_BUDGET

async def process_request_budget(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает выбор бюджета"""
    if update.message.text == "🔙 Назад":
        await update.message.reply_text(
            "Опишите вашу задачу:",
            reply_markup=ReplyKeyboardMarkup([["🔙 Назад"]], resize_keyboard=True)
        )
        return REQUEST_DESCRIPTION
    
    if update.message.text not in BUDGET_OPTIONS:
        await update.message.reply_text(
            "Пожалуйста, выберите бюджет из списка:",
            reply_markup=get_budget_keyboard()
        )
        return REQUEST_BUDGET
    
    context.user_data['request_budget'] = update.message.text
    
    await update.message.reply_text(
        "⏰ *Срок выполнения*\n\n"
        "Когда нужно выполнить задачу?\n"
        "Укажите желаемый срок:",
        parse_mode='Markdown',
        reply_markup=get_deadline_keyboard()
    )
    return REQUEST_DEADLINE

async def process_request_deadline(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Завершает выбор срока и запрашивает контакты"""
    if update.message.text == "🔙 Назад":
        await update.message.reply_text(
            "Выберите бюджет:",
            reply_markup=get_budget_keyboard()
        )
        return REQUEST_BUDGET
    
    if update.message.text not in DEADLINE_OPTIONS:
        await update.message.reply_text(
            "Пожалуйста, выберите срок из списка:",
            reply_markup=get_deadline_keyboard()
        )
        return REQUEST_DEADLINE
    
    context.user_data['request_deadline'] = update.message.text
    
    await update.message.reply_text(
        "📞 *Контактная информация (обязательно)*\n\n"
        "Укажите, как с вами можно связаться (Telegram username, email или телефон):",
        parse_mode='Markdown',
        reply_markup=ReplyKeyboardMarkup([["🔙 Назад"]], resize_keyboard=True)
    )
    return REQUEST_CONTACTS

async def process_request_contacts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает ввод контактов и сохраняет запрос"""
    if update.message.text == "🔙 Назад":
        await update.message.reply_text(
            "Выберите срок:",
            reply_markup=get_deadline_keyboard()
        )
        return REQUEST_DEADLINE
    
    contacts = update.message.text.strip()
    if len(contacts) < 3:
        await update.message.reply_text("Пожалуйста, укажите корректные контакты:")
        return REQUEST_CONTACTS
    
    user = update.effective_user
    
    # Сохраняем запрос с контактами
    request_id = request_system.save_request(
        user_id=user.id,
        username=user.username or user.first_name,
        category=context.user_data.get('request_category_name', '—'),
        description=context.user_data.get('request_description', ''),
        budget=context.user_data.get('request_budget', 'Не указан'),
        deadline=context.user_data.get('request_deadline', 'Не указан'),
        contacts=contacts
    )
    
    # Формируем текст и подтверждение
    request_text = format_request_text(
        request_id=request_id,
        username=user.username or user.first_name,
        category=context.user_data.get('request_category_name', '—'),
        description=context.user_data.get('request_description', ''),
        budget=context.user_data.get('request_budget', 'Не указан'),
        deadline=context.user_data.get('request_deadline', 'Не указан')
    )
    
    # Очищаем временные данные
    context.user_data.clear()
    
    await update.message.reply_text(
        f"✅ *Запрос с контактами создан!*\n\n"
        f"🆔 ID запроса: #{request_id}\n\n"
        f"Контакты: {contacts}\n\n"
        f"Исполнители могут откликнуться и увидеть ваши контакты.",
        parse_mode='Markdown',
        reply_markup=get_need_help_main_keyboard()
    )
    
    await update.message.reply_text(
        request_text,
        reply_markup=get_request_keyboard(request_id, is_owner=True),
        parse_mode='Markdown'
    )
    
    from telegram.ext import ConversationHandler
    return ConversationHandler.END

def format_request_text(request_id: int, username: str, category: str, 
                       description: str, budget: str, deadline: str) -> str:
    """Форматирует текст запроса"""
    text = f"🆔 *Запрос #{request_id}*\n\n"
    text += f"👤 *Автор:* {username}\n"
    text += f"🎯 *Категория:* {category}\n"
    text += f"💰 *Бюджет:* {budget}\n"
    text += f"⏰ *Срок:* {deadline}\n\n"
    text += f"📝 *Описание:*\n{description}\n\n"
    text += f"📅 *Создан:* {datetime.now().strftime('%d.%m.%Y %H:%M')}\n"
    text += f"📊 *Откликов:* 0"
    
    return text

async def search_requests(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начинает поиск запросов"""
    # Помечаем, что пользователь в режиме поиска (чтобы следующий ввод категории был обработан как поиск)
    context.user_data['search_mode'] = True
    await update.message.reply_text(
        "🔍 *Поиск запросов*\n\n"
        "Выберите категорию для поиска:",
        reply_markup=get_request_categories_keyboard(),
        parse_mode='Markdown'
    )
    return REQUEST_CATEGORY  # Используем то же состояние, что и для создания

async def show_requests_in_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает запросы в выбранной категории"""
    category_name = update.message.text
    
    # Проверяем валидность категории
    if category_name not in REQUEST_CATEGORIES.values():
        await update.message.reply_text(
            "Пожалуйста, выберите категорию из списка:",
            reply_markup=get_request_categories_keyboard()
        )
        return REQUEST_CATEGORY
    
    # Получаем запросы
    requests = request_system.get_requests_by_category(category_name, limit=10)
    
    if not requests:
        await update.message.reply_text(
            f"😔 В категории *{category_name}* пока нет активных запросов.\n\n"
            f"Попробуйте:\n"
            f"• Выбрать другую категорию\n"
            f"• Создать свой запрос\n"
            f"• Зайти позже",
            parse_mode='Markdown',
            reply_markup=get_need_help_main_keyboard()
        )
        from telegram.ext import ConversationHandler
        return ConversationHandler.END
    
    await update.message.reply_text(
        f"🔍 *Найдено запросов: {len(requests)}*\n\n"
        f"Категория: {category_name}\n"
        f"👇 Вот несколько свежих запросов:",
        parse_mode='Markdown',
        reply_markup=get_need_help_main_keyboard()
    )
    
    # Показываем первые 3 запроса
    for request in requests[:3]:
        request_text = (
            f"🆔 *Запрос #{request['id']}*\n"
            f"👤 {request['username']}\n"
            f"💰 {request['budget']}\n"
            f"⏰ {request['deadline']}\n"
            f"📊 Откликов: {request['applications_count']}\n\n"
            f"{request['description'][:150]}...\n\n"
            f"📅 {datetime.fromisoformat(request['created_at']).strftime('%d.%m.%Y %H:%M')}"
        )
        
        await update.message.reply_text(
            request_text,
            reply_markup=get_request_keyboard(request['id'], is_owner=False),
            parse_mode='Markdown'
        )
    
    if len(requests) > 3:
        await update.message.reply_text(
            f"И еще {len(requests) - 3} запросов...\n"
            f"Используйте поиск снова для просмотра остальных.",
            reply_markup=get_need_help_main_keyboard()
        )
    
    from telegram.ext import ConversationHandler
    return ConversationHandler.END

async def show_my_requests(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает запросы пользователя"""
    user_id = update.effective_user.id
    requests = request_system.get_user_requests(user_id)
    
    if not requests:
        await update.message.reply_text(
            "📭 *У вас пока нет запросов*\n\n"
            "Создайте первый запрос, чтобы найти исполнителя!",
            parse_mode='Markdown',
            reply_markup=get_need_help_main_keyboard()
        )
        return
    
    # Группируем по статусу
    open_requests = [r for r in requests if r['status'] == 'open']
    in_progress_requests = [r for r in requests if r['status'] == 'in_progress']
    completed_requests = [r for r in requests if r['status'] == 'completed']
    
    stats_text = (
        f"📋 *Ваши запросы*\n\n"
        f"📊 *Статистика:*\n"
        f"• 🔍 Открытых: {len(open_requests)}\n"
        f"• 🚀 В работе: {len(in_progress_requests)}\n"
        f"• ✅ Завершено: {len(completed_requests)}\n"
        f"• 📈 Всего: {len(requests)}\n\n"
    )
    
    if open_requests:
        stats_text += "*🔍 Открытые запросы:*\n"
        for req in open_requests[:3]:  # Показываем первые 3
            stats_text += f"• #{req['id']} - {req['category']} ({req['applications_count']} откликов)\n"
    
    await update.message.reply_text(
        stats_text,
        parse_mode='Markdown',
        reply_markup=get_need_help_main_keyboard()
    )
    
    # Показываем детали последнего активного запроса
    active_requests = open_requests + in_progress_requests
    if active_requests:
        latest_request = max(active_requests, key=lambda x: x['created_at'])
        
        request_text = format_request_text(
            request_id=latest_request['id'],
            username=latest_request['username'],
            category=latest_request['category'],
            description=latest_request['description'],
            budget=latest_request['budget'],
            deadline=latest_request['deadline']
        )
        
        # Обновляем количество откликов
        applications_count = request_system.get_applications_for_request(latest_request['id'])
        
        request_text = request_text.replace("Откликов: 0", f"Откликов: {len(applications_count)}")
        
        await update.message.reply_text(
            request_text,
            reply_markup=get_request_keyboard(latest_request['id'], is_owner=True),
            parse_mode='Markdown'
        )

async def show_my_applications(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает отклики пользователя"""
    user_id = update.effective_user.id
    applications = request_system.get_user_applications(user_id)
    
    if not applications:
        await update.message.reply_text(
            "📭 *У вас пока нет откликов*\n\n"
            "Найдите интересные запросы и откликнитесь на них!",
            parse_mode='Markdown',
            reply_markup=get_need_help_main_keyboard()
        )
        return
    
    pending_apps = [a for a in applications if a['status'] == 'pending']
    accepted_apps = [a for a in applications if a['status'] == 'accepted']
    rejected_apps = [a for a in applications if a['status'] == 'rejected']
    
    stats_text = (
        f"📨 *Мои отклики*\n\n"
        f"📊 *Статистика:*\n"
        f"• ⏳ Ожидают: {len(pending_apps)}\n"
        f"• ✅ Приняты: {len(accepted_apps)}\n"
        f"• ❌ Отклонены: {len(rejected_apps)}\n"
        f"• 📈 Всего: {len(applications)}\n"
    )
    
    await update.message.reply_text(
        stats_text,
        parse_mode='Markdown',
        reply_markup=get_need_help_main_keyboard()
    )
    
    # Показываем последние отклики
    recent_apps = sorted(applications, key=lambda x: x['created_at'], reverse=True)[:3]
    
    for app in recent_apps:
        request = request_system.get_request_by_id(app['request_id'])
        if request:
            status_emoji = {
                'pending': '⏳',
                'accepted': '✅',
                'rejected': '❌'
            }.get(app['status'], '❓')
            
            app_text = (
                f"{status_emoji} *Отклик на запрос #{app['request_id']}*\n"
                f"📝 {request['category']}\n"
                f"💰 {request['budget']}\n"
                f"📅 {datetime.fromisoformat(app['created_at']).strftime('%d.%m.%Y')}\n"
                f"📋 *Ваше сообщение:*\n{app['message'][:100]}..."
            )
            
            await update.message.reply_text(
                app_text,
                parse_mode='Markdown'
            )

async def start_apply_for_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начинает процесс отклика на запрос"""
    # Этот обработчик вызывается из callback (при нажатии кнопки "Откликнуться")
    query = update.callback_query
    await query.answer()
    
    request_id = int(query.data.replace("apply_req_", ""))
    request = request_system.get_request_by_id(request_id)
    
    if not request:
        await query.edit_message_text("❌ Запрос не найден!")
        return
    
    context.user_data['applying_request_id'] = request_id
    context.user_data['applying_request'] = request
    
    await query.edit_message_text(
        f"✋ *Отклик на запрос #{request_id}*\n\n"
        f"📝 *Задача:* {request['category']}\n"
        f"💰 *Бюджет:* {request['budget']}\n\n"
        f"Напишите, почему вы подходите для этой задачи:\n"
        f"• Ваш опыт и навыки\n"
        f"• Примеры работ\n"
        f"• Сроки выполнения\n"
        f"• Ваши условия\n\n"
        f"*Совет:* Будьте конкретны и предложите решение!",
        parse_mode='Markdown'
    )
    
    return SEND_APPLICATION

async def send_application(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отправляет заявку на выполнение запроса"""
    request_id = context.user_data['applying_request_id']
    request = context.user_data['applying_request']
    user = update.effective_user
    
    application_message = update.message.text
    
    # Сохраняем заявку
    application_id = request_system.save_application(
        request_id=request_id,
        applicant_id=user.id,
        applicant_username=user.username or user.first_name,
        message=application_message
    )
    
    # Попытка уведомить автора запроса о новом отклике
    try:
        author_id = request.get('user_id')
        if author_id:
            author_username = request.get('username') or ''
            applicant_username = user.username or user.first_name
            notify_text = (
                f"📨 *Новый отклик на ваш запрос #{request_id}*\n\n"
                f"👤 От: @{applicant_username} (ID: {user.id})\n\n"
                f"📝 Сообщение исполнителя:\n{application_message}\n\n"
                f"📞 Контакты исполнителя: @{applicant_username if user.username else '—'}\n\n"
                "Вы можете принять или отклонить отклик в панели заявки."
            )
            # Отправляем уведомление автору запроса с кнопками управления заявкой
            await context.bot.send_message(
                chat_id=author_id,
                text=notify_text,
                parse_mode='Markdown',
                reply_markup=get_application_keyboard(application_id, request_id)
            )
    except Exception as e:
        logger.warning(f"Не удалось отправить уведомление автору запроса #{request_id}: {e}", exc_info=True)
    
    # Очищаем временные данные
    context.user_data.pop('applying_request_id', None)
    context.user_data.pop('applying_request', None)
    
    # Подробности о контактах автора (чтобы можно было написать)
    author_contacts = request.get('contacts', '')
    author_username = (request.get('username') or '').lstrip('@')
    
    # Кнопки: только ссылка на профиль автора (если есть)
    buttons = []
    if author_username:
        buttons.append([InlineKeyboardButton("🔗 Открыть профиль автора", url=f"https://t.me/{author_username}")])
    
    await update.message.reply_text(
        f"✅ *Заявка отправлена!*\n\n"
        f"🆔 ID заявки: #{application_id}\n"
        f"📋 К запросу: #{request_id}\n\n"
        f"👤 Автор: @{author_username or request.get('username','—')}\n"
        f"📞 Контакты автора: {author_contacts if author_contacts else 'не указаны'}\n\n"
        f"Используйте контакты автора или отклик на другие заявки.",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(buttons) if buttons else None
    )
    
    from telegram.ext import ConversationHandler
    return ConversationHandler.END

async def cancel_request_flow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отменяет процесс создания/поиска запроса"""
    await update.message.reply_text(
        "Действие отменено.",
        reply_markup=get_need_help_main_keyboard()
    )
    
    # Очищаем временные данные
    context.user_data.clear()
    
    from telegram.ext import ConversationHandler
    return ConversationHandler.END

# Обработчик callback-запросов
async def handle_request_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает нажатия inline-кнопок в запросах"""
    query = update.callback_query
    await query.answer()
    
    callback_data = query.data
    
    if callback_data.startswith("apply_req_"):
        # Обработка перенаправляется в start_apply_for_request
        return await start_apply_for_request(update, context)
    
    elif callback_data.startswith("message_req_"):
        request_id = int(callback_data.replace("message_req_", ""))
        request = request_system.get_request_by_id(request_id)
        if not request:
            await query.edit_message_text("❌ Запрос не найден!")
            return
        author_username = (request.get('username') or '').lstrip('@')
        contacts = request.get('contacts') or 'Контакты не указаны'
        
        # Показываем username и контакты, без кнопки "написать через бота"
        username_line = f"@{author_username}" if author_username else "—"
        text = (
            f"👤 *Автор:* {username_line}\n"
            f"📞 *Контакты:* {contacts}\n\n"
            f"Вы можете открыть профиль автора (если указан) или связаться напрямую по контактам."
        )
        
        buttons = []
        if author_username:
            buttons.append([InlineKeyboardButton("🔗 Открыть профиль", url=f"https://t.me/{author_username}")])
        buttons.append([InlineKeyboardButton("🔙 Назад к заявке", callback_data=f"back_to_req_{request_id}")])
        
        await query.edit_message_text(
            text,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(buttons)
        )
        return
    
    elif callback_data.startswith("view_apps_"):
        request_id = int(callback_data.replace("view_apps_", ""))
        applications = request_system.get_applications_for_request(request_id)
        
        if not applications:
            await query.edit_message_text(
                f"📭 *Запрос #{request_id}*\n\n"
                "Пока нет откликов на этот запрос.\n"
                "Поделитесь запросом, чтобы привлечь больше исполнителей!",
                parse_mode='Markdown'
            )
            return
        
        await query.edit_message_text(
            f"👥 *Отклики на запрос #{request_id}*\n\n"
            f"📊 Всего откликов: {len(applications)}\n\n"
            f"👇 Вот последние отклики:",
            parse_mode='Markdown'
        )
        
        # Показываем последние 2 отклика
        for app in applications[-2:]:
            app_text = (
                f"👤 *{app['applicant_username']}*\n"
                f"📅 {datetime.fromisoformat(app['created_at']).strftime('%d.%m.%Y %H:%M')}\n"
                f"📝 {app['message'][:100]}...\n"
                f"📊 Статус: {app['status']}"
            )
            
            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text=app_text,
                reply_markup=get_application_keyboard(app['id'], request_id),
                parse_mode='Markdown'
            )
    
    elif callback_data.startswith("accept_app_"):
        application_id = int(callback_data.replace("accept_app_", ""))
        await query.edit_message_text(
            f"✅ Заявка #{application_id} принята!\n\n"
            "Свяжитесь с исполнителем для обсуждения деталей.",
            parse_mode='Markdown'
        )
    
    elif callback_data.startswith("complete_req_"):
        request_id = int(callback_data.replace("complete_req_", ""))
        await query.edit_message_text(
            f"✅ Запрос #{request_id} завершен!\n\n"
            "Не забудьте оценить работу исполнителя.",
            parse_mode='Markdown'
        )