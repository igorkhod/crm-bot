#!/bin/bash
# Восстановление роли admin для указанного telegram_id

DB_PATH="/var/data/crm.db"
TG_ID=${1:-448124106}   # можно передать ID параметром, по умолчанию твой

sqlite3 "$DB_PATH" "UPDATE users SET role='admin' WHERE telegram_id=$TG_ID;"
echo "✅ Пользователь $TG_ID теперь admin"

##!/usr/bin/env bash
## admin.sh — вернуть роль admin указанному telegram_id
## Использование: ./admin.sh 123456789
#
#set -euo pipefail
#
#DB="/var/data/crm.db"
#TGID="448124106"
#
#if [ -z "$TGID" ]; then
#  echo "Usage: $0 <telegram_id>"
#  exit 1
#fi
#
#sqlite3 "$DB" <<SQL
#UPDATE users
#SET role='admin'
#WHERE telegram_id=$TGID;
#SQL
#
#echo "✅ Готово: пользователю telegram_id=$TGID назначена роль admin."
