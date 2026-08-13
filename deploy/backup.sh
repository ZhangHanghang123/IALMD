#!/bin/bash
# ============================================================
# IALMD 数据库定时备份脚本
# 保留策略: 每日7天 + 每周4周 + 每月3月
# ============================================================

BACKUP_DIR="/opt/ialmd/backup"
DB_NAME="IALMD"
DB_USER="ialmd_user"
# 从 .env 读取密码
DB_PASS=$(grep DATABASE_URL /opt/ialmd/backend/.env 2>/dev/null | sed 's/.*:\/\/[^:]*:\([^@]*\)@.*/\1/')

if [ -z "$DB_PASS" ]; then
    echo "[$(date)] ERROR: 无法读取数据库密码，请检查 .env"
    exit 1
fi

DATE=$(date +%Y%m%d_%H%M%S)
WEEKDAY=$(date +%u)
DAY=$(date +%d)

mkdir -p "$BACKUP_DIR/daily" "$BACKUP_DIR/weekly" "$BACKUP_DIR/monthly"

echo "[$(date)] Starting backup..."

mysqldump -u "$DB_USER" -p"$DB_PASS" \
    --single-transaction \
    --routines \
    --triggers \
    --quick \
    "$DB_NAME" > "$BACKUP_DIR/daily/IALMD_${DATE}.sql"

gzip "$BACKUP_DIR/daily/IALMD_${DATE}.sql"

if [ $? -eq 0 ]; then
    SIZE=$(du -sh "$BACKUP_DIR/daily/IALMD_${DATE}.sql.gz" | awk '{print $1}')
    echo "[$(date)] Backup OK: IALMD_${DATE}.sql.gz ($SIZE)"

    if [ "$WEEKDAY" == "7" ]; then
        cp "$BACKUP_DIR/daily/IALMD_${DATE}.sql.gz" "$BACKUP_DIR/weekly/"
    fi

    if [ "$DAY" == "01" ]; then
        cp "$BACKUP_DIR/daily/IALMD_${DATE}.sql.gz" "$BACKUP_DIR/monthly/"
    fi
else
    echo "[$(date)] Backup FAILED!"
    exit 1
fi

find "$BACKUP_DIR/daily" -name "*.sql.gz" -mtime +7 -delete
find "$BACKUP_DIR/weekly" -name "*.sql.gz" -mtime +28 -delete
find "$BACKUP_DIR/monthly" -name "*.sql.gz" -mtime +90 -delete

echo "[$(date)] Summary: Daily=$(ls -1 $BACKUP_DIR/daily/ | wc -l) Weekly=$(ls -1 $BACKUP_DIR/weekly/ | wc -l) Monthly=$(ls -1 $BACKUP_DIR/monthly/ | wc -l)"
