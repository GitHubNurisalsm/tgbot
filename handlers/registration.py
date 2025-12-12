"""Регистрация"""
import logging
import hashlib
import re
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from keyboards import get_start_keyboard, get_main_menu_keyboard
from database import db
from states import REGISTER_NAME, REGISTER_PHONE, REGISTER_EMAIL, REGISTER_PASSWORD

logger = logging.getLogger(__name__)


def hash_password(pwd: str) -> str:
    """Хэширование пароля"""
    return hashlib.sha256(pwd.encode()).hexdigest()


async def start_registration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало регистрации"""
    user_id = update.effective_user.id
    
    if db.get_user_by_telegram_id(user_id):
        await update.message.reply_text("✅ Вы уже зарегистрированы!")
        return ConversationHandler.END
    
    await update.message.reply_text("Введите ваше ФИО:")
    return REGISTER_NAME


async def register_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Имя"""
    name = update.message.text.strip()
    
    if len(name) < 2:
        await update.message.reply_text("❌ Имя слишком короткое. Попробуйте снова:")
        return REGISTER_NAME
    
    context.user_data['full_name'] = name
    await update.message.reply_text("Введите номер телефона (+996555123456):")
    return REGISTER_PHONE


async def register_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Телефон"""
    phone = update.message.text.strip()
    cleaned = ''.join(filter(str.isdigit, phone))
    
    if len(cleaned) < 10:
        await update.message.reply_text("❌ Неверный номер. Попробуйте снова:")
        return REGISTER_PHONE
    
    context.user_data['phone'] = phone
    await update.message.reply_text("Введите email:")
    return REGISTER_EMAIL


async def register_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Email"""
    email = update.message.text.strip().lower()
    
    if '@' not in email or '.' not in email:
        await update.message.reply_text("❌ Неверный email. Попробуйте снова:")
        return REGISTER_EMAIL
    
    if db.get_user_by_email(email):
        await update.message.reply_text("❌ Email уже используется. Попробуйте другой:")
        return REGISTER_EMAIL
    
    context.user_data['email'] = email
    await update.message.reply_text("Придумайте пароль (минимум 6 символов):")
    return REGISTER_PASSWORD


async def register_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Пароль"""
    password = update.message.text
    
    if len(password) < 6:
        await update.message.reply_text("❌ Пароль слишком короткий. Попробуйте снова:")
        return REGISTER_PASSWORD
    
    user_id = update.effective_user.id
    pwd_hash = hash_password(password)
    
    user_db_id = db.create_user(
        telegram_id=user_id,
        full_name=context.user_data['full_name'],
        phone=context.user_data['phone'],
        email=context.user_data['email'],
        password_hash=pwd_hash
    )
    
    if not user_db_id:
        await update.message.reply_text("❌ Ошибка регистрации. Попробуйте позже.")
        return ConversationHandler.END
    
    context.user_data.clear()
    
    await update.message.reply_text(
        "✅ Регистрация успешна!\n\n"
        "Добро пожаловать в ДоброБот!",
        reply_markup=get_main_menu_keyboard()
    )
    
    return ConversationHandler.END


async def cancel_registration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отмена регистрации"""
    context.user_data.clear()
    await update.message.reply_text("❌ Регистрация отменена", reply_markup=get_start_keyboard())
    return ConversationHandler.END