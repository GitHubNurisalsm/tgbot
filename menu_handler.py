# handlers/menu_handler.py
from telegram import Update
from telegram.ext import ContextTypes
from menu import get_main_menu_keyboard, is_back_to_menu

async def handle_menu_commands(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает нажатия кнопок меню"""
    text = update.message.text
    
    if is_back_to_menu(text):
        await update.message.reply_text(
            "Возвращаю в главное меню:",
            reply_markup=get_main_menu_keyboard()
        )
        return
    
    # Обработка других кнопок меню
    if text == "👤 Профиль":
        await update.message.reply_text("Здесь будет ваш профиль...")
    elif text == "⚙️ Настройки":
        await update.message.reply_text("Здесь будут настройки...")