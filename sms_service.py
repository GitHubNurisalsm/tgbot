"""
Сервис для отправки SMS с кодами подтверждения
Поддерживает smsc.ru API
"""
import os
import random
import logging
import httpx
import hashlib
from typing import Optional, Tuple

logger = logging.getLogger(__name__)


class SMSService:
    """Сервис для отправки SMS через smsc.ru"""
    
    def __init__(self):
        self.login = os.getenv('SMSC_LOGIN', '')
        self.password = os.getenv('SMSC_PASSWORD', '')
        self.use_md5 = os.getenv('SMSC_USE_MD5', 'false').lower() == 'true'
        self.api_url = 'https://smsc.ru/sys/send.php'
        self.enabled = bool(self.login and self.password)
        
        if not self.enabled:
            logger.warning("⚠️ SMS сервис не настроен (SMSC_LOGIN/SMSC_PASSWORD не установлены). SMS не будут отправляться.")
            logger.warning("⚠️ В режиме разработки код будет показан пользователю в сообщении.")
        else:
            logger.info(f"✅ SMS сервис настроен (логин: {self.login[:3]}***)")
    
    def generate_code(self, length: int = 6) -> str:
        """Генерирует случайный код подтверждения"""
        return ''.join([str(random.randint(0, 9)) for _ in range(length)])
    
    def send_verification_code(self, phone: str, code: str) -> Tuple[bool, str]:
        """
        Отправляет код подтверждения на телефон
        
        Args:
            phone: Номер телефона (формат: +7XXXXXXXXXX или 7XXXXXXXXXX)
            code: Код подтверждения для отправки
        
        Returns:
            Tuple[bool, str]: (успех, сообщение об ошибке или успехе)
        """
        # Нормализация номера телефона
        original_phone = phone
        phone = phone.replace('+', '').replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
        if phone.startswith('8'):
            phone = '7' + phone[1:]
        if not phone.startswith('7'):
            phone = '7' + phone
        
        logger.info(f"📱 Попытка отправить SMS код {code} на номер {phone} (исходный: {original_phone})")
        
        if not self.enabled:
            # В режиме разработки просто логируем код
            logger.warning(f"🔐 [DEV MODE] SMS сервис не настроен. Код подтверждения для {phone}: {code}")
            logger.warning(f"🔐 [DEV MODE] Для настройки SMS добавьте в .env: SMSC_LOGIN=... и SMSC_PASSWORD=...")
            return True, f"Код отправлен (режим разработки). Ваш код: {code}"
        
        try:
            # Подготовка пароля (MD5 хеш, если требуется)
            password_param = self.password
            if self.use_md5:
                password_param = hashlib.md5(self.password.encode('utf-8')).hexdigest()
            
            # Параметры для smsc.ru API
            params = {
                'login': self.login,
                'psw': password_param,
                'phones': phone,
                'mes': f'Ваш код подтверждения: {code}',
                'charset': 'utf-8',
                'fmt': 3  # JSON формат ответа
            }
            
            logger.debug(f"Отправка SMS запроса: URL={self.api_url}, phone={phone}, login={self.login[:3]}***")
            
            # Отправка запроса
            with httpx.Client(timeout=10.0) as client:
                response = client.get(self.api_url, params=params)
                logger.debug(f"Ответ от SMS API: status={response.status_code}, body={response.text[:200]}")
                response.raise_for_status()
                
                try:
                    result = response.json()
                except Exception as json_err:
                    logger.error(f"Ошибка парсинга JSON ответа: {json_err}, ответ: {response.text}")
                    return False, f"Ошибка обработки ответа от SMS сервиса"
                
                logger.debug(f"Результат SMS API: {result}")
                
                # Проверка результата smsc.ru API
                # smsc.ru при fmt=3 возвращает:
                # - При успехе: массив [{"id": "...", "cnt": 1}]
                # - При ошибке: {"error": "текст ошибки", "error_code": "код"}
                # - Или просто строку с ошибкой в некоторых случаях
                
                if isinstance(result, list) and len(result) > 0:
                    # Если массив, проверяем первый элемент
                    first_result = result[0]
                    if isinstance(first_result, dict):
                        if 'error' in first_result:
                            error_msg = first_result.get('error', 'Неизвестная ошибка')
                            error_code = first_result.get('error_code', '')
                            logger.error(f"Ошибка отправки SMS на {phone}: {error_msg} (код: {error_code})")
                            return False, f"Ошибка отправки SMS: {error_msg}"
                        elif 'id' in first_result or 'cnt' in first_result:
                            # Успешная отправка (есть id или cnt)
                            logger.info(f"✅ SMS код отправлен на {phone} (ID: {first_result.get('id', 'N/A')})")
                            return True, "Код подтверждения отправлен"
                        else:
                            # Неизвестная структура, но без ошибки
                            logger.info(f"✅ SMS код отправлен на {phone}")
                            return True, "Код подтверждения отправлен"
                    else:
                        # Массив, но первый элемент не словарь
                        logger.info(f"✅ SMS код отправлен на {phone}")
                        return True, "Код подтверждения отправлен"
                elif isinstance(result, dict):
                    # Если словарь, проверяем наличие ошибки
                    if 'error' in result:
                        error_msg = result.get('error', 'Неизвестная ошибка')
                        error_code = result.get('error_code', '')
                        logger.error(f"Ошибка отправки SMS на {phone}: {error_msg} (код: {error_code})")
                        return False, f"Ошибка отправки SMS: {error_msg}"
                    elif 'id' in result or 'cnt' in result:
                        # Успешная отправка
                        logger.info(f"✅ SMS код отправлен на {phone} (ID: {result.get('id', 'N/A')})")
                        return True, "Код подтверждения отправлен"
                    else:
                        # Словарь без известных полей
                        logger.warning(f"Неожиданная структура ответа: {result}")
                        logger.info(f"✅ SMS код отправлен на {phone} (неопределённый формат)")
                        return True, "Код подтверждения отправлен"
                elif isinstance(result, str):
                    # Строка - может быть ошибкой
                    if 'error' in result.lower() or 'ошибка' in result.lower():
                        logger.error(f"Ошибка отправки SMS на {phone}: {result}")
                        return False, f"Ошибка отправки SMS: {result}"
                    else:
                        logger.info(f"✅ SMS код отправлен на {phone}")
                        return True, "Код подтверждения отправлен"
                else:
                    logger.warning(f"Неожиданный формат ответа от SMS API: {type(result)}, значение: {result}")
                    # Если статус 200, считаем успешным
                    logger.info(f"✅ SMS код отправлен на {phone} (неопределённый формат ответа)")
                    return True, "Код подтверждения отправлен"
                
        except httpx.RequestError as e:
            logger.error(f"Ошибка сети при отправке SMS: {e}", exc_info=True)
            return False, f"Ошибка сети: {str(e)}"
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP ошибка при отправке SMS: {e.response.status_code} - {e.response.text}")
            return False, f"Ошибка HTTP {e.response.status_code}"
        except Exception as e:
            logger.error(f"Неожиданная ошибка при отправке SMS: {e}", exc_info=True)
            return False, f"Ошибка: {str(e)}"


# Глобальный экземпляр сервиса
sms_service = SMSService()


def generate_and_send_code(phone: str) -> Tuple[Optional[str], bool, str]:
    """
    Генерирует код и отправляет его на телефон
    
    Returns:
        Tuple[Optional[str], bool, str]: (код, успех отправки, сообщение)
    """
    code = sms_service.generate_code()
    success, message = sms_service.send_verification_code(phone, code)
    
    if success:
        return code, True, message
    else:
        return None, False, message

