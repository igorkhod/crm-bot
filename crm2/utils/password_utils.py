# crm2/utils/password_utils.py
# crm2/utils/password_utils.py
# Назначение: Утилиты для безопасной работы с паролями - хеширование, проверка и нормализация
# Функции:
# - normalize_string - Нормализация строк (удаление невидимых символов, пробелов)
# - is_bcrypt_hash - Проверка является ли строка bcrypt-хешем
# - hash_password - Хеширование пароля с использованием bcrypt
# - verify_password - Проверка пароля с поддержкой bcrypt и plain text (для миграции)
# - needs_rehash - Проверка необходимости перехеширования пароля
# - verify_and_upgrade_password - Комплексная проверка и автоматическое обновление хеша
from __future__ import annotations

import hmac
import re

import bcrypt

# Bcrypt хеш всегда имеет длину 60 символов
BCRYPT_HASH_LENGTH = 60

def normalize_string(s: str) -> str:
    """Убираем неразрывные/невидимые пробелы и обрезаем края."""
    if s is None:
        return ""
    s = (s.replace("\u00A0", " ")  # NBSP
         .replace("\uFEFF", "")  # BOM
         .replace("\u200B", "")
         .replace("\u200C", "")
         .replace("\u200D", ""))
    s = re.sub(r"\s+", " ", s)
    return s.strip()

_BCRYPT_RE = re.compile(r"^\$2[aby]?\$\d{2}\$[./A-Za-z0-9]{53}$")

def is_bcrypt_hash(s: str) -> bool:
    return bool(s) and bool(_BCRYPT_RE.match(s))

def hash_password(password: str) -> str:
    password = normalize_string(password)
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    plain_password = normalize_string(plain_password)
    hashed_password = str(hashed_password or "")

    if is_bcrypt_hash(hashed_password):
        try:
            return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
        except Exception:
            return False

    # Для обратной совместимости с plain text паролями
    normalized_hashed = normalize_string(hashed_password)
    normalized_plain = normalize_string(plain_password)

    try:
        return hmac.compare_digest(normalized_hashed, normalized_plain)
    except Exception:
        return normalized_hashed == normalized_plain

def needs_rehash(hashed_password: str) -> bool:
    """Проверяет, нужно ли перехешировать пароль (если он в plain text)."""
    return not is_bcrypt_hash(hashed_password)

def verify_and_upgrade_password(plain_password: str, stored_password: str, user_id: int = None) -> tuple[bool, str]:
    """
    Проверяет пароль и возвращает (успех, новый_хеш_если_нужно).
    """
    plain_password = normalize_string(plain_password)
    stored_password = str(stored_password or "")

    # Если пароль уже хеширован - проверяем через bcrypt
    if is_bcrypt_hash(stored_password):
        try:
            success = bcrypt.checkpw(plain_password.encode('utf-8'), stored_password.encode('utf-8'))
            return success, stored_password
        except Exception:
            return False, stored_password

    # Если пароль в plain text - проверяем простое сравнение
    normalized_stored = normalize_string(stored_password)
    normalized_plain = normalize_string(plain_password)

    try:
        success = hmac.compare_digest(normalized_stored, normalized_plain)
    except Exception:
        success = normalized_stored == normalized_plain

    # Если пароль верный и он в plain text - создаем новый хеш
    if success and len(stored_password) < BCRYPT_HASH_LENGTH:
        new_hash = hash_password(plain_password)
        return True, new_hash

    return success, stored_password