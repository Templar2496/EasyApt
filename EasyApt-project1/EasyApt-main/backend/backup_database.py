#!/usr/bin/env python3
"""
Database Backup Script for EasyApt
Performs automated backups with timestamp and verification
Author: Mason Rasberry
"""

import shutil
import os
from datetime import datetime
import sqlite3

def backup_database():
    """
    Create a timestamped backup of the database
    Returns the backup file path or None if failed
    """
    # Source database
    source_db = "easyapt.db"
    
    # Create backups directory if it doesn't exist
    backup_dir = "backups"
    os.makedirs(backup_dir, exist_ok=True)
    
    # Generate timestamped backup filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = f"{backup_dir}/easyapt_backup_{timestamp}.db"
    
    try:
        # Check if source database exists
        if not os.path.exists(source_db):
            print(f" Source database not found: {source_db}")
            return None
        
        # Copy database file
        shutil.copy2(source_db, backup_file)
        
        # Get file sizes
        source_size = os.path.getsize(source_db)
        backup_size = os.path.getsize(backup_file)
        
        print("=" * 60)
        print(" DATABASE BACKUP SUCCESSFUL")
        print("=" * 60)
        print(f" Source: {source_db}")
        print(f" Backup: {backup_file}")
        print(f" Source size: {source_size / 1024:.2f} KB")
        print(f" Backup size: {backup_size / 1024:.2f} KB")
        print(f" Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        # Verify backup integrity
        verify_backup(backup_file)
        
        return backup_file
        
    except FileNotFoundError:
        print(" Database file not found!")
        return None
    except PermissionError:
        print(" Permission denied! Cannot create backup.")
        return None
    except Exception as e:
        print(f" Backup failed: {e}")
        return None

def verify_backup(backup_file):
    """
    Verify the integrity of a backup file
    """
    print("\n Verifying backup integrity...")
    
    try:
        # Try to connect to the backup
        conn = sqlite3.connect(backup_file)
        cursor = conn.cursor()
        
        # Check tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        if not tables:
            print("⚠️ Warning: Backup appears to be empty!")
            conn.close()
            return False
        
        print(f" Backup verified successfully!")
        print(f" Tables found: {len(tables)}")
        
        # Count records in each table
        for table in tables:
            table_name = table[0]
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"   - {table_name}: {count} records")
        
        conn.close()
        return True
        
    except sqlite3.Error as e:
        print(f" Backup verification failed: {e}")
        return False

def list_backups():
    """
    List all available backups
    """
    backup_dir = "backups"
    
    if not os.path.exists(backup_dir):
        print(" No backups directory found.")
        return []
    
    import glob
    backups = glob.glob(f"{backup_dir}/easyapt_backup_*.db")
    backups.sort(reverse=True)  # Most recent first
    
    if not backups:
        print(" No backups found.")
        return []
    
# List all available backups
    print("\n" + "=" * 60)
    print(" AVAILABLE BACKUPS")
    print("=" * 60)
    
    backup_files = sorted(
        [f for f in os.listdir(backup_dir) if f.endswith('.db')],
        reverse=True
    )
    
    for i, backup_file in enumerate(backup_files, 1):
        backup_path = os.path.join(backup_dir, backup_file)
        size = os.path.getsize(backup_path) / 1024
        
        # Parse timestamp from filename instead of using file ctime
        try:
            # Extract timestamp from filename
            # Example: easyapt_backup_20260428_212455.db -> 20260428_212455
            timestamp_str = backup_file.replace('easyapt_backup_', '').replace('.db', '')
            # Parse: 20260428_212455 -> datetime
            backup_time = datetime.strptime(timestamp_str, '%Y%m%d_%H%M%S')
            created_str = backup_time.strftime('%Y-%m-%d %H:%M:%S')
        except:
            # Fallback to file modification time if parsing fails
            created_str = datetime.fromtimestamp(os.path.getmtime(backup_path)).strftime('%Y-%m-%d %H:%M:%S')
        
        print(f"{i}. {backup_file}")
        print(f"   Size: {size:.2f} KB | Created: {created_str}")

def cleanup_old_backups(keep_count=7):
    """
    Keep only the most recent N backups, delete older ones
    """
    backup_dir = "backups"
    
    if not os.path.exists(backup_dir):
        return
    
    import glob
    backups = glob.glob(f"{backup_dir}/easyapt_backup_*.db")
    backups.sort(reverse=True)  # Most recent first
    
    if len(backups) <= keep_count:
        print(f" No cleanup needed. Current backups: {len(backups)}")
        return
    
    # Delete old backups
    old_backups = backups[keep_count:]
    print(f"\n Cleaning up {len(old_backups)} old backup(s)...")
    
    for backup in old_backups:
        try:
            os.remove(backup)
            print(f"   Deleted: {os.path.basename(backup)}")
        except Exception as e:
            print(f"   ⚠️ Could not delete {backup}: {e}")
    
    print(f" Cleanup complete. Kept {keep_count} most recent backups.")

if __name__ == "__main__":
    print("\n EasyApt Database Backup System")
    print("=" * 60)
    
    # Perform backup
    backup_file = backup_database()
    
    if backup_file:
        # List all backups
        list_backups()
        
        # Clean up old backups (keep last 7)
        cleanup_old_backups(keep_count=7)
        
        print("\n Backup operation completed successfully!")
    else:
        print("\n Backup operation failed!")
