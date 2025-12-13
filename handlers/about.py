import os
import logging
from telegram import Update
from telegram.ext import ContextTypes
from telegram.error import BadRequest

from keyboards import get_main_menu_keyboard, get_start_keyboard

logger = logging.getLogger(__name__)

SUPPORT_CONTACT = os.getenv('SUPPORT_CONTACT', '@dobrobot_support')


async def _safe_send_text(message_obj, text, **kwargs):
    """Попытка отправки с parse_mode, на ошибку повтор без parse_mode"""
    try:
        return await message_obj.reply_text(text, **kwargs)
    except BadRequest as e:
        logger.warning("BadRequest while sending text with entities: %s. Retrying without parse_mode.", e)
        try:
            # убираем парсинг сущностей — отправляем как plain text
            kwargs.pop('parse_mode', None)
            return await message_obj.reply_text(text, **kwargs)
        except Exception:
            logger.exception("Failed to send text without parse_mode")
            raise


async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает информацию о проекте (plain text, без parse_mode чтобы избежать ошибок парсинга)"""
    try:
        about_text = (
            "🤝 ДоброБот — платформа взаимопомощи.\n\n"
            "Здесь можно попросить помощи или предложить её другим людям.\n"
            "Наша цель — объединить людей для добрых дел.\n\n"
            "Если хотите — зарегистрируйтесь, чтобы публиковать/откликаться на заявки."
        )
        # Отправляем без parse_mode, чтобы избежать ошибок парсинга сущностей
        await _safe_send_text(update.message, about_text, disable_web_page_preview=True)
        logger.info(f"📖 Пользователь {update.effective_user.id} посмотрел о проекте")
    except Exception:
        logger.exception("Ошибка в about_command")
        await update.message.reply_text("Информация временно недоступна.")


async def contact_support_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает контакты поддержки (без парс-режимов)"""
    try:
        text = (
            "📞 Поддержка ДоброБота\n\n"
            f"Связаться с поддержкой: {SUPPORT_CONTACT}\n\n"
            "Опишите проблему — и мы ответим вам в ближайшее время."
        )
        await _safe_send_text(update.message, text, disable_web_page_preview=True)
        logger.info(f"📞 Пользователь {update.effective_user.id} запросил поддержку")
    except Exception:
        logger.exception("Ошибка в contact_support_command")
        await update.message.reply_text("Служба поддержки временно недоступна.")


async def show_faq_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает короткое FAQ (plain text)"""
    try:
        faq_text = (
            "❓ FAQ — Частые вопросы\n\n"
            "1) Как создать заявку?\n"
            "- Нажмите '🙏 Попросить помощи' -> заполните форму.\n\n"
            "2) Как откликнуться?\n"
            "- Откройте '📋 Активные заявки' -> нажмите 'Откликнуться' у нужной заявки.\n\n"
            "Если вопрос не решён — напишите в поддержку."
        )
        await _safe_send_text(update.message, faq_text, disable_web_page_preview=True)
        logger.info(f"❓ Пользователь {update.effective_user.id} посмотрел FAQ")
    except Exception:
        logger.exception("Ошибка в show_faq_command")
        await update.message.reply_text("FAQ временно недоступен.")