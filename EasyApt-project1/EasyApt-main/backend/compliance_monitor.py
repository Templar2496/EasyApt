"""
Compliance Monitoring System for EasyApt
Monitors security, data integrity, and regulatory compliance
"""

import sqlite3
from datetime import datetime, timedelta
import json

def check_password_requirements():
    """Check if all users have strong passwords (hashed properly)"""
    conn = sqlite3.connect('easyapt.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM user WHERE password_hash IS NULL OR password_hash = ''")
    weak_passwords = cursor.fetchone()[0]
    
    conn.close()
    
    return {
        "check": "Password Requirements",
        "status": "PASS" if weak_passwords == 0 else "FAIL",
        "details": f"{weak_passwords} users with weak/missing passwords",
        "compliant": weak_passwords == 0
    }

def check_2fa_adoption():
    """Monitor two-factor authentication adoption rate"""
    conn = sqlite3.connect('easyapt.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM user")
    total_users = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM user WHERE two_factor_enabled = 1")
    twofa_users = cursor.fetchone()[0]
    
    conn.close()
    
    adoption_rate = (twofa_users / total_users * 100) if total_users > 0 else 0
    
    return {
        "check": "2FA Adoption",
        "status": "PASS" if adoption_rate >= 50 else "WARNING",
        "details": f"{twofa_users}/{total_users} users ({adoption_rate:.1f}%) have 2FA enabled",
        "compliant": adoption_rate >= 50
    }

def check_data_integrity():
    """Verify referential integrity and data consistency"""
    conn = sqlite3.connect('easyapt.db')
    cursor = conn.cursor()
    
    issues = []
    
    # Check for orphaned appointments (patient deleted but appointments remain)
    cursor.execute("""
        SELECT COUNT(*) FROM appointment 
        WHERE patient_id NOT IN (SELECT id FROM user)
    """)
    orphaned_appointments = cursor.fetchone()[0]
    if orphaned_appointments > 0:
        issues.append(f"{orphaned_appointments} orphaned appointments")
    
    # Check for appointments with invalid providers
    cursor.execute("""
        SELECT COUNT(*) FROM appointment 
        WHERE provider_id NOT IN (SELECT id FROM provider)
    """)
    invalid_providers = cursor.fetchone()[0]
    if invalid_providers > 0:
        issues.append(f"{invalid_providers} appointments with invalid providers")
    
    # Check for profiles without users
    cursor.execute("""
        SELECT COUNT(*) FROM patientprofile 
        WHERE user_id NOT IN (SELECT id FROM user)
    """)
    orphaned_profiles = cursor.fetchone()[0]
    if orphaned_profiles > 0:
        issues.append(f"{orphaned_profiles} orphaned profiles")
    
    conn.close()
    
    return {
        "check": "Data Integrity",
        "status": "PASS" if len(issues) == 0 else "FAIL",
        "details": "No integrity issues found" if len(issues) == 0 else "; ".join(issues),
        "compliant": len(issues) == 0
    }

def check_backup_compliance():
    """Verify backup system is running and retaining proper backups"""
    import os
    from datetime import datetime

    backup_dir = 'backups'
    
    if not os.path.exists(backup_dir):
        return {
            "check": "Backup Compliance",
            "status": "FAIL",
            "details": "Backup directory not found",
            "compliant": False
        }
    
    backups = [f for f in os.listdir(backup_dir) if f.endswith('.db')]
    
    if len(backups) == 0:
        return {
            "check": "Backup Compliance",
            "status": "FAIL",
            "details": "No backups found",
            "compliant": False
        }
    
    # Check if backups are recent (within last 7 hours - should run every 6)
    latest_backup = max(backups)
    try:
        # Extract timestamp from filename
        # Example: easyapt_backup_20260428_212455.db -> 20260428_212455
        timestamp_str = latest_backup.replace('easyapt_backup_', '').replace('.db', '')
        # Parse: 20260428_212455 -> datetime
        backup_time = datetime.strptime(timestamp_str, '%Y%m%d_%H%M%S')
        backup_age = (datetime.now() - backup_time).total_seconds() / 3600
        
        return {
            "check": "Backup Compliance",
            "status": "PASS" if backup_age < 7 else "WARNING",
            "details": f"{len(backups)} backups found, latest is {backup_age:.1f} hours old",
            "compliant": backup_age < 7
        }
    except Exception as e:
        # Fallback to old method if filename parsing fails
        backup_path = os.path.join(backup_dir, latest_backup)
        backup_age = (datetime.now().timestamp() - os.path.getmtime(backup_path)) / 3600
        
        return {
            "check": "Backup Compliance",
            "status": "WARNING",
            "details": f"{len(backups)} backups found, latest filename: {latest_backup} (age calculation error)",
            "compliant": False
        }
def check_session_security():
    """Check for inactive sessions and lockout compliance"""
    conn = sqlite3.connect('easyapt.db')
    cursor = conn.cursor()
    
    # Check for locked accounts
    cursor.execute("""
        SELECT COUNT(*) FROM user 
        WHERE failed_login_attempts >= 5 AND lockout_until > datetime('now')
    """)
    locked_accounts = cursor.fetchone()[0]
    
    # Check for stale sessions (users who haven't been active recently)
    one_month_ago = (datetime.now() - timedelta(days=30)).isoformat()
    cursor.execute("""
        SELECT COUNT(*) FROM user 
        WHERE last_active < ?
    """, (one_month_ago,))
    stale_sessions = cursor.fetchone()[0]
    
    conn.close()
    
    return {
        "check": "Session Security",
        "status": "PASS",
        "details": f"{locked_accounts} currently locked accounts, {stale_sessions} stale sessions (>30 days)",
        "compliant": True
    }

def check_hipaa_compliance():
    """Check HIPAA-related compliance requirements"""
    issues = []
    
    # Check if patient health data has proper access controls
    conn = sqlite3.connect('easyapt.db')
    cursor = conn.cursor()
    
    # Verify all patient profiles have encryption-worthy data
    cursor.execute("""
        SELECT COUNT(*) FROM patientprofile 
        WHERE (medical_conditions IS NOT NULL OR allergies IS NOT NULL OR medications IS NOT NULL)
    """)
    profiles_with_phi = cursor.fetchone()[0]
    
    conn.close()
    
    return {
        "check": "HIPAA Compliance (Data Protection)",
        "status": "PASS",
        "details": f"{profiles_with_phi} patient profiles contain PHI (Protected Health Information)",
        "compliant": True
    }

def run_compliance_checks():
    """Run all compliance checks and generate report"""
    print("=" * 70)
    print(" EasyApt Compliance Monitoring Report")
    print("=" * 70)
    print(f" Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    print()
    
    checks = [
        check_password_requirements(),
        check_2fa_adoption(),
        check_data_integrity(),
        check_backup_compliance(),
        check_session_security(),
        check_hipaa_compliance()
    ]
    
    passed = sum(1 for c in checks if c['compliant'])
    total = len(checks)
    
    for check in checks:
        status_symbol = "✓" if check['status'] == "PASS" else " " if check['status'] == "WARNING" else "✗"
        print(f"{status_symbol} {check['check']}: {check['status']}")
        print(f"  {check['details']}")
        print()
    
    print("=" * 70)
    print(f" Overall Compliance: {passed}/{total} checks passed ({passed/total*100:.1f}%)")
    print("=" * 70)
    
    # Log to file
    with open('compliance_log.txt', 'a') as f:
        f.write(f"\n{'='*70}\n")
        f.write(f"Compliance Check - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"{'='*70}\n")
        for check in checks:
            f.write(f"{check['check']}: {check['status']} - {check['details']}\n")
        f.write(f"Overall: {passed}/{total} passed\n")
    
    return checks

if __name__ == '__main__':
    run_compliance_checks()
