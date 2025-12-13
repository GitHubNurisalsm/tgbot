"""
ДоброБот - Платформа взаимопомощи
Полная интеграция всех функций
"""
import logging
import sys
import os
import json
from datetime import datetime

os.makedirs('logs', exist_ok=True)
os.makedirs('data', exist_ok=True)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('logs/bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ===== КОНФИГУРАЦИЯ =====
try:
    from dotenv import load_dotenv
    load_dotenv()
    TOKEN = os.getenv('BOT_TOKEN')
    if not TOKEN:
        raise ValueError("BOT_TOKEN не найден в .env")
except Exception as e:
    logger.error(f"❌ Ошибка конфигурации: {e}")
    sys.exit(1)

from telegram.ext import (
    Application, CommandHandler, MessageHandler, ConversationHandler, filters, CallbackQueryHandler
)

# ===== ИМПОРТЫ ОБРАБОТЧИКОВ =====
from handlers.start import start_command, help_command, menu_command, cancel_command
from handlers.registration import (
    start_registration, register_name, register_phone, register_confirm_phone,
    register_verify_phone_code, register_email, register_password, cancel_registration
)
from handlers.login import (
    start_login, process_login_input, process_password_input, cancel_login
)
from handlers.about import about_command, contact_support_command, show_faq_command
from handlers.offer_help import (
    start_offer_help, process_offer_category, process_offer_title,
    process_offer_description, process_offer_contacts, cancel_offer
)

# Импортируем персонал
from personal import show_profile, handle_profile_callback, save_edited_field, cancel_edit
from states import EDIT_NAME, EDIT_AGE, EDIT_EMAIL, EDIT_PHONE

# Импортируем функционал "Попросить помощи" и дополнительные сущности
# #region agent log
import json
try:
    with open('/Users/macbook/Documents/Inai/tgbot/.cursor/debug.log', 'a', encoding='utf-8') as f:
        f.write(json.dumps({"id":"log_import_start","timestamp":int(__import__('time').time()*1000),"location":"bot.py:59","message":"Starting need_help import","data":{"requested_functions":["show_need_help_menu","start_create_request","process_request_category","process_request_description","process_request_budget","process_request_deadline","process_request_contacts","cancel_request_flow","REQUEST_CATEGORY","REQUEST_DESCRIPTION","REQUEST_BUDGET","REQUEST_DEADLINE","REQUEST_CONTACTS","handle_request_callback","request_system","get_request_keyboard","search_requests","show_requests_in_category"]},"sessionId":"debug-session","runId":"run1","hypothesisId":"A"}) + '\n')
except: pass
# #endregion
try:
    import need_help
    # #region agent log
    try:
        with open('/Users/macbook/Documents/Inai/tgbot/.cursor/debug.log', 'a', encoding='utf-8') as f:
            f.write(json.dumps({"id":"log_need_help_loaded","timestamp":int(__import__('time').time()*1000),"location":"bot.py:59","message":"need_help module loaded successfully","data":{"available_attrs":list(dir(need_help))},"sessionId":"debug-session","runId":"run1","hypothesisId":"A"}) + '\n')
    except: pass
    # #endregion
    # #region agent log
    try:
        with open('/Users/macbook/Documents/Inai/tgbot/.cursor/debug.log', 'a', encoding='utf-8') as f:
            has_handle = hasattr(need_help, 'handle_request_callback')
            has_show = hasattr(need_help, 'show_requests_in_category')
            f.write(json.dumps({"id":"log_check_functions","timestamp":int(__import__('time').time()*1000),"location":"bot.py:59","message":"Checking if functions exist in need_help","data":{"has_handle_request_callback":has_handle,"has_show_requests_in_category":has_show},"sessionId":"debug-session","runId":"run1","hypothesisId":"A"}) + '\n')
    except: pass
    # #endregion
    from need_help import (
        show_need_help_menu, start_create_request, process_request_category, process_request_description,
        process_request_budget, process_request_deadline, process_request_contacts, cancel_request_flow,
        REQUEST_CATEGORY, REQUEST_DESCRIPTION, REQUEST_BUDGET, REQUEST_DEADLINE, REQUEST_CONTACTS,
        request_system, get_request_keyboard,
        search_requests
    )
    # #region agent log
    try:
        with open('/Users/macbook/Documents/Inai/tgbot/.cursor/debug.log', 'a', encoding='utf-8') as f:
            f.write(json.dumps({"id":"log_partial_import_success","timestamp":int(__import__('time').time()*1000),"location":"bot.py:59","message":"Partial import from need_help succeeded","data":{"imported":["show_need_help_menu","start_create_request","process_request_category","process_request_description","process_request_budget","process_request_deadline","process_request_contacts","cancel_request_flow","REQUEST_CATEGORY","REQUEST_DESCRIPTION","REQUEST_BUDGET","REQUEST_DEADLINE","REQUEST_CONTACTS","request_system","get_request_keyboard","search_requests"]},"sessionId":"debug-session","runId":"run1","hypothesisId":"A"}) + '\n')
    except: pass
    # #endregion
    # Try to import handle_request_callback from requests instead
    # #region agent log
    try:
        with open('/Users/macbook/Documents/Inai/tgbot/.cursor/debug.log', 'a', encoding='utf-8') as f:
            f.write(json.dumps({"id":"log_trying_requests_import","timestamp":int(__import__('time').time()*1000),"location":"bot.py:59","message":"Attempting to import handle_request_callback from requests","data":{},"sessionId":"debug-session","runId":"run1","hypothesisId":"A"}) + '\n')
    except: pass
    # #endregion
    try:
        import requests as requests_module
        # #region agent log
        try:
            with open('/Users/macbook/Documents/Inai/tgbot/.cursor/debug.log', 'a', encoding='utf-8') as f:
                has_handle_in_requests = hasattr(requests_module, 'handle_request_callback')
                f.write(json.dumps({"id":"log_check_requests_module","timestamp":int(__import__('time').time()*1000),"location":"bot.py:59","message":"Checking requests module for handle_request_callback","data":{"has_handle_request_callback":has_handle_in_requests,"available_attrs":list(dir(requests_module))[:20]},"sessionId":"debug-session","runId":"run1","hypothesisId":"A"}) + '\n')
        except: pass
        # #endregion
        if hasattr(requests_module, 'handle_request_callback'):
            handle_request_callback = requests_module.handle_request_callback
            # #region agent log
            try:
                with open('/Users/macbook/Documents/Inai/tgbot/.cursor/debug.log', 'a', encoding='utf-8') as f:
                    f.write(json.dumps({"id":"log_import_success_requests","timestamp":int(__import__('time').time()*1000),"location":"bot.py:59","message":"Successfully imported handle_request_callback from requests","data":{},"sessionId":"debug-session","runId":"run1","hypothesisId":"A"}) + '\n')
            except: pass
            # #endregion
        else:
            # #region agent log
            try:
                with open('/Users/macbook/Documents/Inai/tgbot/.cursor/debug.log', 'a', encoding='utf-8') as f:
                    f.write(json.dumps({"id":"log_handle_not_found","timestamp":int(__import__('time').time()*1000),"location":"bot.py:59","message":"handle_request_callback not found in requests module","data":{},"sessionId":"debug-session","runId":"run1","hypothesisId":"A"}) + '\n')
            except: pass
            # #endregion
            handle_request_callback = None
    except Exception as e:
        # #region agent log
        try:
            with open('/Users/macbook/Documents/Inai/tgbot/.cursor/debug.log', 'a', encoding='utf-8') as f:
                f.write(json.dumps({"id":"log_requests_import_error","timestamp":int(__import__('time').time()*1000),"location":"bot.py:59","message":"Error importing from requests","data":{"error":str(e)},"sessionId":"debug-session","runId":"run1","hypothesisId":"A"}) + '\n')
        except: pass
        # #endregion
        handle_request_callback = None
    # show_requests_in_category is not used, so we skip it
    show_requests_in_category = None
except ImportError as e:
    # #region agent log
    try:
        with open('/Users/macbook/Documents/Inai/tgbot/.cursor/debug.log', 'a', encoding='utf-8') as f:
            f.write(json.dumps({"id":"log_import_error","timestamp":int(__import__('time').time()*1000),"location":"bot.py:59","message":"ImportError from need_help","data":{"error":str(e),"error_type":type(e).__name__},"sessionId":"debug-session","runId":"run1","hypothesisId":"A"}) + '\n')
    except: pass
    # #endregion
    raise

from states import (
    REGISTER_NAME, REGISTER_PHONE, REGISTER_CONFIRM_PHONE, REGISTER_VERIFY_PHONE_CODE,
    REGISTER_EMAIL, REGISTER_PASSWORD,
    LOGIN_EMAIL, LOGIN_PASSWORD,
    OFFER_CATEGORY, OFFER_TITLE, OFFER_DESCRIPTION, OFFER_CONTACTS
)

from keyboards import get_start_keyboard, get_main_menu_keyboard
from rating import rating_system


async def error_handler(update, context):
    """Обработчик глобальных ошибок"""
    logger.error(f"Ошибка: {context.error}", exc_info=True)


# ===== ОБРАБОТЧИКИ ГЛАВНОГО МЕНЮ =====

async def handle_offer_help(update, context):
    """🙋‍♂️ Предложить помощь — запускает процесс создания предложения помощи"""
    logger.info(f"handle_offer_help вызван для пользователя {update.effective_user.id if update.effective_user else 'unknown'}")
    # Запускаем процесс создания предложения помощи
    return await start_offer_help(update, context)


async def handle_need_help(update, context):
    """🙏 Попросить помощи — показывает меню или запускает создание запроса"""
    logger.info(f"handle_need_help вызван для пользователя {update.effective_user.id if update.effective_user else 'unknown'}")
    await show_need_help_menu(update, context)
    logger.info(f"Пользователь {update.effective_user.id} открыл меню 'Нужна помощь'")


async def handle_profile(update, context):
    """👤 Личный кабинет"""
    logger.info(f"handle_profile вызван для пользователя {update.effective_user.id if update.effective_user else 'unknown'}")
    user_id = update.effective_user.id
    from database import db
    
    user_data = db.get_user_by_telegram_id(user_id)
    
    if not user_data:
        await update.message.reply_text(
            "❌ Вы не зарегистрированы.\n"
            "Пожалуйста, зарегистрируйтесь сначала.",
            reply_markup=get_start_keyboard()
        )
        return
    
    profile_text = (
        f"👤 Личный кабинет\n\n"
        f"📛 Имя: {user_data.get('full_name', 'Не указано')}\n"
        f"📧 Email: {user_data.get('email', 'Не указан')}\n"
        f"📱 Телефон: {user_data.get('phone', 'Не указан')}\n"
        f"⭐ Рейтинг: {user_data.get('rating', 5.0)}/5.0\n"
        f"🙋 Помогли: {user_data.get('help_offered_count', 0)} раз\n"
        f"🙏 Получили: {user_data.get('help_received_count', 0)} раз\n\n"
        f"Функции редактирования в разработке."
    )
    
    await update.message.reply_text(
        profile_text,
        reply_markup=get_main_menu_keyboard()
    )
    logger.info(f"Пользователь {user_id} открыл профиль")


async def handle_rating(update, context):
    """⭐ Общий рейтинг волонтёров (топ и статистика)"""
    logger.info(f"handle_rating вызван для пользователя {update.effective_user.id if update.effective_user else 'unknown'}")
    try:
        top_users = rating_system.get_top_users(limit=10)
        # Подсчёт средней оценки по всем пользователям (если есть данные)
        try:
            with open(rating_system.ratings_file, 'r', encoding='utf-8') as f:
                all_ratings = json.load(f)
            ratings_values = [v['current_rating'] for v in all_ratings.values() if v.get('total_reviews', 0) > 0]
            avg_rating = round(sum(ratings_values) / len(ratings_values), 2) if ratings_values else 0.0
            rated_users_count = len([1 for v in all_ratings.values() if v.get('total_reviews', 0) > 0])
        except Exception:
            avg_rating = 0.0
            rated_users_count = 0

        if not top_users:
            await update.message.reply_text(
                f"⭐ Общий рейтинг волонтёров\n\n"
                f"Пока нет достаточных данных (не менее 3 отзывов) для формирования топа.\n\n"
                f"Средний рейтинг: {avg_rating}/5.0\n"
                f"Оценённых пользователей: {rated_users_count}",
                reply_markup=get_main_menu_keyboard()
            )
            return

        text = f"🏆 Топ волонтёров (по рейтингу)\n\n"
        text += f"📊 Средний рейтинг: {avg_rating}/5.0\n"
        text += f"👥 Оценённых пользователей: {rated_users_count}\n\n"

        for i, u in enumerate(top_users, 1):
            text += f"{i}. Пользователь #{u['user_id']} — {u['rating']}/5.0 ({u['total_reviews']} отзывов) — уровень {u.get('level','-')}\n"

        await update.message.reply_text(text, reply_markup=get_main_menu_keyboard())
    except Exception as e:
        logger.error(f"Ошибка в handle_rating: {e}", exc_info=True)
        await update.message.reply_text("❌ Ошибка при формировании рейтинга", reply_markup=get_main_menu_keyboard())


async def handle_requests(update, context):
    """📋 Показать последние активные заявки"""
    logger.info(f"handle_requests вызван для пользователя {update.effective_user.id if update.effective_user else 'unknown'}")
    user = update.effective_user
    if not user:
        return await update.message.reply_text("❌ Ошибка пользователя")

    # Получаем последние активные заявки
    requests = request_system.get_all_active_requests(limit=10)

    if not requests:
        await update.message.reply_text(
            "📭 Пока нет активных заявок. Попробуйте позже или создайте свою.",
            reply_markup=get_main_menu_keyboard()
        )
        return

    await update.message.reply_text(
        f"📋 Найдено {len(requests)} активных заявок (показаны последние):",
        reply_markup=get_main_menu_keyboard()
    )

    for req in requests:
        created = req.get('created_at', '')
        try:
            created_str = datetime.fromisoformat(created).strftime('%d.%m.%Y %H:%M') if created else ''
        except Exception:
            created_str = created

        text = (
            f"🆔 Запрос #{req['id']}\n"
            f"👤 Автор: {req.get('username', '—')}\n"
            f"🎯 Категория: {req.get('category', '—')}\n"
            f"💰 Бюджет: {req.get('budget', 'Не указан')}\n"
            f"⏰ Срок: {req.get('deadline', 'Не указан')}\n\n"
            f"{(req.get('description') or '')[:400]}{('...' if len(req.get('description',''))>400 else '')}\n\n"
            f"📅 Создан: {created_str}"
        )

        await update.message.reply_text(
            text,
            reply_markup=get_request_keyboard(req['id'], is_owner=(user.id == req.get('user_id')))
        )


async def main_menu_handler(update, context):
    """Основной обработчик меню - распределяет нажатия кнопок"""
    if not update.message:
        return
    
    text = update.message.text
    user_id = update.effective_user.id if update.effective_user else None
    
    logger.info(f"Обработка сообщения от пользователя {user_id}: '{text}'")
    
    if text == "🙋‍♂️ Предложить помощь":
        await handle_offer_help(update, context)
    elif text == "🙏 Попросить помощи":
        await handle_need_help(update, context)
    elif text == "👤 Личный кабинет":
        await handle_profile(update, context)
    elif text == "⭐ Рейтинг":
        await handle_rating(update, context)
    elif text == "📋 Активные заявки":
        await handle_requests(update, context)
    elif text == "📞 Поддержка":
        await contact_support_command(update, context)
    else:
        # Если ничего не совпадает, показываем справку
        logger.debug(f"Неизвестная команда: '{text}', показываем справку")
        await help_command(update, context)


# Импортируем обработчики для сообщений/заявок (без in-bot chat)
from requests import handle_requests_callback

def register_handlers(app):
    """Регистрирует все обработчики в приложении"""
    
    logger.info("📝 Регистрация обработчиков...")
    
    # ===== БАЗОВЫЕ КОМАНДЫ =====
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("menu", menu_command))
    app.add_handler(CommandHandler("cancel", cancel_command))
    
    # ===== ПРОФИЛЬ (Conversation + Callback) =====
    # Используем handle_profile вместо show_profile для entry point, чтобы показывать главное меню
    profile_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(handle_profile_callback, pattern="^(edit_|profile_settings|back_to_profile|back_to_menu|toggle_notifications)")
        ],
        states={
            EDIT_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_edited_field)],
            EDIT_AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_edited_field)],
            EDIT_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_edited_field)],
            EDIT_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_edited_field)],
        },
        fallbacks=[
            CallbackQueryHandler(cancel_edit, pattern="^back_to_menu$"),
            CommandHandler('cancel', cancel_edit)
        ],
        allow_reentry=True
    )
    app.add_handler(profile_conv)
    
    logger.info("  ✅ Профиль зарегистрирован")
    
    # ===== РЕГИСТРАЦИЯ =====
    registration_conv = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex("^🚀 Регистрация$"), start_registration),
            CommandHandler("register", start_registration)
        ],
        states={
            REGISTER_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_name)],
            REGISTER_PHONE: [
                MessageHandler(filters.CONTACT, register_phone),
                MessageHandler(filters.TEXT & ~filters.COMMAND, register_phone)
            ],
            REGISTER_CONFIRM_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_confirm_phone)],
            REGISTER_VERIFY_PHONE_CODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_verify_phone_code)],
            REGISTER_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_email)],
            REGISTER_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_password)],
        },
        fallbacks=[
            CommandHandler('cancel', cancel_registration),
            MessageHandler(filters.Regex("^🔙 Назад$"), cancel_registration)
        ]
    )
    app.add_handler(registration_conv)
    
    logger.info("  ✅ Регистрация зарегистрирована")
    
    # ===== ВХОД =====
    login_conv = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex("^🔐 Вход$"), start_login),
            CommandHandler("login", start_login)
        ],
        states={
            LOGIN_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_login_input)],
            LOGIN_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_password_input)],
        },
        fallbacks=[
            CommandHandler('cancel', cancel_login),
            MessageHandler(filters.Regex("^🔙 Назад$"), cancel_login)
        ]
    )
    app.add_handler(login_conv)
    
    logger.info("  ✅ Вход зарегистрирован")
    
    # ===== ИНФОРМАЦИОННЫЕ КОМАНДЫ =====
    app.add_handler(MessageHandler(filters.Regex("^ℹ️ О проекте$"), about_command))
    app.add_handler(MessageHandler(filters.Regex("^📞 Поддержка$"), contact_support_command))
    app.add_handler(MessageHandler(filters.Regex("^❓ FAQ$"), show_faq_command))
    
    logger.info("  ✅ Информационные команды зарегистрированы")
    
    # ===== КОМАНДЫ ЗАЯВОК =====
    app.add_handler(CallbackQueryHandler(handle_request_callback))
    logger.info("  ✅ CallbackQueryHandler для запросов зарегистрирован")

    # ===== ПОПРОСИТЬ ПОМОЩИ =====
    need_help_conv = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex("^🙏 Попросить помощи$"), start_create_request),
            MessageHandler(filters.Regex("^➕ Создать запрос$"), start_create_request),
            MessageHandler(filters.Regex("^🔍 Искать запросы$"), search_requests)
        ],
        states={
            REQUEST_CATEGORY: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_request_category)],
            REQUEST_DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_request_description)],
            REQUEST_BUDGET: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_request_budget)],
            REQUEST_DEADLINE: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_request_deadline)],
            REQUEST_CONTACTS: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_request_contacts)],
        },
        fallbacks=[CommandHandler('cancel', cancel_request_flow), MessageHandler(filters.Regex("^🔙 Назад$"), cancel_request_flow)]
    )
    app.add_handler(need_help_conv)
    logger.info("  ✅ 'Попросить помощи' зарегистрирована")
    
    # ===== ПРЕДЛОЖИТЬ ПОМОЩЬ =====
    offer_help_conv = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex("^🙋‍♂️ Предложить помощь$"), start_offer_help),
        ],
        states={
            OFFER_CATEGORY: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_offer_category)],
            OFFER_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_offer_title)],
            OFFER_DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_offer_description)],
            OFFER_CONTACTS: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_offer_contacts)],
        },
        fallbacks=[
            CommandHandler('cancel', cancel_offer),
            MessageHandler(filters.Regex("^🔙 Назад$|^🔙 Отмена$|^🔙 Назад в меню$"), cancel_offer)
        ]
    )
    app.add_handler(offer_help_conv)
    logger.info("  ✅ 'Предложить помощь' зарегистрирована")

    # ===== ГЛАВНОЕ МЕНЮ (ДОЛЖНО БЫТЬ ПОСЛЕДНИМ!) =====
    # Сначала регистрируем специфичные обработчики для каждой кнопки главного меню
    # Это гарантирует, что они будут обработаны до общего обработчика
    # Примечание: "🙋‍♂️ Предложить помощь" обрабатывается ConversationHandler выше
    app.add_handler(MessageHandler(filters.Regex("^🙏 Попросить помощи$"), handle_need_help))
    app.add_handler(MessageHandler(filters.Regex("^👤 Личный кабинет$"), handle_profile))
    app.add_handler(MessageHandler(filters.Regex("^⭐ Рейтинг$"), handle_rating))
    app.add_handler(MessageHandler(filters.Regex("^📋 Активные заявки$"), handle_requests))
    app.add_handler(MessageHandler(filters.Regex("^📞 Поддержка$"), contact_support_command))
    logger.info("  ✅ Обработчики кнопок главного меню зарегистрированы")
    
    # Глобальная "Назад" -> возвращаем в главное меню (если не в ConversationHandler)
    app.add_handler(MessageHandler(filters.Regex(r"^(🔙 Назад|🔙 Назад в меню|Назад)$"), menu_command))
    logger.info("  ✅ 'Назад' глобальный handler зарегистрирован")
    
    # Общий обработчик для остальных текстовых сообщений (должен быть последним)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, main_menu_handler))
    
    logger.info("  ✅ Главное меню зарегистрировано")
    
    # ===== ОБРАБОТЧИК ОШИБОК =====
    app.add_error_handler(error_handler)
    
    logger.info("✅ Все обработчики успешно зарегистрированы!")


def main():
    """Главная функция запуска бота"""
    try:
        logger.info("=" * 70)
        logger.info("🤖 ДоброБот запускается...")
        logger.info("=" * 70)
        
        # Создаем приложение
        app = Application.builder().token(TOKEN).build()
        
        # Регистрируем все обработчики
        register_handlers(app)
        
        logger.info("=" * 70)
        logger.info("✅ ДоброБот готов к работе!")
        logger.info("⏰ Ожидание входящих сообщений...")
        logger.info("=" * 70)
        
        # Запускаем бота
        app.run_polling(allowed_updates=['message', 'callback_query'])
        
    except KeyboardInterrupt:
        logger.info("⏹️  Бот остановлен пользователем")
        sys.exit(0)
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}", exc_info=True)
        print(f"\n❌ ОШИБКА: {e}")
        print("\n📋 Что проверить:")
        print("1. ✅ Файл .env с BOT_TOKEN существует")
        print("2. ✅ Все зависимости установлены (pip install -r requirements.txt)")
        print("3. ✅ Структура папок правильная (handlers/, data/, logs/)")
        print("4. ✅ Все файлы обработчиков на месте")
        sys.exit(1)


if __name__ == '__main__':
    main()