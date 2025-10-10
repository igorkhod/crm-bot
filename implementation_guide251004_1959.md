# 📋 Инструкция по внедрению исправлений

## ✅ Что было исправлено

### 1. **Подключение модуля домашних заданий**
- В `panel.py` кнопка "📚 Домашние задания" теперь вызывает FSM-обработчик вместо заглушки

### 2. **Исправлен цикл статусов посещаемости**
- Убран несуществующий статус `expelled` (не соответствовал CHECK constraint БД)
- Цикл теперь: `пусто → present → absent → late → пусто`
- Обновлены иконки: ✅ (present) → ❌ (absent) → ⏰ (late) → ⬜️ (пусто)

### 3. **Создан сервисный слой для attendance**
- Новый файл `services/attendance.py` с функциями:
  - `get_sessions_near()` - занятия за последние N дней
  - `get_present_users()` - кто отмечен "присутствовал"
  - `get_not_yet_delivered()` - кто ещё не получил ДЗ
  - `mark_homework_delivered()` - отметка доставки

### 4. **Улучшена логика рассылки ДЗ**
- Проверка наличия получателей перед запросом ссылки
- Отображение количества получателей
- Предотвращение повторной отправки одним и тем же пользователям

---

## 📂 Файлы для замены/создания

### 1. **Заменить** `crm2/handlers/admin/panel.py`
```python
# ПАТЧ 1 (строки 47-52):
# Было:
#     await cq.message.answer("Раздел «Домашние задания» в разработке.")
# 
# Стало:
    from crm2.handlers.admin_homework import admin_homework_entry
    await admin_homework_entry(cq.message)
```

### 2. **Заменить** `crm2/handlers/admin_attendance.py`
```python
# ПАТЧ 2 (строки 167-186):
# Было:
#     curr = marks.get(user_id)  # None|'present'|'absent'|'expelled'
#     nxt = (
#         "present" if curr is None else
#         "absent" if curr == "present" else
#         "expelled" if curr == "absent" else  # ⚠️ ОШИБКА
#         None
#     )
# 
# Стало:
    curr = marks.get(user_id)  # None|'present'|'absent'|'late'
    nxt = (
        "present" if curr is None else
        "absent" if curr == "present" else
        "late" if curr == "absent" else  # ✅ ИСПРАВЛЕНО
        None
    )
    
    # И в msg:
    msg = {
        "present": "✅ присутствовал",
        "absent": "❌ отсутствовал",
        "late": "⏰ опоздал"  # ✅ ИСПРАВЛЕНО
    }[nxt]
```

### 3. **Создать** `crm2/services/attendance.py`
- Полный код в артефакте "services/attendance.py (новый файл)"

### 4. **Заменить** `crm2/handlers/admin_homework.py`
- Использовать FSM-версию с ПАТЧЕМ 3 из артефакта

### 5. **Заменить** `crm2/keyboards/admin_attendance.py`
```python
# ПАТЧ 4 (функция icon):
# Было:
#     return "✅" if st == "present" else "❌" if st == "absent" else "⛔️" if st == "expelled" else "⬜️"
#
# Стало:
    return (
        "✅" if st == "present" else
        "❌" if st == "absent" else
        "⏰" if st == "late" else
        "⬜️"
    )
```

---

## 🚀 Порядок внедрения

### Шаг 1: Создать новую папку (если нет)
```bash
mkdir -p crm2/services
touch crm2/services/__init__.py
```

### Шаг 2: Применить изменения
1. Скопировать `services/attendance.py` из артефакта
2. Применить ПАТЧ 1 в `panel.py`
3. Применить ПАТЧ 2 в `admin_attendance.py`
4. Заменить `admin_homework.py` на FSM-версию (с ПАТЧЕМ 3)
5. Применить ПАТЧ 4 в `keyboards/admin_attendance.py`

### Шаг 3: Проверить импорты в app.py
Убедитесь, что подключен роутер из FSM-версии:
```python
from crm2.handlers import admin_homework
dp.include_router(admin_homework.router)
```

### Шаг 4: Тестирование
1. Запустить локально: `python app.py`
2. Открыть админ-панель: `/admin`
3. Протестировать цепочку:
   - ✅ Посещаемость → отметить присутствующих
   - 📚 Домашние задания → выбрать занятие → отправить ДЗ
   - Проверить, что ДЗ приходит только присутствовавшим
   - Проверить, что повторная отправка не дублирует

---

## 🔍 Как проверить работу

### Тест 1: Посещаемость
```
1. /admin → ✅ Посещаемость
2. Выбрать занятие
3. Кликать на имена:
   ⬜️ → ✅ → ❌ → ⏰ → ⬜️
4. Убедиться, что нет ошибок БД
```

### Тест 2: Рассылка ДЗ
```
1. Отметить 2-3 человека как "✅ присутствовал"
2. /admin → 📚 Домашние задания
3. Выбрать то же занятие
4. "🚀 Отправить ДЗ"
5. Должно показать: "Готово к отправке: 2 получателей"
6. Вставить ссылку, отправить
7. Проверить в таблице homework_delivery
```

### SQL для проверки
```sql
-- Посмотреть присутствовавших
SELECT u.full_name, a.status 
FROM attendance a
JOIN users u ON u.id = a.user_id
WHERE a.session_id = 1;

-- Посмотреть доставки ДЗ
SELECT u.full_name, hd.link, hd.sent_at
FROM homework_delivery hd
JOIN users u ON u.id = hd.user_id
WHERE hd.session_id = 1;
```

---

## ⚠️ Важные моменты

1. **База данных не требует изменений** - структура остаётся прежней
2. **Удалить старую Command-версию** `admin_homework.py` если она есть отдельно
3. **Статусы в БД**: `present`, `absent`, `late` (НЕ `expelled`)
4. **FSM-версия** использует состояния для ввода ссылок (более user-friendly)

---

## 📊 Архитектура решения

```
[Админ нажимает "✅ Посещаемость"]
         ↓
[Отмечает: user1=present, user2=present, user3=absent]
         ↓
[Сохраняется в attendance с session_id]
         ↓
[Админ → "📚 Домашние задания" → Выбирает занятие]
         ↓
[get_not_yet_delivered(session_id)]
  → Запрос: кто present И ещё нет в homework_delivery
         ↓
[Показывает: "Готово к отправке: 2 получателей"]
         ↓
[Админ вводит ссылку]
         ↓
[Рассылка только user1 и user2]
         ↓
[mark_homework_delivered() → запись в homework_delivery]
         ↓
[Повторная отправка → "Всем уже отправлено"]
```

---

## 🎯 Результат

✅ ДЗ отправляется **только присутствовавшим**  
✅ Нет повторных отправок  
✅ Удобный интерфейс через FSM  
✅ Статистика доставок  
✅ Корректные статусы посещаемости  

Готово к деплою! 🚀