import pytest
from unittest.mock import patch
import sqlite3
from app import app, bcrypt
import main

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False

    # Create in-memory SQLite DB and add test user
    conn = sqlite3.connect(':memory:')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            email TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            role TEXT NOT NULL
        )
    ''')

    hashed_pw = bcrypt.generate_password_hash('password123').decode('utf-8')
    cursor.execute('''
        INSERT INTO users (username, email, password, role)
        VALUES (?, ?, ?, ?)
    ''', ('testuser', 'test@example.com', hashed_pw, 'user'))
    conn.commit()

    # Patch get_db_connection to return this in-memory connection
    with patch('app.db.get_db_connection', return_value=conn):
        with app.test_client() as client:
            yield client

    conn.close()


def test_login_get(client):
    response = client.get('/login')
    assert response.status_code == 200
    assert b'Login' in response.data


def test_login_post_failure(client):
    response = client.post('/login', data={
        'username': 'wronguser',
        'password': 'wrongpassword'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Invalid credentials' in response.data


def test_register_get(client):
    response = client.get('/register')
    assert response.status_code == 200
    assert b'Register' in response.data




def test_logout(client):
    # First login
    client.post('/login', data={
        'username': 'testuser',
        'password': 'password123'
    }, follow_redirects=True)

    response = client.get('/logout', follow_redirects=True)
    assert response.status_code == 200
    assert b'You have been logged out.' in response.data
