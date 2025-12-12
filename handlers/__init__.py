"""Пакет обработчиков"""

from .start import start_command, help_command, menu_command, cancel_command
from .registration import start_registration, register_name, register_phone, register_email, register_password, cancel_registration
from .login import start_login, process_login_input, process_password_input, cancel_login
from .about import about_command, contact_support_command, show_faq_command

__all__ = [
    'start_command', 'help_command', 'menu_command', 'cancel_command',
    'start_registration', 'register_name', 'register_phone', 'register_email', 
    'register_password', 'cancel_registration',
    'start_login', 'process_login_input', 'process_password_input', 'cancel_login',
    'about_command', 'contact_support_command', 'show_faq_command'
]
