-- Проверка количества всех занятий
SELECT COUNT(*) AS total_sessions FROM session_days;

-- Разбивка по потокам
SELECT cohort_id, COUNT(*) AS sessions
FROM session_days
GROUP BY cohort_id;

-- 5 ближайших занятий
SELECT start_date, end_date, topic_code, title
FROM session_days
ORDER BY start_date
LIMIT 5;

-- Список кодов тем (20 шт.)
SELECT DISTINCT topic_code
FROM session_days
WHERE topic_code IS NOT NULL
LIMIT 20;

-- Привязка тем к занятиям (10 самых используемых)
SELECT t.code, t.title, COUNT(sd.id) AS used_in_sessions
FROM topics t
LEFT JOIN session_days sd ON sd.topic_code = t.code
GROUP BY t.code, t.title
ORDER BY used_in_sessions DESC
LIMIT 10;

