cat > sql_db.sh <<'SH'
#!/bin/bash
# Краткая аннотация: запускает SQL-проверку расписания CRM-базы (Render/Linux)
# Использует schedule.sql и базу /var/data/crm.db
sqlite3 /var/data/crm.db < schedule.sql
SH

chmod +x sql_db.sh
