"""Регистрация"""
import os
import json
import hashlib
import logging
import re
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

from keyboards import get_main_menu_keyboard, get_contact_request_keyboard, get_confirmation_keyboard, get_registration_keyboard
from personal import show_profile

from database import db
from states import (
    REGISTER_NAME, REGISTER_PHONE, REGISTER_CONFIRM_PHONE, REGISTER_VERIFY_PHONE_CODE,
    REGISTER_EMAIL, REGISTER_PASSWORD
)
from sms_service import generate_and_send_code

logger = logging.getLogger(__name__)

async def start_registration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    logger.info(f"Пользователь {user.id} начал регистрацию")
    context.user_data['registration'] = {}
    await update.message.reply_text(
        "Введите, пожалуйста, ваше имя и фамилию (например: Иван Иванов):",
        reply_markup=get_registration_keyboard()
    )
    return REGISTER_NAME

async def register_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (update.message.text or "").strip()
    if not text:
        await update.message.reply_text("Имя не распознано. Попробуйте ещё раз.")
        return REGISTER_NAME
    context.user_data['registration']['full_name'] = text
    await update.message.reply_text(
        "Отлично! Теперь укажите номер телефона (или нажмите кнопку, чтобы поделиться контактом):",
        reply_markup=get_contact_request_keyboard()
    )
    return REGISTER_PHONE

async def register_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    phone = None
    if update.message.contact:
        phone = update.message.contact.phone_number
    else:
        phone = (update.message.text or "").strip()
    # normalize phone
    phone = re.sub(r"[^\d\+]", "", phone or "")
    context.user_data['registration']['phone'] = phone or None

    if phone:
        await update.message.reply_text(
            f"Вы ввели номер: {phone}. Подтверждаете?",
            reply_markup=get_confirmation_keyboard()
        )
        return REGISTER_CONFIRM_PHONE
    else:
        await update.message.reply_text(
            "Номер не распознан. Пожалуйста, введите телефон формата +7xxxxxxxxxx или нажмите кнопку 'Поделиться контактом'.",
            reply_markup=get_contact_request_keyboard()
        )
        return REGISTER_PHONE

async def register_confirm_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (update.message.text or "").strip().lower()
    if text in ["✅ да", "да", "подтверждаю", "да,"]:
        # Отправляем SMS с кодом подтверждения
        phone = context.user_data.get('registration', {}).get('phone')
        if not phone:
            await update.message.reply_text(
                "❌ Ошибка: номер телефона не найден. Введите телефон снова:",
                reply_markup=get_contact_request_keyboard()
            )
            return REGISTER_PHONE
        
        # Генерируем и отправляем код
        logger.info(f"Попытка отправить SMS код на номер {phone}")
        code, success, message = generate_and_send_code(phone)
        
        if success and code:
            # Сохраняем код для проверки
            context.user_data['registration']['sms_code'] = code
            context.user_data['registration']['sms_attempts'] = 0
            
            # Проверяем, настроен ли SMS сервис
            from sms_service import sms_service
            is_dev_mode = not sms_service.enabled
            
            if is_dev_mode:
                # В режиме разработки показываем код пользователю
                await update.message.reply_text(
                    f"📱 {message}\n\n"
                    f"⚠️ Режим разработки: SMS сервис не настроен.\n"
                    f"🔐 Ваш код подтверждения: <code>{code}</code>\n\n"
                    f"Введите этот код для продолжения:",
                    parse_mode='HTML'
                )
            else:
                await update.message.reply_text(
                    f"📱 {message}\n\n"
                    f"Введите код подтверждения, который мы отправили на номер {phone}:"
                )
            return REGISTER_VERIFY_PHONE_CODE
        else:
            logger.error(f"Не удалось отправить SMS: success={success}, message={message}, code={code}")
            await update.message.reply_text(
                f"❌ Не удалось отправить SMS: {message}\n\n"
                f"Попробуйте ввести телефон снова:",
                reply_markup=get_contact_request_keyboard()
            )
            return REGISTER_PHONE
    else:
        await update.message.reply_text(
            "Хорошо, введите телефон снова или нажмите кнопку, чтобы поделиться контактом:",
            reply_markup=get_contact_request_keyboard()
        )
        return REGISTER_PHONE

async def register_verify_phone_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Проверяет введённый SMS код"""
    entered_code = (update.message.text or "").strip()
    reg = context.user_data.get('registration', {})
    expected_code = reg.get('sms_code')
    attempts = reg.get('sms_attempts', 0)
    
    if not expected_code:
        # Код не был сгенерирован, возвращаемся к вводу телефона
        await update.message.reply_text(
            "❌ Ошибка: код не был отправлен. Введите телефон снова:",
            reply_markup=get_contact_request_keyboard()
        )
        return REGISTER_PHONE
    
    # Проверяем код
    if entered_code == expected_code:
        # Код верный, переходим к email
        reg['phone_verified'] = True
        reg.pop('sms_code', None)
        reg.pop('sms_attempts', None)
        await update.message.reply_text(
            "✅ Номер телефона успешно подтверждён!\n\n"
            "Теперь укажите e-mail (или оставьте пустым):"
        )
        return REGISTER_EMAIL
    else:
        # Неверный код
        attempts += 1
        reg['sms_attempts'] = attempts
        
        if attempts >= 3:
            # Превышено количество попыток
            reg.pop('sms_code', None)
            reg.pop('sms_attempts', None)
            await update.message.reply_text(
                "❌ Превышено количество попыток ввода кода.\n\n"
                "Введите телефон снова, и мы отправим новый код:",
                reply_markup=get_contact_request_keyboard()
            )
            return REGISTER_PHONE
        else:
            remaining = 3 - attempts
            await update.message.reply_text(
                f"❌ Неверный код. Осталось попыток: {remaining}\n\n"
                f"Введите код подтверждения ещё раз:"
            )
            return REGISTER_VERIFY_PHONE_CODE

async def register_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (update.message.text or "").strip().lower()
    context.user_data['registration']['email'] = text or None

    if text:
        # simple validation
        if not re.match(r"^[^@]+@[^@]+\.[^@]+$", text):
            await update.message.reply_text("Похоже, адрес указан неверно. Попробуйте ещё раз:")
            return REGISTER_EMAIL
        # Email валиден, сразу переходим к паролю
        await update.message.reply_text("Email сохранён. Придумайте пароль (минимум 6 символов):")
        return REGISTER_PASSWORD
    else:
        await update.message.reply_text("Хорошо, пропускаем email. Придумайте пароль (минимум 6 символов):")
        return REGISTER_PASSWORD

async def register_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pwd = (update.message.text or "").strip()
    if len(pwd) < 6:
        await update.message.reply_text("Пароль слишком короткий, минимум 6 символов. Попробуйте ещё раз:")
        return REGISTER_PASSWORD

    hashed = hashlib.sha256(pwd.encode('utf-8')).hexdigest()
    reg = context.user_data.get('registration', {})
    reg['password_hash'] = hashed
    reg['telegram_id'] = str(update.effective_user.id)
    reg['username'] = update.effective_user.username or ""
    reg['created_at'] = datetime.utcnow().isoformat()
    reg.setdefault('rating', 5.0)
    reg.setdefault('help_offered_count', 0)
    reg.setdefault('help_received_count', 0)

    saved = False
    try:
        if hasattr(db, "create_or_update_user"):
            db.create_or_update_user(reg)
            saved = True
    except Exception as e:
        logger.error(f"Ошибка записи в DB: {e}", exc_info=True)
        saved = False

    if not saved:
        users_path = os.path.join("data", "users.json")
        os.makedirs(os.path.dirname(users_path), exist_ok=True)
        try:
            loaded = {}
            if os.path.exists(users_path):
                with open(users_path, 'r', encoding='utf-8') as f:
                    txt = f.read().strip()
                    loaded = json.loads(txt) if txt else {}
            loaded[reg['telegram_id']] = reg
            with open(users_path, 'w', encoding='utf-8') as f:
                json.dump(loaded, f, ensure_ascii=False, indent=2)
            saved = True
        except Exception as e:
            logger.error(f"Ошибка при сохранении профиля в файл: {e}", exc_info=True)
            saved = False

    # Завершение регистрации и показ главного меню
    if saved:
        welcome_text = (
            f"✅ Регистрация завершена!\n\n"
            f"👋 Добро пожаловать, {reg.get('full_name', 'пользователь')}!\n\n"
            f"Теперь вы можете использовать все функции бота:\n"
            f"🙋‍♂️ Предложить помощь\n"
            f"🙏 Попросить помощи\n"
            f"👤 Личный кабинет\n"
            f"⭐ Рейтинг\n"
            f"📋 Активные заявки\n\n"
            f"Выберите действие:"
        )
        await update.message.reply_text(
            welcome_text,
            reply_markup=get_main_menu_keyboard()
        )
        logger.info(f"Пользователь {reg['telegram_id']} успешно зарегистрирован")
    else:
        await update.message.reply_text(
            "❌ Ошибка при сохранении профиля. Попробуйте позже.",
            reply_markup=get_main_menu_keyboard()
        )

    # Clean up и завершение ConversationHandler
    context.user_data.pop('registration', None)
    # Явно очищаем все данные регистрации
    for key in list(context.user_data.keys()):
        if key.startswith('registration') or key.startswith('sms_'):
            context.user_data.pop(key, None)
    logger.info(f"Регистрация завершена, ConversationHandler завершён для пользователя {reg.get('telegram_id')}")
    return ConversationHandler.END

async def cancel_registration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.pop('registration', None)
    await update.message.reply_text("Регистрация отменена.", reply_markup=get_main_menu_keyboard())
    return ConversationHandler.END