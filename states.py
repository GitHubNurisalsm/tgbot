# states.py - Константы состояний для ConversationHandler
# Используются для управления многошаговыми диалогами

# ========== РЕГИСТРАЦИЯ ==========
# Шаги регистрации нового пользователя
REGISTER_NAME, REGISTER_PHONE, REGISTER_CONFIRM_PHONE, REGISTER_VERIFY_PHONE_CODE, REGISTER_EMAIL, REGISTER_CONFIRM_EMAIL, REGISTER_PASSWORD = range(10, 17)

# ========== ВХОД В СИСТЕМУ ==========
# Шаги процесса входа
LOGIN_EMAIL, LOGIN_PASSWORD = range(20, 22)

# ========== ПРЕДЛОЖИТЬ ПОМОЩЬ ==========
# Шаги создания предложения помощи
OFFER_CATEGORY, OFFER_TITLE, OFFER_DESCRIPTION, OFFER_CONTACTS = range(40, 44)

# ========== ПОПРОСИТЬ ПОМОЩИ ==========
# Шаги создания заявки "Попросить помощи"
REQUEST_CATEGORY, REQUEST_DESCRIPTION, REQUEST_BUDGET, REQUEST_DEADLINE, REQUEST_CONTACTS = range(50, 55)

# ========== РЕДАКТИРОВАНИЕ ПРОФИЛЯ ==========
# Шаги редактирования профиля пользователя
EDIT_NAME, EDIT_AGE, EDIT_EMAIL, EDIT_PHONE = range(30, 34)

# ========== СОЗДАНИЕ ОТКЛИКА ==========
# Шаги создания отклика на заявку
RESPONSE_CHOOSE_REQUEST, RESPONSE_WRITE_MESSAGE = range(22, 24)

# ========== ОБРАТНАЯ СВЯЗЬ И ОЦЕНКА ==========
# Шаги оставления отзыва и оценки
FEEDBACK_RATING, FEEDBACK_COMMENT = range(24, 26)

# ========== ПОИСК ЗАЯВОК ==========
# Шаги поиска заявок по фильтрам
SEARCH_CATEGORY, SEARCH_LOCATION, SEARCH_RADIUS = range(26, 29)

# ========== АДМИН ПАНЕЛЬ ==========
# Шаги административных действий
ADMIN_CHOOSE_ACTION, ADMIN_SEND_NOTIFICATION, ADMIN_MODERATE_REQUEST = range(29, 32)

# ========== СОЗДАНИЕ УВЕДОМЛЕНИЯ ==========
# Шаги создания массового уведомления
NOTIFICATION_TITLE, NOTIFICATION_TEXT, NOTIFICATION_CONFIRM = range(32, 35)

# ========== ВОССТАНОВЛЕНИЕ ПАРОЛЯ ==========
# Шаги восстановления пароля
RESET_EMAIL, RESET_CODE, RESET_NEW_PASSWORD = range(35, 38)

# ========== ЖАЛОБА НА ПОЛЬЗОВАТЕЛЯ/ЗАЯВКУ ==========
REPORT_CHOOSE_TYPE, REPORT_DESCRIPTION, REPORT_CONFIRM = range(38, 41)

# ========== СЛОВАРЬ ОПИСАНИЙ СОСТОЯНИЙ (для отладки) ==========
STATE_DESCRIPTIONS = {
    # Регистрация
    REGISTER_NAME: "Ввод ФИО при регистрации",
    REGISTER_PHONE: "Ввод телефона при регистрации",
    REGISTER_CONFIRM_PHONE: "Подтверждение телефона",
    REGISTER_VERIFY_PHONE_CODE: "Ввод SMS кода подтверждения",
    REGISTER_EMAIL: "Ввод email при регистрации",
    REGISTER_CONFIRM_EMAIL: "Подтверждение email",
    REGISTER_PASSWORD: "Ввод пароля при регистрации",
    
    # Вход
    LOGIN_EMAIL: "Ввод email при входе",
    LOGIN_PASSWORD: "Ввод пароля при входе",
    
    # Предложить помощь
    OFFER_CATEGORY: "Выбор категории при предложении помощи",
    OFFER_TITLE: "Ввод заголовка заявки",
    OFFER_DESCRIPTION: "Ввод описания заявки",
    OFFER_CONTACTS: "Выбор контактов для связи",
    
    # Попросить помощи
    REQUEST_CATEGORY: "Выбор категории при запросе помощи",
    REQUEST_DESCRIPTION: "Ввод описания запроса",
    REQUEST_BUDGET: "Ввод бюджета запроса",
    REQUEST_DEADLINE: "Ввод срока выполнения запроса",
    REQUEST_CONTACTS: "Выбор контактов для связи",
    
    # Редактирование профиля
    EDIT_NAME: "Редактирование ФИО",
    EDIT_AGE: "Редактирование возраста",
    EDIT_EMAIL: "Редактирование email",
    EDIT_PHONE: "Редактирование телефона",
    
    # Отклик на заявку
    RESPONSE_CHOOSE_REQUEST: "Выбор заявки для отклика",
    RESPONSE_WRITE_MESSAGE: "Написание сообщения для отклика",
    
    # Оценка и отзыв
    FEEDBACK_RATING: "Постановка оценки",
    FEEDBACK_COMMENT: "Написание комментария",
    
    # Поиск
    SEARCH_CATEGORY: "Выбор категории для поиска",
    SEARCH_LOCATION: "Ввод местоположения для поиска",
    SEARCH_RADIUS: "Выбор радиуса поиска",
    
    # Админка
    ADMIN_CHOOSE_ACTION: "Выбор действия админа",
    ADMIN_SEND_NOTIFICATION: "Отправка уведомления",
    ADMIN_MODERATE_REQUEST: "Модерация заявки",
    
    # Уведомления
    NOTIFICATION_TITLE: "Ввод заголовка уведомления",
    NOTIFICATION_TEXT: "Ввод текста уведомления",
    NOTIFICATION_CONFIRM: "Подтверждение отправки уведомления",
    
    # Восстановление пароля
    RESET_EMAIL: "Ввод email для восстановления",
    RESET_CODE: "Ввод кода подтверждения",
    RESET_NEW_PASSWORD: "Ввод нового пароля",
    
    # Жалобы
    REPORT_CHOOSE_TYPE: "Выбор типа жалобы",
    REPORT_DESCRIPTION: "Описание жалобы",
    REPORT_CONFIRM: "Подтверждение отправки жалобы",
}

# ========== УТИЛИТЫ ДЛЯ РАБОТЫ СО СОСТОЯНИЯМИ ==========

def get_state_description(state: int) -> str:
    """
    Получение описания состояния по его коду
    
    Args:
        state: Код состояния
    
    Returns:
        str: Описание состояния или "Неизвестное состояние"
    """
    return STATE_DESCRIPTIONS.get(state, "Неизвестное состояние")


def print_all_states():
    """
    Вывод всех состояний с описаниями (для отладки)
    """
    print("📋 Список всех состояний ConversationHandler:")
    print("-" * 50)
    
    # Сортируем состояния по значению
    sorted_states = sorted(STATE_DESCRIPTIONS.items(), key=lambda x: x[0])
    
    for state_code, description in sorted_states:
        print(f"{state_code:3} - {description}")
    
    print("-" * 50)
    print(f"Всего состояний: {len(STATE_DESCRIPTIONS)}")


# ========== ГРУППЫ СОСТОЯНИЙ (для удобства) ==========

# Все состояния регистрации
REGISTRATION_STATES = {
    REGISTER_NAME,
    REGISTER_PHONE,
    REGISTER_CONFIRM_PHONE,
    REGISTER_VERIFY_PHONE_CODE,
    REGISTER_EMAIL,
    REGISTER_CONFIRM_EMAIL,
    REGISTER_PASSWORD
}

# Все состояния создания заявок
REQUEST_CREATION_STATES = {
    OFFER_CATEGORY, OFFER_TITLE, OFFER_DESCRIPTION, OFFER_CONTACTS,
    REQUEST_CATEGORY, REQUEST_DESCRIPTION, REQUEST_BUDGET, REQUEST_DEADLINE, REQUEST_CONTACTS
}

# Все состояния редактирования профиля
PROFILE_EDIT_STATES = {
    EDIT_NAME, EDIT_PHONE, EDIT_EMAIL
}

# Все состояния связанные с заявками
REQUEST_RELATED_STATES = {
    RESPONSE_CHOOSE_REQUEST, RESPONSE_WRITE_MESSAGE,
    FEEDBACK_RATING, FEEDBACK_COMMENT,
    SEARCH_CATEGORY, SEARCH_LOCATION, SEARCH_RADIUS
}

# Все административные состояния
ADMIN_STATES = {
    ADMIN_CHOOSE_ACTION, ADMIN_SEND_NOTIFICATION, ADMIN_MODERATE_REQUEST,
    NOTIFICATION_TITLE, NOTIFICATION_TEXT, NOTIFICATION_CONFIRM
}

# Все состояния авторизации
AUTH_STATES = {
    REGISTER_NAME, REGISTER_PHONE, REGISTER_EMAIL, REGISTER_PASSWORD,
    LOGIN_EMAIL, LOGIN_PASSWORD,
    RESET_EMAIL, RESET_CODE, RESET_NEW_PASSWORD
}

# ========== ПРОВЕРКА СОСТОЯНИЙ ==========

def is_registration_state(state: int) -> bool:
    """Проверяет, является ли состояние частью регистрации"""
    return state in REGISTRATION_STATES


def is_auth_state(state: int) -> bool:
    """Проверяет, является ли состояние частью авторизации"""
    return state in AUTH_STATES


def is_request_state(state: int) -> bool:
    """Проверяет, связано ли состояние с заявками"""
    return state in REQUEST_CREATION_STATES or state in REQUEST_RELATED_STATES


def is_admin_state(state: int) -> bool:
    """Проверяет, является ли состояние административным"""
    return state in ADMIN_STATES


# ========== ТЕСТИРОВАНИЕ ==========

if __name__ == '__main__':
    print("🧪 Тестирование модуля состояний...")
    print_all_states()
    
    # Примеры использования
    print("\n📊 Примеры проверок состояний:")
    print(f"REGISTER_NAME ({REGISTER_NAME}) - это регистрация: {is_registration_state(REGISTER_NAME)}")
    print(f"LOGIN_EMAIL ({LOGIN_EMAIL}) - это авторизация: {is_auth_state(LOGIN_EMAIL)}")
    print(f"OFFER_CATEGORY ({OFFER_CATEGORY}) - это заявка: {is_request_state(OFFER_CATEGORY)}")
    
    print("\n✅ Модуль состояний готов к использованию!")