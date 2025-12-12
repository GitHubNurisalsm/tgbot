# handlers/start.py - Обработчики базовых команд
import logging
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from keyboards import get_start_keyboard, get_main_menu_keyboard, get_back_button
from database import db

logger = logging.getLogger(__name__)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    try:
        user = update.effective_user
        user_id = user.id
        
        logger.info(f"Пользователь {user_id} ({user.username}) запустил бота")
        
        # Проверяем регистрацию
        user_data = db.get_user_by_telegram_id(user_id)
        
        if user_data:
            welcome_text = (
                f"👋 *Добро пожаловать, {user_data.get('full_name', user.first_name)}!*\n\n"
                f"⭐ Ваш рейтинг: {user_data.get('rating', 5.0)}/5.0\n"
                f"🙋 Помогли: {user_data.get('help_offered_count', 0)} раз\n"
                f"🙏 Получили: {user_data.get('help_received_count', 0)} раз\n\n"
                f"Выберите действие:"
            )
            keyboard = get_main_menu_keyboard()
        else:
            welcome_text = (
                f"👋 *Добро пожаловать в ДоброБот!*\n\n"
                f"🌟 Платформа взаимопомощи, где люди помогают друг другу.\n\n"
                f"🚀 Начните с регистрации для доступа ко всем функциям!"
            )
            keyboard = get_start_keyboard()
        
        await update.message.reply_text(
            welcome_text,
            parse_mode='Markdown',
            reply_markup=keyboard
        )
        
    except Exception as e:
        logger.error(f"Ошибка в start_command: {e}", exc_info=True)
        await update.message.reply_text(
            "❌ Произошла ошибка. Попробуйте позже.",
            reply_markup=get_start_keyboard()
        )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /help"""
    try:
        help_text = (
            "📚 *Справка по ДоброБоту*\n\n"
            "*🎯 Команды:*\n"
            "`/start` - Начать\n"
            "`/help` - Справка\n"
            "`/menu` - Меню\n"
            "`/cancel` - Отмена\n\n"
            "*📱 Функции:*\n"
            "• 🙋 Предложить помощь\n"
            "• 🙏 Попросить помощи\n"
            "• ⭐ Система рейтингов\n"
            "• 👤 Личный кабинет\n\n"
            "*📞 Поддержка:* +996556666313"
        )
        
        user_id = update.effective_user.id
        user_data = db.get_user_by_telegram_id(user_id)
        keyboard = get_main_menu_keyboard() if user_data else get_start_keyboard()
        
        await update.message.reply_text(
            help_text,
            parse_mode='Markdown',
            reply_markup=keyboard
        )
        
        logger.info(f"Пользователь {user_id} запросил справку")
        
    except Exception as e:
        logger.error(f"Ошибка в help_command: {e}")
        await update.message.reply_text("❌ Ошибка при загрузке справки")


async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /menu"""
    try:
        user_id = update.effective_user.id
        user_data = db.get_user_by_telegram_id(user_id)
        
        if user_data:
            await update.message.reply_text(
                "📋 Главное меню:",
                reply_markup=get_main_menu_keyboard()
            )
        else:
            await update.message.reply_text(
                "Сначала зарегистрируйтесь!",
                reply_markup=get_start_keyboard()
            )
        
        logger.info(f"Пользователь {user_id} запросил меню")
        
    except Exception as e:
        logger.error(f"Ошибка в menu_command: {e}")


async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отмена текущего действия"""
    try:
        user_id = update.effective_user.id
        
        # Очищаем временные данные
        if context.user_data:
            context.user_data.clear()
        
        user_data = db.get_user_by_telegram_id(user_id)
        keyboard = get_main_menu_keyboard() if user_data else get_start_keyboard()
        
        await update.message.reply_text(
            "✅ Действие отменено.",
            reply_markup=keyboard
        )
        
        logger.info(f"Пользователь {user_id} отменил действие")
        return ConversationHandler.END
        
    except Exception as e:
        logger.error(f"Ошибка в cancel_command: {e}")
