import logging
import re
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    Application, CommandHandler, MessageHandler, filters,
    ContextTypes, ConversationHandler
)
from config import TOKEN

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Состояния для диалогов
REGISTER_NAME, REGISTER_PHONE, REGISTER_EMAIL, REGISTER_PASSWORD = range(4)
LOGIN_USERNAME, LOGIN_PASSWORD = range(2)
OFFER_CATEGORY, OFFER_DESCRIPTION, OFFER_LOCATION = range(3)
NEED_CATEGORY, NEED_DESCRIPTION, NEED_LOCATION, NEED_URGENT = range(4)

# Временное хранилище пользователей (замените на БД!)
users_db = {}
requests_db = []
user_responses = {}

# Функции для клавиатур
def get_start_keyboard():
    return ReplyKeyboardMarkup([
        [KeyboardButton("🚀 Регистрация"), KeyboardButton("🔐 Вход")],
        [KeyboardButton("ℹ️ О проекте")]
    ], resize_keyboard=True, one_time_keyboard=True)

def get_main_menu_keyboard():
    return ReplyKeyboardMarkup([
        [KeyboardButton("🙋‍♂️ Предложить помощь"), KeyboardButton("🙏 Попросить помощи")],
        [KeyboardButton("👤 Личный кабинет"), KeyboardButton("🏆 Рейтинг волонтеров")],
        [KeyboardButton("📋 Активные заявки")]
    ], resize_keyboard=True)

def get_categories_keyboard(help_type):
    """Клавиатура с категориями помощи"""
    if help_type == 'offer':
        categories = [
            "🚗 Транспорт", "🛠️ Ремонт", "🎓 Обучение",
            "🛒 Покупки", "👨‍👩‍👦 Сопровождение", "💻 IT-помощь"
        ]
    else:  # need
        categories = [
            "🚗 Транспорт", "🛠️ Ремонт", "🎓 Обучение",
            "🛒 Покупки", "💊 Медицина", "🏠 Жилье"
        ]
    
    # Создаем кнопки по 2 в ряд
    buttons = []
    for i in range(0, len(categories), 2):
        row = categories[i:i+2]
        buttons.append([KeyboardButton(cat) for cat in row])
    
    # Добавляем кнопку "Назад"
    buttons.append([KeyboardButton("⬅️ Назад в меню")])
    
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)

# --- ОБРАБОТЧИКИ КОМАНД ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    await update.message.reply_text(
        "👋 Привет! Я ДоброБот - платформа взаимопомощи!\n\n"
        "Здесь люди помогают друг другу в бытовых задачах.\n"
        "Выберите действие:",
        reply_markup=get_start_keyboard()
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /help"""
    await update.message.reply_text(
        "📚 Помощь по командам:\n\n"
        "/start - начать работу с ботом\n"
        "/help - показать это сообщение\n"
        "/cancel - отменить текущее действие\n"
        "/menu - вернуться в главное меню\n\n"
        "Используйте кнопки меню для навигации.",
        reply_markup=get_start_keyboard()
    )

async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда для возврата в меню"""
    user_id = update.effective_user.id
    if user_id in users_db:
        await update.message.reply_text(
            "Главное меню:",
            reply_markup=get_main_menu_keyboard()
        )
    else:
        await update.message.reply_text(
            "Вы не вошли в систему. Пожалуйста, войдите или зарегистрируйтесь.",
            reply_markup=get_start_keyboard()
        )

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отмена любого действия"""
    await update.message.reply_text(
        "Действие отменено.",
        reply_markup=get_start_keyboard()
    )
    return ConversationHandler.END

# --- 1. РЕГИСТРАЦИЯ (уже работает) ---
async def handle_registration_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало регистрации"""
    await update.message.reply_text(
        "📝 Начинаем регистрацию!\n\n"
        "Для отмены введите /cancel в любой момент.\n\n"
        "Введите ваше ФИО (полностью):"
    )
    return REGISTER_NAME

async def register_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['full_name'] = update.message.text
    await update.message.reply_text("Введите ваш номер телефона (например: +996555123456):")
    return REGISTER_PHONE

async def register_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    phone = update.message.text
    if not phone.startswith('+'):
        await update.message.reply_text("❌ Введите номер с кодом страны. Попробуйте еще раз:")
        return REGISTER_PHONE
    context.user_data['phone'] = phone
    await update.message.reply_text("Введите ваш email (например: ivanov@gmail.com):")
    return REGISTER_EMAIL

async def register_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    email = update.message.text
    if '@' not in email or '.' not in email:
        await update.message.reply_text("❌ Введите корректный email. Попробуйте еще раз:")
        return REGISTER_EMAIL
    context.user_data['email'] = email
    await update.message.reply_text("Придумайте пароль (минимум 6 символов):")
    return REGISTER_PASSWORD

async def register_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    password = update.message.text
    if len(password) < 6:
        await update.message.reply_text("❌ Пароль должен быть не менее 6 символов. Попробуйте еще раз:")
        return REGISTER_PASSWORD
    
    # Сохраняем пользователя
    user_id = update.effective_user.id
    users_db[user_id] = {
        'full_name': context.user_data['full_name'],
        'phone': context.user_data['phone'],
        'email': context.user_data['email'],
        'password': password,
        'rating': 5.0,
        'help_count': 0,
        'requests_count': 0
    }
    
    await update.message.reply_text(
        f"🎉 Регистрация успешно завершена, {context.user_data['full_name']}!\n"
        "Теперь вы можете пользоваться всеми функциями бота!",
        reply_markup=get_main_menu_keyboard()
    )
    
    context.user_data.clear()
    return ConversationHandler.END

# --- 2. ВХОД (НОВАЯ ФУНКЦИЯ) ---
async def handle_login_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало входа"""
    user_id = update.effective_user.id
    
    # Если уже зарегистрирован
    if user_id in users_db:
        await update.message.reply_text(
            f"👋 Вы уже вошли как {users_db[user_id]['full_name']}!",
            reply_markup=get_main_menu_keyboard()
        )
        return ConversationHandler.END
    
    await update.message.reply_text(
        "🔐 Вход в систему\n\n"
        "Введите ваш email (или телефон):"
    )
    return LOGIN_USERNAME

async def login_username(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получение email/телефона для входа"""
    identifier = update.message.text
    context.user_data['login_identifier'] = identifier
    
    # Ищем пользователя по email или телефону
    user_found = None
    for user_id, user_data in users_db.items():
        if user_data['email'] == identifier or user_data['phone'] == identifier:
            user_found = user_data
            context.user_data['login_user_id'] = user_id
            break
    
    if not user_found:
        await update.message.reply_text(
            "❌ Пользователь не найден. Проверьте email/телефон или зарегистрируйтесь.\n"
            "Попробуйте еще раз или введите /cancel:"
        )
        return LOGIN_USERNAME
    
    await update.message.reply_text("Введите ваш пароль:")
    return LOGIN_PASSWORD

async def login_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Проверка пароля и завершение входа"""
    password = update.message.text
    user_id = context.user_data.get('login_user_id')
    
    if user_id and user_id in users_db and users_db[user_id]['password'] == password:
        # Обновляем текущего пользователя
        current_user_id = update.effective_user.id
        if current_user_id != user_id:
            users_db[current_user_id] = users_db[user_id].copy()
        
        await update.message.reply_text(
            f"✅ Вход выполнен успешно!\n"
            f"Добро пожаловать, {users_db[user_id]['full_name']}!",
            reply_markup=get_main_menu_keyboard()
        )
    else:
        await update.message.reply_text(
            "❌ Неверный пароль. Попробуйте еще раз или введите /cancel:"
        )
        return LOGIN_PASSWORD
    
    context.user_data.clear()
    return ConversationHandler.END

# --- 3. ПРЕДЛОЖИТЬ ПОМОЩЬ ---
async def handle_offer_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало создания предложения помощи"""
    user_id = update.effective_user.id
    if user_id not in users_db:
        await update.message.reply_text(
            "❌ Сначала войдите или зарегистрируйтесь.",
            reply_markup=get_start_keyboard()
        )
        return ConversationHandler.END
    
    await update.message.reply_text(
        "🙋‍♂️ *Предложить помощь*\n\n"
        "Выберите категорию помощи, которую хотите предложить:",
        parse_mode='Markdown',
        reply_markup=get_categories_keyboard('offer')
    )
    return OFFER_CATEGORY

async def offer_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Выбор категории помощи"""
    if update.message.text == "⬅️ Назад в меню":
        await update.message.reply_text("Главное меню:", reply_markup=get_main_menu_keyboard())
        return ConversationHandler.END
    
    context.user_data['offer_category'] = update.message.text
    await update.message.reply_text(
        "Опишите, какую именно помощь вы можете оказать:\n"
        "(Например: 'Могу помочь с переездом в субботу', 'Готов обучить работе с Excel')"
    )
    return OFFER_DESCRIPTION

async def offer_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Описание помощи"""
    context.user_data['offer_description'] = update.message.text
    await update.message.reply_text(
        "Укажите район или адрес, где можете помочь:\n"
        "(Например: 'Район Аламедин', 'Выезд по городу', 'Онлайн')"
    )
    return OFFER_LOCATION

async def offer_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Местоположение и завершение"""
    user_id = update.effective_user.id
    user_name = users_db[user_id]['full_name']
    
    # Создаем заявку
    request_id = len(requests_db) + 1
    request = {
        'id': request_id,
        'type': 'offer',
        'user_id': user_id,
        'user_name': user_name,
        'category': context.user_data['offer_category'],
        'description': context.user_data['offer_description'],
        'location': update.message.text,
        'status': 'active',
        'responses': []
    }
    
    requests_db.append(request)
    
    # Увеличиваем счетчик помощи пользователя
    users_db[user_id]['help_count'] += 1
    
    await update.message.reply_text(
        f"✅ *Ваше предложение помощи опубликовано!*\n\n"
        f"📌 *Категория:* {context.user_data['offer_category']}\n"
        f"📝 *Описание:* {context.user_data['offer_description']}\n"
        f"📍 *Место:* {update.message.text}\n\n"
        f"Теперь другие пользователи смогут увидеть ваше предложение "
        f"в разделе 'Активные заявки'.",
        parse_mode='Markdown',
        reply_markup=get_main_menu_keyboard()
    )
    
    context.user_data.clear()
    return ConversationHandler.END

# --- 4. ПОПРОСИТЬ ПОМОЩИ ---
async def handle_need_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало создания запроса помощи"""
    user_id = update.effective_user.id
    if user_id not in users_db:
        await update.message.reply_text(
            "❌ Сначала войдите или зарегистрируйтесь.",
            reply_markup=get_start_keyboard()
        )
        return ConversationHandler.END
    
    await update.message.reply_text(
        "🙏 *Попросить помощи*\n\n"
        "Выберите категорию необходимой помощи:",
        parse_mode='Markdown',
        reply_markup=get_categories_keyboard('need')
    )
    return NEED_CATEGORY

async def need_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Выбор категории"""
    if update.message.text == "⬅️ Назад в меню":
        await update.message.reply_text("Главное меню:", reply_markup=get_main_menu_keyboard())
        return ConversationHandler.END
    
    context.user_data['need_category'] = update.message.text
    await update.message.reply_text(
        "Подробно опишите, какая помощь вам нужна:\n"
        "(Например: 'Нужна помощь с переездом 20 числа', "
        "'Требуется ремонт крана на кухне')"
    )
    return NEED_DESCRIPTION

async def need_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Описание потребности"""
    context.user_data['need_description'] = update.message.text
    await update.message.reply_text(
        "Укажите ваш район или адрес:\n"
        "(Например: 'ул. Манас 45', 'микрорайон Джал', 'Онлайн')"
    )
    return NEED_LOCATION

async def need_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Местоположение"""
    context.user_data['need_location'] = update.message.text
    await update.message.reply_text(
        "❓ Это срочная заявка?\n"
        "Ответьте 'да' или 'нет':"
    )
    return NEED_URGENT

async def need_urgent(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Срочность и завершение"""
    user_id = update.effective_user.id
    user_name = users_db[user_id]['full_name']
    urgent = update.message.text.lower() in ['да', 'yes', 'срочно']
    
    # Создаем заявку
    request_id = len(requests_db) + 1
    request = {
        'id': request_id,
        'type': 'need',
        'user_id': user_id,
        'user_name': user_name,
        'category': context.user_data['need_category'],
        'description': context.user_data['need_description'],
        'location': context.user_data['need_location'],
        'urgent': urgent,
        'status': 'active',
        'responses': []
    }
    
    requests_db.append(request)
    
    # Увеличиваем счетчик заявок пользователя
    users_db[user_id]['requests_count'] += 1
    
    urgent_text = "🔴 *СРОЧНО* " if urgent else ""
    
    await update.message.reply_text(
        f"{urgent_text}✅ *Ваш запрос помощи опубликован!*\n\n"
        f"📌 *Категория:* {context.user_data['need_category']}\n"
        f"📝 *Описание:* {context.user_data['need_description']}\n"
        f"📍 *Место:* {context.user_data['need_location']}\n"
        f"🚨 *Срочно:* {'Да' if urgent else 'Нет'}\n\n"
        f"Теперь волонтеры смогут увидеть вашу заявку "
        f"и предложить помощь.",
        parse_mode='Markdown',
        reply_markup=get_main_menu_keyboard()
    )
    
    context.user_data.clear()
    return ConversationHandler.END

# --- 5. ЛИЧНЫЙ КАБИНЕТ ---
async def handle_personal_cabinet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Личный кабинет пользователя"""
    user_id = update.effective_user.id
    
    if user_id not in users_db:
        await update.message.reply_text(
            "❌ Сначала войдите или зарегистрируйтесь.",
            reply_markup=get_start_keyboard()
        )
        return
    
    user = users_db[user_id]
    
    # Считаем активные заявки пользователя
    user_requests = [r for r in requests_db if r['user_id'] == user_id and r['status'] == 'active']
    user_responses_list = []
    for req in requests_db:
        if user_id in req.get('responses', []):
            user_responses_list.append(req)
    
    # Формируем текст профиля
    profile_text = (
        f"👤 *Личный кабинет*\n\n"
        f"📛 *ФИО:* {user['full_name']}\n"
        f"📞 *Телефон:* {user['phone']}\n"
        f"📧 *Email:* {user['email']}\n"
        f"⭐ *Рейтинг:* {user['rating']}/5.0\n\n"
        f"📊 *Статистика:*\n"
        f"• Помощь предложена: {user['help_count']} раз\n"
        f"• Помощь запрошена: {user['requests_count']} раз\n"
        f"• Активных заявок: {len(user_requests)}\n"
        f"• Откликов на заявки: {len(user_responses_list)}\n\n"
        f"💼 *Мои активные заявки:*\n"
    )
    
    if user_requests:
        for req in user_requests[:3]:  # Показываем первые 3
            req_type = "🙋‍♂️ Предложение" if req['type'] == 'offer' else "🙏 Запрос"
            profile_text += f"• {req_type}: {req['description'][:30]}...\n"
    else:
        profile_text += "Нет активных заявок\n"
    
    # Клавиатура личного кабинета
    keyboard = ReplyKeyboardMarkup([
        [KeyboardButton("✏️ Изменить профиль"), KeyboardButton("📊 Детальная статистика")],
        [KeyboardButton("📋 Мои заявки"), KeyboardButton("🔄 Мои отклики")],
        [KeyboardButton("⬅️ Назад в меню")]
    ], resize_keyboard=True)
    
    await update.message.reply_text(
        profile_text,
        parse_mode='Markdown',
        reply_markup=keyboard
    )

# --- ОБРАБОТЧИКИ КНОПОК ЛИЧНОГО КАБИНЕТА ---
async def handle_personal_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка кнопок личного кабинета"""
    text = update.message.text
    user_id = update.effective_user.id
    
    if text == "✏️ Изменить профиль":
        await update.message.reply_text(
            "Функция изменения профиля скоро будет доступна!\n"
            "Пока вы можете:\n"
            "• Просмотреть статистику\n"
            "• Управлять заявками",
            reply_markup=get_main_menu_keyboard()
        )
        
    elif text == "📊 Детальная статистика":
        user = users_db.get(user_id, {})
        
        # Считаем заявки по типам
        offer_requests = [r for r in requests_db if r['user_id'] == user_id and r['type'] == 'offer']
        need_requests = [r for r in requests_db if r['user_id'] == user_id and r['type'] == 'need']
        
        stats_text = (
            f"📊 *Детальная статистика*\n\n"
            f"👤 Пользователь: {user.get('full_name', 'Неизвестно')}\n\n"
            f"📈 *Активность:*\n"
            f"• Предложений помощи: {len(offer_requests)}\n"
            f"• Запросов помощи: {len(need_requests)}\n"
            f"• Всего заявок: {len(offer_requests) + len(need_requests)}\n\n"
            f"🏆 *Достижения:*\n"
        )
        
        # Простые достижения
        if user.get('help_count', 0) >= 5:
            stats_text += "• 🏅 Помощник уровня 1 (5+ помощи)\n"
        if user.get('help_count', 0) >= 10:
            stats_text += "• 🏅 Помощник уровня 2 (10+ помощи)\n"
        if len(offer_requests) > 0 and len(need_requests) > 0:
            stats_text += "• 🤝 Универсальный помощник\n"
        
        await update.message.reply_text(
            stats_text,
            parse_mode='Markdown',
            reply_markup=get_main_menu_keyboard()
        )
        
    elif text == "📋 Мои заявки":
        user_requests = [r for r in requests_db if r['user_id'] == user_id]
        
        if not user_requests:
            await update.message.reply_text(
                "У вас пока нет заявок.\n"
                "Создайте первую заявку в главном меню!",
                reply_markup=get_main_menu_keyboard()
            )
            return
        
        requests_text = "📋 *Мои заявки:*\n\n"
        for req in user_requests[:5]:  # Показываем первые 5
            req_type = "🙋‍♂️ Предложение" if req['type'] == 'offer' else "🙏 Запрос"
            status = "✅ Активна" if req['status'] == 'active' else "❌ Завершена"
            urgent = "🔴 " if req.get('urgent', False) else ""
            
            requests_text += (
                f"{urgent}*Заявка #{req['id']}* - {req_type}\n"
                f"📝 {req['description'][:50]}...\n"
                f"📍 {req['location']}\n"
                f"📊 {status} | Откликов: {len(req.get('responses', []))}\n\n"
            )
        
        await update.message.reply_text(
            requests_text,
            parse_mode='Markdown',
            reply_markup=get_main_menu_keyboard()
        )
        
    elif text == "🔄 Мои отклики":
        # Ищем заявки, на которые пользователь откликнулся
        user_responses_list = []
        for req in requests_db:
            if user_id in req.get('responses', []):
                user_responses_list.append(req)
        
        if not user_responses_list:
            await update.message.reply_text(
                "Вы еще не откликались на заявки.\n"
                "Посмотрите активные заявки в главном меню!",
                reply_markup=get_main_menu_keyboard()
            )
            return
        
        responses_text = "🔄 *Мои отклики:*\n\n"
        for req in user_responses_list[:5]:
            req_type = "🙋‍♂️ Предложение" if req['type'] == 'offer' else "🙏 Запрос"
            responses_text += (
                f"*Заявка #{req['id']}* - {req_type}\n"
                f"👤 От: {req['user_name']}\n"
                f"📝 {req['description'][:40]}...\n"
                f"📍 {req['location']}\n\n"
            )
        
        await update.message.reply_text(
            responses_text,
            parse_mode='Markdown',
            reply_markup=get_main_menu_keyboard()
        )
        
    elif text == "⬅️ Назад в меню":
        await update.message.reply_text(
            "Главное меню:",
            reply_markup=get_main_menu_keyboard()
        )

# --- ОБРАБОТЧИК АКТИВНЫХ ЗАЯВОК ---
async def handle_active_requests(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показ активных заявок"""
    user_id = update.effective_user.id
    
    if user_id not in users_db:
        await update.message.reply_text(
            "❌ Сначала войдите или зарегистрируйтесь.",
            reply_markup=get_start_keyboard()
        )
        return
    
    active_requests = [r for r in requests_db if r['status'] == 'active']
    
    if not active_requests:
        await update.message.reply_text(
            "📭 Пока нет активных заявок.\n"
            "Будьте первым, кто создаст заявку!",
            reply_markup=get_main_menu_keyboard()
        )
        return
    
    # Показываем первые 5 заявок
    requests_text = "📋 *Активные заявки:*\n\n"
    for i, req in enumerate(active_requests[:5], 1):
        req_type = "🙋‍♂️ Предложение помощи" if req['type'] == 'offer' else "🙏 Нужна помощь"
        urgent = "🔴 СРОЧНО " if req.get('urgent', False) else ""
        
        requests_text += (
            f"{urgent}*{i}. {req_type}*\n"
            f"👤 От: {req['user_name']}\n"
            f"📌 Категория: {req['category']}\n"
            f"📝 {req['description'][:60]}...\n"
            f"📍 Место: {req['location']}\n"
            f"🔄 Откликов: {len(req.get('responses', []))}\n"
            f"💬 Чтобы откликнуться, напишите: /respond_{req['id']}\n\n"
        )
    
    requests_text += "Чтобы откликнуться на заявку, используйте команду /respond_номер"
    
    await update.message.reply_text(
        requests_text,
        parse_mode='Markdown',
        reply_markup=get_main_menu_keyboard()
    )

# --- ОБРАБОТЧИК ОТКЛИКОВ ---
async def handle_respond(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка команды отклика на заявку"""
    user_id = update.effective_user.id
    
    if user_id not in users_db:
        await update.message.reply_text(
            "❌ Сначала войдите или зарегистрируйтесь.",
            reply_markup=get_start_keyboard()
        )
        return
    
    # Извлекаем номер заявки из команды
    command_parts = update.message.text.split('_')
    if len(command_parts) != 2:
        await update.message.reply_text("Используйте команду в формате: /respond_номер")
        return
    
    try:
        request_id = int(command_parts[1]) - 1  # Индекс в списке
        if request_id < 0 or request_id >= len(requests_db):
            await update.message.reply_text("Заявка с таким номером не найдена.")
            return
        
        request = requests_db[request_id]
        
        # Проверяем, не владелец ли заявки
        if request['user_id'] == user_id:
            await update.message.reply_text("❌ Вы не можете откликнуться на свою заявку.")
            return
        
        # Проверяем, не откликался ли уже
        if user_id in request.get('responses', []):
            await update.message.reply_text("❌ Вы уже откликались на эту заявку.")
            return
        
        # Добавляем отклик
        if 'responses' not in request:
            request['responses'] = []
        request['responses'].append(user_id)
        
        user_name = users_db[user_id]['full_name']
        
        await update.message.reply_text(
            f"✅ Вы откликнулись на заявку!\n\n"
            f"📌 *Категория:* {request['category']}\n"
            f"👤 *Автор:* {request['user_name']}\n"
            f"📝 *Описание:* {request['description'][:50]}...\n\n"
            f"Теперь автор заявки увидит ваш отклик. "
            f"Ожидайте связи с вами!",
            parse_mode='Markdown',
            reply_markup=get_main_menu_keyboard()
        )
        
    except ValueError:
        await update.message.reply_text("Используйте команду в формате: /respond_номер")

# --- ОБРАБОТЧИК РЕЙТИНГА ---
async def handle_rating(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показ рейтинга волонтеров"""
    # Сортируем пользователей по рейтингу
    sorted_users = sorted(
        [(uid, data) for uid, data in users_db.items()],
        key=lambda x: x[1]['rating'],
        reverse=True
    )
    
    if not sorted_users:
        await update.message.reply_text(
            "🏆 Пока нет пользователей в рейтинге.\n"
            "Зарегистрируйтесь первым!",
            reply_markup=get_main_menu_keyboard()
        )
        return
    
    rating_text = "🏆 *Топ волонтеров:*\n\n"
    
    for i, (user_id, user_data) in enumerate(sorted_users[:10], 1):
        stars = "⭐" * int(user_data['rating'])
        rating_text += (
            f"{i}. *{user_data['full_name']}*\n"
            f"   {stars} {user_data['rating']}/5.0\n"
            f"   📊 Помощь: {user_data['help_count']} | Запросы: {user_data['requests_count']}\n\n"
        )
    
    await update.message.reply_text(
        rating_text,
        parse_mode='Markdown',
        reply_markup=get_main_menu_keyboard()
    )

# --- ОБРАБОТЧИК "О ПРОЕКТЕ" ---
async def handle_about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🌟 *ДоброБот* - платформа взаимопомощи\n\n"
        "💡 *Миссия:* Создать сообщество, где каждый может "
        "быть и тем, кто помогает, и тем, кому помогают.\n\n"
        "🔧 *Возможности:*\n"
        "• Регистрация с анкетой\n"
        "• Создание заявок (предложить/попросить помощь)\n"
        "• Просмотр активных заявок\n"
        "• Отклики на заявки\n"
        "• Личный кабинет со статистикой\n"
        "• Рейтинговая система\n\n"
        "🚀 *Для хакатона:*\n"
        "• MVP за 24 часа\n"
        "• Telegram-бот как прототип\n"
        "• Базовая функциональность\n\n"
        "📞 *Связь:* @ваш_никнейм\n"
        "💻 *GitHub:* github.com/ваш_репозиторий",
        parse_mode='Markdown',
        reply_markup=get_start_keyboard()
    )

# --- ГЛАВНАЯ ФУНКЦИЯ ---
def main():
    """Запуск бота"""
    application = Application.builder().token(TOKEN).build()
    
    # ConversationHandler для регистрации
    registration_handler = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex('^🚀 Регистрация$'), handle_registration_start)
        ],
        states={
            REGISTER_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, register_name)
            ],
            REGISTER_PHONE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, register_phone)
            ],
            REGISTER_EMAIL: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, register_email)
            ],
            REGISTER_PASSWORD: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, register_password)
            ],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    
    # ConversationHandler для входа
    login_handler = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex('^🔐 Вход$'), handle_login_start)
        ],
        states={
            LOGIN_USERNAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, login_username)
            ],
            LOGIN_PASSWORD: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, login_password)
            ],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    
    # ConversationHandler для предложения помощи
    offer_handler = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex('^🙋‍♂️ Предложить помощи$'), handle_offer_help)
        ],
        states={
            OFFER_CATEGORY: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, offer_category)
            ],
            OFFER_DESCRIPTION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, offer_description)
            ],
            OFFER_LOCATION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, offer_location)
            ],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    
    # ConversationHandler для запроса помощи
    need_handler = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex('^🙏 Попросить помощи$'), handle_need_help)
        ],
        states={
            NEED_CATEGORY: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, need_category)
            ],
            NEED_DESCRIPTION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, need_description)
            ],
            NEED_LOCATION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, need_location)
            ],
            NEED_URGENT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, need_urgent)
            ],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    
    # Регистрируем все обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("menu", menu_command))
    application.add_handler(CommandHandler("cancel", cancel))
    
    # Добавляем ConversationHandler
    application.add_handler(registration_handler)
    application.add_handler(login_handler)
    application.add_handler(offer_handler)
    application.add_handler(need_handler)
    
    # Обработчики для остальных кнопок
    application.add_handler(MessageHandler(
        filters.Regex('^👤 Личный кабинет$'), 
        handle_personal_cabinet
    ))
    application.add_handler(MessageHandler(
        filters.Regex('^📋 Активные заявки$'), 
        handle_active_requests
    ))
    application.add_handler(MessageHandler(
        filters.Regex('^🏆 Рейтинг волонтеров$'), 
        handle_rating
    ))
    application.add_handler(MessageHandler(
        filters.Regex('^ℹ️ О проекте$'), 
        handle_about
    ))
    
    # Обработчики кнопок личного кабинета
    application.add_handler(MessageHandler(
        filters.Regex('^(✏️ Изменить профиль|📊 Детальная статистика|📋 Мои заявки|🔄 Мои отклики|⬅️ Назад в меню)$'),
        handle_personal_buttons
    ))
    
    # Обработчик команд отклика
    application.add_handler(MessageHandler(
        filters.Regex(r'^/respond_\d+$'),
        handle_respond
    ))
    
    # Запускаем бота
    logger.info("🤖 ДоброБот запускается со всеми функциями...")
    application.run_polling()

if __name__ == '__main__':
    main()