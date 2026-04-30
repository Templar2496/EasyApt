#!/bin/bash
# Automated Database Backup Script for EasyApt
# Logs backups with timestamps

# Set paths
BACKEND_DIR="/home/mjr0315/EasyApt/EasyApt-main/backend"
LOG_FILE="$BACKEND_DIR/backup_log.txt"

# Change to backend directory
cd $BACKEND_DIR

# Activate virtual environment
source venv/bin/activate

# Run backup
echo "========================================" >> $LOG_FILE
echo "Backup started at $(date)" >> $LOG_FILE
python backup_database.py >> $LOG_FILE 2>&1
echo "Backup completed at $(date)" >> $LOG_FILE
echo "========================================" >> $LOG_FILE

# Deactivate virtual environment
deactivate
