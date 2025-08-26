-- Включим читаемый вывод

.headers on
.mode column

-- 0) Посмотреть схему таблицы: какие поля реально есть
SELECT name AS column_name, type AS column_type
FROM pragma_table_info('session_days');

-- 1) Сколько всего занятий
SELECT COUNT(*) AS total_sessions
FROM session_days;

-- 2) Быстрый предпросмотр первых 5 строк (на случай, если названия столбцов отличаются)
-- (Если нужные поля есть — увидишь их в этом превью)
SELECT *
FROM session_days
ORDER BY 1
LIMIT 5;

-- 3) Список кодов тем (если столбец topic_code есть — покажет; если нет, просто пропусти эту секцию)
SELECT DISTINCT topic_code
FROM session_days
WHERE topic_code IS NOT NULL
ORDER BY topic_code;

-- 4) Статистика использования тем (эта часть у тебя уже работала)
SELECT t.code, t.title, COUNT(sd.id) AS used_in_sessions
FROM topics t
LEFT JOIN session_days sd ON sd.topic_code = t.code
GROUP BY t.code, t.title
ORDER BY used_in_sessions DESC
LIMIT 20;
