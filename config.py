import os
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Основные параметры
TOKEN = os.getenv('BOT_TOKEN')
if not TOKEN:
    raise ValueError("❌ BOT_TOKEN не найден в переменных окружения. "
                     "Создайте файл .env с строкой: BOT_TOKEN=ваш_токен")

# Пути и конфигурация
DATABASE_PATH = os.getenv('DATABASE_PATH', 'data/bot.db')
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
DEBUG_MODE = os.getenv('DEBUG_MODE', 'False').lower() == 'true'

# Константы приложения
APP_NAME = "ДоброБот"
APP_VERSION = "1.0.0"
SUPPORT_CONTACT = "+996556666313"

# Пути для данных
os.makedirs('data', exist_ok=True)
os.makedirs('logs', exist_ok=True)