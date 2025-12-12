"""Базовые команды"""
import logging
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

from keyboards import get_start_keyboard, get_main_menu_keyboard
from database import db

logger = logging.getLogger(__name__)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик /start"""
    user_id = update.effective_user.id
    user_data = db.get_user_by_telegram_id(user_id)
    
    if user_data:
        await update.message.reply_text(
            f"👋 Добро пожаловать, {user_data['full_name']}!",
            reply_markup=get_main_menu_keyboard()
        )
    else:
        await update.message.reply_text(
            "🌟 ДоброБот - платформа взаимопомощи\n\n"
            "Нажмите кнопку ниже для начала:",
            reply_markup=get_start_keyboard()
        )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик /help"""
    await update.message.reply_text(
        "📚 Справка:\n\n"
        "/start - Начать\n"
        "/menu - Меню\n"
        "/help - Помощь"
    )


async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик /menu"""
    user_id = update.effective_user.id
    user_data = db.get_user_by_telegram_id(user_id)
    
    if user_data:
        await update.message.reply_text("Меню:", reply_markup=get_main_menu_keyboard())
    else:
        await update.message.reply_text("Зарегистрируйтесь:", reply_markup=get_start_keyboard())


async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отмена"""
    context.user_data.clear()
    await update.message.reply_text("✅ Отменено")
    return ConversationHandler.END
