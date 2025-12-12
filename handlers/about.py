"""Информация"""
import logging
from telegram import Update
from telegram.ext import ContextTypes
from keyboards import get_start_keyboard, get_main_menu_keyboard
from database import db

logger = logging.getLogger(__name__)


async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """О проекте"""
    text = (
        "🌟 *ДоброБот*\n\n"
        "Платформа взаимопомощи, где люди помогают друг другу.\n\n"
        "✅ Функции:\n"
        "• 🙋 Предложить помощь\n"
        "• 🙏 Попросить помощи\n"
        "• ⭐ Рейтинговая система\n"
        "• 👤 Личный кабинет\n\n"
        "💡 Миссия: Объединить людей для взаимной помощи"
    )
    
    user_id = update.effective_user.id
    keyboard = get_main_menu_keyboard() if db.get_user_by_telegram_id(user_id) else get_start_keyboard()
    
    await update.message.reply_text(text, parse_mode='Markdown', reply_markup=keyboard)


async def contact_support_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Контакты поддержки"""
    try:
        support_text = (
            "📞 *Поддержка ДоброБота*\n\n"
            "📋 *Что обсудить:*\n"
            "• Проблемы и ошибки\n"
            "• Вопросы по функциям\n"
            "• Идеи и предложения\n\n"
            "📞 *Телефон/WhatsApp:* +996556666313\n"
            "📧 *Email:* support@dobrobot.example.com\n\n"
            "⏳ *Время ответа:* 2-4 часа\n\n"
            "🙏 Спасибо за обратную связь!"
        )
        
        await update.message.reply_text(support_text, parse_mode='Markdown')
        logger.info(f"📞 Пользователь запросил поддержку")
        
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")


async def show_faq_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """FAQ"""
    text = (
        "❓ *Часто задаваемые вопросы*\n\n"
        "*Как зарегистрироваться?*\n"
        "Нажмите 🚀 Регистрация\n\n"
        "*Это бесплатно?*\n"
        "Да, полностью!\n\n"
        "*Как начать помогать?*\n"
        "Создайте заявку и помогайте"
    )
    
    user_id = update.effective_user.id
    keyboard = get_main_menu_keyboard() if db.get_user_by_telegram_id(user_id) else get_start_keyboard()
    
    await update.message.reply_text(text, parse_mode='Markdown', reply_markup=keyboard)