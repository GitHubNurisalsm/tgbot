# validators.py (упрощенная версия)
import re
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any, Union

class DataValidators:
    """Класс для валидации различных типов данных (без внешних зависимостей)"""
    
    @staticmethod
    def validate_name(name: str, min_length: int = 2, max_length: int = 50) -> Tuple[bool, str]:
        """Валидация имени пользователя"""
        if not name or not name.strip():
            return False, "Имя не может быть пустым"
        
        name = name.strip()
        
        if len(name) < min_length:
            return False, f"Имя должно содержать минимум {min_length} символа"
        
        if len(name) > max_length:
            return False, f"Имя не должно превышать {max_length} символов"
        
        # Проверка на допустимые символы
        if not re.match(r'^[a-zA-Zа-яА-ЯёЁ\- ]+$', name):
            return False, "Имя может содержать только буквы, дефисы и пробелы"
        
        if '  ' in name:
            return False, "Имя не должно содержать двойных пробелов"
        
        if name.startswith('-') or name.endswith('-'):
            return False, "Имя не должно начинаться или заканчиваться дефисом"
        
        return True, "Имя валидно"
    
    @staticmethod
    def validate_age(age_str: str, min_age: int = 14, max_age: int = 120) -> Tuple[bool, str, Optional[int]]:
        """Валидация возраста"""
        if not age_str:
            return False, "Возраст не может быть пустым", None
        
        try:
            age = int(age_str.strip())
        except ValueError:
            return False, "Возраст должен быть числом", None
        
        if age < min_age:
            return False, f"Минимальный возраст: {min_age} лет", None
        
        if age > max_age:
            return False, f"Максимальный возраст: {max_age} лет", None
        
        return True, "Возраст валиден", age
    
    @staticmethod
    def validate_email(email: str) -> Tuple[bool, str, Optional[str]]:
        """Валидация email адреса (упрощенная)"""
        if not email or not email.strip():
            return False, "Email не может быть пустым", None
        
        email = email.strip().lower()
        
        # Базовая проверка формата
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        
        if not re.match(email_pattern, email):
            return False, "Неверный формат email", None
        
        # Проверка длины
        if len(email) > 254:
            return False, "Email слишком длинный", None
        
        return True, "Email валиден", email
    
    @staticmethod
    def validate_phone(phone: str) -> Tuple[bool, str, Optional[str]]:
        """Валидация номера телефона (упрощенная для России)"""
        if not phone or not phone.strip():
            return False, "Номер телефона не может быть пустым", None
        
        phone = phone.strip()
        
        # Убираем все нецифровые символы, кроме плюса в начале
        if phone.startswith('+'):
            cleaned = '+' + re.sub(r'\D', '', phone[1:])
        else:
            cleaned = re.sub(r'\D', '', phone)
        
        # Для российских номеров
        if cleaned.startswith('+7'):
            number = cleaned[2:]  # Убираем +7
        elif cleaned.startswith('7'):
            number = cleaned[1:]  # Убираем 7
        elif cleaned.startswith('8'):
            number = cleaned[1:]  # Убираем 8
        else:
            number = cleaned
        
        # Проверка длины (10 цифр для России)
        if len(number) == 10 and number.startswith('9'):
            formatted = f"+7 ({number[:3]}) {number[3:6]}-{number[6:8]}-{number[8:]}"
            return True, "Номер телефона валиден", formatted
        
        # Общая проверка
        if len(cleaned) >= 8:
            return True, "Номер телефона валиден", cleaned
        
        return False, "Номер телефона слишком короткий", None
    
    @staticmethod
    def validate_password(password: str, min_length: int = 8, max_length: int = 64) -> Tuple[bool, str]:
        """Валидация пароля"""
        if not password:
            return False, "Пароль не может быть пустым"
        
        if len(password) < min_length:
            return False, f"Пароль должен содержать минимум {min_length} символов"
        
        if len(password) > max_length:
            return False, f"Пароль не должен превышать {max_length} символов"
        
        return True, "Пароль валиден"

class UserValidators:
    @staticmethod
    def validate_user_data(user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Комплексная валидация данных пользователя"""
        errors = []
        validated_data = {}
        
        if 'name' in user_data:
            is_valid, message = DataValidators.validate_name(user_data['name'])
            if is_valid:
                validated_data['name'] = user_data['name'].strip()
            else:
                errors.append(f"Имя: {message}")
        
        if 'age' in user_data:
            is_valid, message, age = DataValidators.validate_age(str(user_data['age']))
            if is_valid:
                validated_data['age'] = age
            else:
                errors.append(f"Возраст: {message}")
        
        if 'email' in user_data:
            is_valid, message, email = DataValidators.validate_email(user_data['email'])
            if is_valid:
                validated_data['email'] = email
            else:
                errors.append(f"Email: {message}")
        
        return {
            'is_valid': len(errors) == 0,
            'errors': errors,
            'validated_data': validated_data
        }

# Создаем экземпляры для импорта
validators = DataValidators()
user_validators = UserValidators()