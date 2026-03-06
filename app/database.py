import sqlite3
import json
from datetime import datetime
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'history.db')

def init_db():
    """Initializes the SQLite database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS scans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            total_waste REAL,
            storage_waste REAL,
            compute_waste REAL,
            total_gb REAL,
            idle_ec2_count INTEGER,
            zombie_vols_count INTEGER,
            raw_data TEXT
        )
    ''')
    conn.commit()
    conn.close()

def save_scan(data):
    """Saves scan results to the database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO scans (
            total_waste, storage_waste, compute_waste, total_gb, 
            idle_ec2_count, zombie_vols_count, raw_data
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        data['total_waste'],
        data['storage_waste'],
        data['compute_waste'],
        data['total_gb'],
        len(data['idle_ec2']),
        len(data['zombie_vols']),
        json.dumps(data)
    ))
    
    conn.commit()
    conn.close()

def get_history(limit=10):
    """Retrieves the last N scan results."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM scans ORDER BY timestamp DESC LIMIT ?', (limit,))
    rows = cursor.fetchall()
    
    history = []
    for row in rows:
        history.append(dict(row))
    
    conn.close()
    return history[::-1] # Return in chronological order for charts

if __name__ == "__main__":
    init_db()
    print("Database initialized.")
