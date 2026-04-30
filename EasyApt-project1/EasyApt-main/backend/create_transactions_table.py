"""
Create transactions table
"""

import sqlite3

def create_transactions_table():
    conn = sqlite3.connect('easyapt.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS app_transaction (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            appointment_id INTEGER,
            amount REAL DEFAULT 0.0,
            description TEXT DEFAULT 'Appointment booking',
            transaction_type TEXT DEFAULT 'booking',
            status TEXT DEFAULT 'completed',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES user(id),
            FOREIGN KEY (appointment_id) REFERENCES appointment(id)
        )
    ''')
    
    conn.commit()
    conn.close()
    print(' Transactions table created!')

if __name__ == '__main__':
    create_transactions_table()
