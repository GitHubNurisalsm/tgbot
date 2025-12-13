# need_help.py
"""
Модуль для системы запросов помощи - пользователи могут просить о помощи
"""
import json
import os
import logging
from datetime import datetime
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)
DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)
REQUESTS_FILE = os.path.join(DATA_DIR, "help_requests.json")

# Conversation states (должны совпадать со states.py / bot.py)
REQUEST_CATEGORY = 100
REQUEST_DESCRIPTION = 101
REQUEST_BUDGET = 102
REQUEST_DEADLINE = 103
REQUEST_CONTACTS = 104

def _load_requests():
    if not os.path.exists(REQUESTS_FILE):
        return {}
    try:
        with open(REQUESTS_FILE, 'r', encoding='utf-8') as f:
            raw = json.load(f) or {}
    except Exception as e:
        logger.exception("Failed to load requests file")
        raw = {}

    # Нормализуем ключи: если ключи в формате "req_1", приведём к "1"
    norm = {}
    for k, v in raw.items():
        nk = k
        if isinstance(k, str) and k.startswith("req_"):
            nk = k[len("req_"):]
        norm[str(nk)] = v
    return norm

def _save_requests(data: dict):
    try:
        with open(REQUESTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        logger.exception("Failed to save requests file")

class RequestSystem:
    def __init__(self):
        self._data = _load_requests()

    def _save(self):
        _save_requests(self._data)

    def get_all_active_requests(self, limit=10):
        items = list(self._data.values())
        items = [i for i in items if i.get('status') != 'closed']
        items.sort(key=lambda x: x.get('created_at',''), reverse=True)
        return items[:limit]

    def get_request_by_id(self, req_id):
        if req_id is None:
            return None
        rid = str(req_id)
        if rid.startswith("req_"):
            rid = rid[len("req_"):]
        # Try both forms
        r = self._data.get(rid)
        if r:
            return r
        return self._data.get(f"req_{rid}")

    def create_request(self, data: dict):
        # generate simple numeric id
        existing = [int(k) for k in self._data.keys() if k.isdigit()]
        next_id = str(max(existing) + 1 if existing else 1)
        self._data[next_id] = data
        self._data[next_id]['id'] = next_id
        self._data[next_id]['created_at'] = datetime.utcnow().isoformat()
        self._save()
        return next_id

    def search_requests(self, q: str, category: str = None):
        q = (q or "").strip().lower()
        results = []
        for r in self._data.values():
            if r.get('status') == 'closed':
                continue
            text = f"{r.get('description','')} {r.get('title','')}".lower()
            if category and category != "Все" and (r.get('category') or "").lower() != category.lower():
                continue
            if not q or q in text:
                results.append(r)
        return results

# Экземпляр для доступа извне
request_system = RequestSystem()

def get_request_keyboard(req_id: str, is_owner: bool = False):
    buttons = [[InlineKeyboardButton("📝 Посмотреть", callback_data=f"req_{req_id}_view"),
                InlineKeyboardButton("🤝 Откликнуться", callback_data=f"req_{req_id}_apply")]]
    if is_owner:
        buttons.append([InlineKeyboardButton("✅ Закрыть заявку", callback_data=f"req_{req_id}_close")])
    return InlineKeyboardMarkup(buttons)

# Простые conversational helpers
async def show_need_help_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🙏 Меню: отправьте ключевые слова для поиска заявок или нажмите '➕ Создать запрос', чтобы создать."
    )

async def start_create_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['new_request'] = {}
    await update.message.reply_text("Выберите категорию (введите текст):")
    return REQUEST_CATEGORY

async def process_request_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['new_request']['category'] = (update.message.text or "").strip()
    await update.message.reply_text("Опишите, в чём нуждаетесь:")
    return REQUEST_DESCRIPTION

async def process_request_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['new_request']['description'] = (update.message.text or "").strip()
    await update.message.reply_text("Укажите желаемый бюджет (или 'Бесплатно'):")
    return REQUEST_BUDGET

async def process_request_budget(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['new_request']['budget'] = (update.message.text or "").strip()
    await update.message.reply_text("Укажите срок (например: 3 дня):")
    return REQUEST_DEADLINE

async def process_request_deadline(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['new_request']['deadline'] = (update.message.text or "").strip()
    await update.message.reply_text("Укажите контакты для связи (телефон / @username / email):")
    return REQUEST_CONTACTS

async def process_request_contacts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    req = context.user_data.get('new_request', {})
    req['contacts'] = (update.message.text or "").strip()
    user = update.effective_user
    req['user_id'] = user.id
    req['username'] = user.username or user.full_name
    req_id = request_system.create_request(req)
    await update.message.reply_text(f"✅ Ваша заявка #{req_id} создана.")
    context.user_data.pop('new_request', None)
    return -1

async def cancel_request_flow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.pop('new_request', None)
    await update.message.reply_text("Создание заявки отменено.")
    return -1

# Поиск
async def search_requests(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = (update.message.text or "").strip()
    results = request_system.search_requests(q)
    if not results:
        await update.message.reply_text("По вашему запросу ничего не найдено.")
        return -1
    for r in results:
        txt = f"#{r['id']} — {r.get('description','')} ({r.get('category','-')}) — {r.get('budget','-')}"
        await update.message.reply_text(txt, reply_markup=get_request_keyboard(r['id'], is_owner=False))
    return -1
