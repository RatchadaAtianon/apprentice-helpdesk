import sqlite3


def get_db_connection():
    conn = sqlite3.connect('helpdesk.db')
    conn.row_factory = sqlite3.Row
    return conn


def get_ticket_by_id(ticket_id):
    conn = get_db_connection()
    ticket = conn.execute('SELECT * FROM tickets WHERE id = ?', (ticket_id,)).fetchone()
    conn.close()
    return ticket


def get_user_id(username):
    conn = get_db_connection()
    user = conn.execute('SELECT id FROM users WHERE username = ?', (username,)).fetchone()
    conn.close()
    return user['id'] if user else None
