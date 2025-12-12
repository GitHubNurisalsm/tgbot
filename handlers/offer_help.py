"""Обработчики для функции 'Предложить помощь'"""
import logging
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes, ConversationHandler

from keyboards import get_main_menu_keyboard, get_start_keyboard
from database import db
from states import OFFER_CATEGORY, OFFER_TITLE, OFFER_DESCRIPTION, OFFER_CONTACTS

logger = logging.getLogger(__name__)

# Категории помощи
OFFER_CATEGORIES = {
    "IT": "💻 IT и программирование",
    "design": "🎨 Дизайн и графика",
    "writing": "📝 Тексты и переводы",
    "marketing": "📊 Маркетинг",
    "tutoring": "🎓 Обучение",
    "consulting": "🗣️ Консультации",
    "other": "🔧 Разное"
}


def get_categories_keyboard():
    """Клавиатура категорий"""
    keyboard = [
        [KeyboardButton("💻 IT и программирование"), KeyboardButton("🎨 Дизайн и графика")],
        [KeyboardButton("📝 Тексты и переводы"), KeyboardButton("📊 Маркетинг")],
        [KeyboardButton("🎓 Обучение"), KeyboardButton("🗣️ Консультации")],
        [KeyboardButton("🔧 Разное"), KeyboardButton("🔙 Назад в меню")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)


async def start_offer_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало предложения помощи"""
    user_id = update.effective_user.id
    user_data = db.get_user_by_telegram_id(user_id)
    
    if not user_data:
        await update.message.reply_text(
            "❌ Вы не зарегистрированы.\n"
            "Пожалуйста, зарегистрируйтесь сначала.",
            reply_markup=get_start_keyboard()
        )
        return ConversationHandler.END
    
    await update.message.reply_text(
        "🤝 *Предложить помощь*\n\n"
        "Выберите категорию, в которой вы можете помочь:",
        parse_mode='Markdown',
        reply_markup=get_categories_keyboard()
    )
    
    logger.info(f"Пользователь {user_id} начал предложение помощи")
    return OFFER_CATEGORY


async def process_offer_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка выбора категории"""
    category = update.message.text
    
    if category == "🔙 Назад в меню":
        await update.message.reply_text(
            "Действие отменено.",
            reply_markup=get_main_menu_keyboard()
        )
        return ConversationHandler.END
    
    # Проверяем валидность категории
    if category not in OFFER_CATEGORIES.values():
        await update.message.reply_text(
            "❌ Пожалуйста, выберите категорию из списка:",
            reply_markup=get_categories_keyboard()
        )
        return OFFER_CATEGORY
    
    context.user_data['offer_category'] = category
    
    await update.message.reply_text(
        f"✅ Выбрана категория: {category}\n\n"
        f"📝 *Теперь введите название вашего предложения:*\n\n"
        f"Примеры:\n"
        f"• 'Помощь с Python и Django'\n"
        f"• 'Дизайн логотипа за 24 часа'\n"
        f"• 'Переводы с английского на русский'\n\n"
        f"Введите название (максимум 100 символов):",
        parse_mode='Markdown',
        reply_markup=ReplyKeyboardMarkup([["🔙 Отмена"]], resize_keyboard=True)
    )
    
    return OFFER_TITLE


async def process_offer_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка названия предложения"""
    title = update.message.text.strip()
    
    if title == "🔙 Отмена":
        await update.message.reply_text(
            "Действие отменено.",
            reply_markup=get_main_menu_keyboard()
        )
        return ConversationHandler.END
    
    if len(title) < 3:
        await update.message.reply_text(
            "❌ Название должно содержать минимум 3 символа.\n\n"
            "Попробуйте снова:"
        )
        return OFFER_TITLE
    
    if len(title) > 100:
        await update.message.reply_text(
            "❌ Название не должно превышать 100 символов.\n\n"
            "Попробуйте снова:"
        )
        return OFFER_TITLE
    
    context.user_data['offer_title'] = title
    
    await update.message.reply_text(
        f"✅ Название: {title}\n\n"
        f"📋 *Теперь подробно опишите вашу помощь:*\n\n"
        f"Включите:\n"
        f"• Что именно вы можете сделать\n"
        f"• Ваш опыт и навыки\n"
        f"• Сроки выполнения\n"
        f"• Примеры работ (ссылки)\n"
        f"• Стоимость (если применимо)\n\n"
        f"Описание (максимум 500 символов):",
        parse_mode='Markdown',
        reply_markup=ReplyKeyboardMarkup([["🔙 Отмена"]], resize_keyboard=True)
    )
    
    return OFFER_DESCRIPTION


async def process_offer_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка описания предложения"""
    description = update.message.text.strip()
    
    if description == "🔙 Отмена":
        await update.message.reply_text(
            "Действие отменено.",
            reply_markup=get_main_menu_keyboard()
        )
        return ConversationHandler.END
    
    if len(description) < 10:
        await update.message.reply_text(
            "❌ Описание должно содержать минимум 10 символов.\n\n"
            "Попробуйте снова:"
        )
        return OFFER_DESCRIPTION
    
    if len(description) > 500:
        await update.message.reply_text(
            "❌ Описание не должно превышать 500 символов.\n\n"
            "Попробуйте снова:"
        )
        return OFFER_DESCRIPTION
    
    context.user_data['offer_description'] = description
    
    await update.message.reply_text(
        f"✅ Описание принято\n\n"
        f"📞 *Укажите контактную информацию для связи:*\n\n"
        f"Варианты:\n"
        f"• @ваш_telegram_username\n"
        f"• your.email@gmail.com\n"
        f"• +7 (XXX) XXX-XX-XX\n"
        f"• Несколько вариантов через запятую\n\n"
        f"Контакты:",
        parse_mode='Markdown',
        reply_markup=ReplyKeyboardMarkup([["🔙 Отмена"]], resize_keyboard=True)
    )
    
    return OFFER_CONTACTS


async def process_offer_contacts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Завершение и сохранение предложения помощи"""
    contacts = update.message.text.strip()
    
    if contacts == "🔙 Отмена":
        await update.message.reply_text(
            "Действие отменено.",
            reply_markup=get_main_menu_keyboard()
        )
        return ConversationHandler.END
    
    if len(contacts) < 3:
        await update.message.reply_text(
            "❌ Пожалуйста, укажите корректные контакты.\n\n"
            "Попробуйте снова:"
        )
        return OFFER_CONTACTS
    
    try:
        user = update.effective_user
        user_id = user.id
        
        # Сохраняем предложение в БД
        offer_data = {
            'user_id': user_id,
            'category': context.user_data['offer_category'],
            'title': context.user_data['offer_title'],
            'description': context.user_data['offer_description'],
            'contacts': contacts
        }
        
        # Сохраняем в файл (пока нет специальной таблицы в БД)
        import json
        import os
        from datetime import datetime
        
        os.makedirs('data', exist_ok=True)
        offers_file = 'data/offers.json'
        
        offers = []
        if os.path.exists(offers_file):
            with open(offers_file, 'r', encoding='utf-8') as f:
                offers = json.load(f)
        
        offer = {
            'id': len(offers) + 1,
            'user_id': user_id,
            'username': user.username or user.first_name,
            'category': context.user_data['offer_category'],
            'title': context.user_data['offer_title'],
            'description': context.user_data['offer_description'],
            'contacts': contacts,
            'created_at': datetime.now().isoformat(),
            'status': 'active',
            'views': 0
        }
        
        offers.append(offer)
        
        with open(offers_file, 'w', encoding='utf-8') as f:
            json.dump(offers, f, ensure_ascii=False, indent=2)
        
        # Очищаем временные данные
        context.user_data.clear()
        
        # Показываем подтверждение
        await update.message.reply_text(
            f"✅ *Предложение опубликовано!*\n\n"
            f"🆔 ID: #{offer['id']}\n"
            f"🎯 Категория: {offer['category']}\n"
            f"📝 Название: {offer['title']}\n\n"
            f"Ваше предложение видят другие пользователи.\n"
            f"Они смогут связаться с вами по указанным контактам!\n\n"
            f"Спасибо за помощь сообществу! 💚",
            parse_mode='Markdown',
            reply_markup=get_main_menu_keyboard()
        )
        
        logger.info(f"Пользователь {user_id} опубликовал предложение помощи #{offer['id']}")
        
    except Exception as e:
        logger.error(f"Ошибка при сохранении предложения: {e}")
        await update.message.reply_text(
            "❌ Ошибка при сохранении предложения.\n"
            "Попробуйте позже.",
            reply_markup=get_main_menu_keyboard()
        )
    
    return ConversationHandler.END


async def cancel_offer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отмена предложения помощи"""
    context.user_data.clear()
    await update.message.reply_text(
        "❌ Отмена предложения помощи.",
        reply_markup=get_main_menu_keyboard()
    )
    
    logger.info(f"Пользователь {update.effective_user.id} отменил предложение помощи")
    return ConversationHandler.END
