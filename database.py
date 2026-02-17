import sqlite3
from datetime import datetime
import hashlib
import os

def init_db():
 

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        full_name TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Create predictions table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS predictions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        image_path TEXT,
        age INTEGER,
        bmi REAL,
        glucose_level REAL,
        insulin_level REAL,
        ca19_9 REAL,
        cea REAL,
        symptoms TEXT,
        prediction_result TEXT,
        confidence_score REAL,
        explanation TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')
    
    # Create patient_records table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS patient_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        record_type TEXT,
        value TEXT,
        date_recorded TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')
    
    conn.commit()
    conn.close()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn