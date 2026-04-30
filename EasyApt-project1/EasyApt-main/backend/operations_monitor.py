"""
Operations & Performance Monitoring System for EasyApt
Monitors system health, performance metrics, and resource usage
"""

import sqlite3
import os
import psutil
from datetime import datetime, timedelta

def check_database_size():
    """Monitor database size and growth"""
    db_file = 'easyapt.db'
    
    if not os.path.exists(db_file):
        return {
            "metric": "Database Size",
            "status": "ERROR",
            "value": "Database not found",
            "healthy": False
        }
    
    size_bytes = os.path.getsize(db_file)
    size_kb = size_bytes / 1024
    
    return {
        "metric": "Database Size",
        "status": "HEALTHY" if size_kb < 10000 else "WARNING",
        "value": f"{size_kb:.2f} KB",
        "healthy": size_kb < 10000
    }

def check_database_performance():
    """Check database query performance and table counts"""
    conn = sqlite3.connect('easyapt.db')
    cursor = conn.cursor()
    
    # Get table counts
    cursor.execute("SELECT COUNT(*) FROM user")
    user_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM appointment")
    appointment_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM provider")
    provider_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM app_transaction")
    transaction_count = cursor.fetchone()[0]
    
    conn.close()
    
    return {
        "metric": "Database Records",
        "status": "HEALTHY",
        "value": f"Users: {user_count}, Appointments: {appointment_count}, Providers: {provider_count}, Transactions: {transaction_count}",
        "healthy": True
    }

def check_system_resources():
    """Monitor CPU and memory usage"""
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    memory_percent = memory.percent
    
    status = "HEALTHY"
    if cpu_percent > 80 or memory_percent > 80:
        status = "WARNING"
    if cpu_percent > 95 or memory_percent > 95:
        status = "CRITICAL"
    
    return {
        "metric": "System Resources",
        "status": status,
        "value": f"CPU: {cpu_percent}%, Memory: {memory_percent}%",
        "healthy": status == "HEALTHY"
    }

def check_disk_space():
    """Monitor available disk space"""
    disk = psutil.disk_usage('/')
    disk_percent = disk.percent
    disk_free_gb = disk.free / (1024**3)
    
    status = "HEALTHY"
    if disk_percent > 80:
        status = "WARNING"
    if disk_percent > 90:
        status = "CRITICAL"
    
    return {
        "metric": "Disk Space",
        "status": status,
        "value": f"{disk_percent}% used, {disk_free_gb:.2f} GB free",
        "healthy": status == "HEALTHY"
    }

def check_backup_system():
    """Monitor backup system health"""
    backup_dir = 'backups'
    
    if not os.path.exists(backup_dir):
        return {
            "metric": "Backup System",
            "status": "ERROR",
            "value": "Backup directory not found",
            "healthy": False
        }
    
    backups = [f for f in os.listdir(backup_dir) if f.endswith('.db')]
    
    if len(backups) == 0:
        return {
            "metric": "Backup System",
            "status": "ERROR",
            "value": "No backups found",
            "healthy": False
        }
    
    # Calculate total backup size
    total_size = sum(os.path.getsize(os.path.join(backup_dir, f)) for f in backups)
    total_size_mb = total_size / (1024 * 1024)
    
    return {
        "metric": "Backup System",
        "status": "HEALTHY",
        "value": f"{len(backups)} backups, {total_size_mb:.2f} MB total",
        "healthy": True
    }

def check_appointment_metrics():
    """Monitor appointment statistics and booking patterns"""
    conn = sqlite3.connect('easyapt.db')
    cursor = conn.cursor()
    
    # Total appointments
    cursor.execute("SELECT COUNT(*) FROM appointment")
    total = cursor.fetchone()[0]
    
    # Booked appointments
    cursor.execute("SELECT COUNT(*) FROM appointment WHERE status = 'booked'")
    booked = cursor.fetchone()[0]
    
    # Cancelled appointments
    cursor.execute("SELECT COUNT(*) FROM appointment WHERE status = 'cancelled'")
    cancelled = cursor.fetchone()[0]
    
    # Today's appointments
    today = datetime.now().date().isoformat()
    cursor.execute("SELECT COUNT(*) FROM appointment WHERE DATE(start_time) = ?", (today,))
    today_count = cursor.fetchone()[0]
    
    conn.close()
    
    cancellation_rate = (cancelled / total * 100) if total > 0 else 0
    
    return {
        "metric": "Appointment Metrics",
        "status": "HEALTHY" if cancellation_rate < 20 else "WARNING",
        "value": f"Total: {total}, Booked: {booked}, Cancelled: {cancelled} ({cancellation_rate:.1f}%), Today: {today_count}",
        "healthy": cancellation_rate < 20
    }

def check_transaction_health():
    """Monitor transaction system health"""
    conn = sqlite3.connect('easyapt.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*), SUM(amount) FROM app_transaction")
    result = cursor.fetchone()
    transaction_count = result[0]
    total_amount = result[1] if result[1] else 0
    
    cursor.execute("SELECT COUNT(*) FROM app_transaction WHERE status = 'completed'")
    completed = cursor.fetchone()[0]
    
    conn.close()
    
    success_rate = (completed / transaction_count * 100) if transaction_count > 0 else 0
    
    return {
        "metric": "Transaction Health",
        "status": "HEALTHY" if success_rate > 95 else "WARNING",
        "value": f"{transaction_count} transactions, ${total_amount:.2f} total, {success_rate:.1f}% success rate",
        "healthy": success_rate > 95
    }

def run_operations_monitoring():
    """Run all operations checks and generate report"""
    print("=" * 70)
    print(" EasyApt Operations & Performance Monitoring Report")
    print("=" * 70)
    print(f" Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    print()
    
    checks = [
        check_database_size(),
        check_database_performance(),
        check_system_resources(),
        check_disk_space(),
        check_backup_system(),
        check_appointment_metrics(),
        check_transaction_health()
    ]
    
    healthy = sum(1 for c in checks if c['healthy'])
    total = len(checks)
    
    for check in checks:
        status_symbol = "✓" if check['status'] == "HEALTHY" else " " if check['status'] == "WARNING" else "✗"
        print(f"{status_symbol} {check['metric']}: {check['status']}")
        print(f"  {check['value']}")
        print()
    
    print("=" * 70)
    print(f" System Health: {healthy}/{total} metrics healthy ({healthy/total*100:.1f}%)")
    print("=" * 70)
    
    # Log to file
    with open('operations_log.txt', 'a') as f:
        f.write(f"\n{'='*70}\n")
        f.write(f"Operations Check - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"{'='*70}\n")
        for check in checks:
            f.write(f"{check['metric']}: {check['status']} - {check['value']}\n")
        f.write(f"Overall: {healthy}/{total} healthy\n")
    
    return checks

if __name__ == '__main__':
    run_operations_monitoring()
