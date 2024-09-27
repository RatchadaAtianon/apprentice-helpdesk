import sqlite3
from flask_bcrypt import Bcrypt

# Initialize Bcrypt (make sure your Flask app is available)
bcrypt = Bcrypt()  # This assumes you have your Flask app context available

def insert_users():
    conn = sqlite3.connect('helpdesk.db')
    cursor = conn.cursor()

    # Sample users
    users = [
        ('apprentice1', 'password123', 'apprentice1@example.com', 'apprentice'),
        ('apprentice2', 'password123', 'apprentice2@example.com', 'apprentice'),
        ('apprentice3', 'password123', 'apprentice3@example.com', 'apprentice'),
        ('apprentice4', 'password123', 'apprentice4@example.com', 'apprentice'),
        ('apprentice5', 'password123', 'apprentice5@example.com', 'apprentice'),
        ('admin1', 'adminpassword', 'admin1@example.com', 'admin'),
        ('admin2', 'adminpassword', 'admin2@example.com', 'admin'),
        ('admin3', 'adminpassword', 'admin3@example.com', 'admin'),
        ('admin4', 'adminpassword', 'admin4@example.com', 'admin'),
        ('admin5', 'adminpassword', 'admin5@example.com', 'admin'),
    ]

    for username, password, email, role in users:
        # Hash the password using Flask-Bcrypt
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')  # Hash the password

        try:
            cursor.execute('''
                INSERT INTO users (username, password, email, role) 
                VALUES (?, ?, ?, ?)
            ''', (username, hashed_password, email, role))
        except sqlite3.IntegrityError:
            print(f"User {username} already exists.")

    conn.commit()
    conn.close()


def insert_tickets():
    conn = sqlite3.connect('helpdesk.db')
    cursor = conn.cursor()

    # Sample tickets
    tickets = [
        (1, 'Issue with laptop', 'My laptop won\'t turn on.', 'High', 'open'),
        (2, 'Software installation', 'Need help installing software.', 'High', 'open'),
        (3, 'Network issue', 'Internet connection is slow.', 'Medium', 'open'),
        (1, 'Printer not working', 'Printer is out of paper.', 'Low', 'closed'),
        (2, 'Email access', 'Can\'t access my email.', 'Medium', 'in_progress'),
        (3, 'Update request', 'Requesting an update for my software.', 'Medium', 'in_progress'),
        (1, 'Forgot password', 'I forgot my password.', 'High', 'open'),
        (2, 'System crash', 'My computer crashed.', 'High', 'open'),
        (3, 'Request for equipment', 'Requesting new equipment.', 'Low', 'closed'),
        (1, 'Training issue', 'Having trouble accessing training materials.', 'Medium', 'open'),
    ]

    for user_id, title, description, priority, status in tickets:
        cursor.execute('''
            INSERT INTO tickets (user_id, title, description, priority, status) 
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, title, description, priority, status))

    conn.commit()
    conn.close()

if __name__ == '__main__':
    insert_users()
    insert_tickets()
