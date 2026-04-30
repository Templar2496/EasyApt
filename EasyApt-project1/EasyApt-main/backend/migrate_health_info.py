"""
Migration script to add health information fields to patient profile
"""

import sqlite3

def migrate_database():
    conn = sqlite3.connect('easyapt.db')
    cursor = conn.cursor()
    
    # Add new columns
    new_columns = [
        ('insurance_policy_number', 'TEXT'),
        ('blood_type', 'TEXT'),
        ('allergies', 'TEXT'),
        ('medications', 'TEXT'),
        ('medical_conditions', 'TEXT'),
        ('emergency_contact_name', 'TEXT'),
        ('emergency_contact_phone', 'TEXT'),
    ]
    
    for column_name, column_type in new_columns:
        try:
            cursor.execute(f'ALTER TABLE patientprofile ADD COLUMN {column_name} {column_type}')
            print(f' Added column: {column_name}')
        except sqlite3.OperationalError as e:
            if 'duplicate column name' in str(e):
                print(f'⚠️ Column {column_name} already exists')
            else:
                print(f' Error adding {column_name}: {e}')
    
    conn.commit()
    conn.close()
    print('\n Database migration completed!')

if __name__ == '__main__':
    migrate_database()
