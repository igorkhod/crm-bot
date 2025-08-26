#!/bin/bash
# Краткая аннотация: запускает SQL-проверку расписания CRM-базы
# Использует check_schedule.sql и базу /var/data/crm.db

sqlite3 /var/data/crm.db < check_schedule.sql
