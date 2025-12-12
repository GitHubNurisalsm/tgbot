"""Вход"""
import logging
import hashlib
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from keyboards import get_start_keyboard, get_main_menu_keyboard
from database import db
from states import LOGIN_EMAIL, LOGIN_PASSWORD

logger = logging.getLogger(__name__)


def hash_password(pwd: str) -> str:
    return hashlib.sha256(pwd.encode()).hexdigest()


async def start_login(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало входа"""
    user_id = update.effective_user.id
    
    if db.get_user_by_telegram_id(user_id):
        await update.message.reply_text("✅ Вы уже вошли!")
        return ConversationHandler.END
    
    context.user_data['login_attempts'] = 0
    await update.message.reply_text("Введите email:")
    return LOGIN_EMAIL


async def process_login_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Email"""
    email = update.message.text.strip().lower()
    user_data = db.get_user_by_email(email)
    
    if not user_data:
        await update.message.reply_text("❌ Email не найден. Попробуйте снова:")
        return LOGIN_EMAIL
    
    context.user_data['login_user_id'] = user_data['id']
    context.user_data['password_hash'] = user_data['password_hash']
    
    await update.message.reply_text("Введите пароль:")
    return LOGIN_PASSWORD


async def process_password_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Пароль"""
    password = update.message.text
    pwd_hash = hash_password(password)
    stored_hash = context.user_data.get('password_hash')
    
    if pwd_hash != stored_hash:
        context.user_data['login_attempts'] += 1
        
        if context.user_data['login_attempts'] >= 3:
            context.user_data.clear()
            await update.message.reply_text("❌ Превышено попыток входа", reply_markup=get_start_keyboard())
            return ConversationHandler.END
        
        await update.message.reply_text("❌ Неверный пароль. Попробуйте снова:")
        return LOGIN_PASSWORD
    
    user_id = update.effective_user.id
    login_user_id = context.user_data.get('login_user_id')
    db.update_user(login_user_id, telegram_id=user_id)
    
    context.user_data.clear()
    
    await update.message.reply_text(
        "✅ Вход выполнен!",
        reply_markup=get_main_menu_keyboard()
    )
    
    return ConversationHandler.END


async def cancel_login(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отмена"""
    context.user_data.clear()
    await update.message.reply_text("❌ Вход отменен", reply_markup=get_start_keyboard())
    return ConversationHandler.END