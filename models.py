import sqlite3
from datetime import datetime

class User:
    def __init__(self, username, email, password, full_name=None):
        self.username = username
        self.email = email
        self.password = password
        self.full_name = full_name
        self.created_at = datetime.now()
    
    def save(self):
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO users (username, email, password, full_name)
            VALUES (?, ?, ?, ?)
        ''', (self.username, self.email, self.password, self.full_name))
        conn.commit()
        conn.close()
    
    @staticmethod
    def get_by_username(username):
        conn = sqlite3.connect('database.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
        user = cursor.fetchone()
        conn.close()
        return user
    
    @staticmethod
    def get_by_email(email):
        conn = sqlite3.connect('database.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
        user = cursor.fetchone()
        conn.close()
        return user

class Prediction:
    @staticmethod
    def save_prediction(user_id, data):
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO predictions 
            (user_id, image_path, age, bmi, glucose_level, insulin_level, 
             ca19_9, cea, symptoms, prediction_result, confidence_score, explanation)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            user_id, data.get('image_path'), data.get('age'), data.get('bmi'),
            data.get('glucose_level'), data.get('insulin_level'), data.get('ca19_9'),
            data.get('cea'), data.get('symptoms'), data.get('prediction_result'),
            data.get('confidence_score'), data.get('explanation')
        ))
        conn.commit()
        prediction_id = cursor.lastrowid
        conn.close()
        return prediction_id
    
    @staticmethod
    def get_user_predictions(user_id):
        conn = sqlite3.connect('database.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM predictions 
            WHERE user_id = ? 
            ORDER BY created_at DESC
        ''', (user_id,))
        predictions = cursor.fetchall()
        conn.close()
        return predictions