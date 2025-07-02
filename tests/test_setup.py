# tests/test_setup.py
import sqlite3
from flask_bcrypt import Bcrypt

def init_test_db():
    bcrypt = Bcrypt()
    conn = sqlite3.connect('helpdesk.db')
    cursor = conn.cursor()

    cursor.execute('DROP TABLE IF EXISTS tickets')
    cursor.execute('DROP TABLE IF EXISTS users')

    # Create tables
    cursor.execute('''
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            email TEXT,
            role TEXT CHECK(role IN ('apprentice', 'admin')) NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            priority TEXT CHECK(priority IN ('High', 'Medium', 'Low')),
            status TEXT CHECK(status IN ('open', 'in_progress', 'closed')),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    # Insert a test apprentice and test admin
    users = [
        ('apprentice_user', bcrypt.generate_password_hash('pass').decode(), 'a@example.com', 'apprentice'),
        ('admin_user', bcrypt.generate_password_hash('pass').decode(), 'admin@example.com', 'admin'),
    ]
    cursor.executemany('INSERT INTO users (username, password, email, role) VALUES (?, ?, ?, ?)', users)

    # Insert sample tickets
    tickets = [
        (1, 'Issue 1', 'Description 1', 'High', 'open'),
        (1, 'Issue 2', 'Description 2', 'Low', 'closed'),
    ]
    cursor.executemany('INSERT INTO tickets (user_id, title, description, priority, status) VALUES (?, ?, ?, ?, ?)', tickets)

    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_test_db()
