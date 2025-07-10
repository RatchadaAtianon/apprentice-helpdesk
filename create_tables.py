import sqlite3


def init_db():
    conn = sqlite3.connect('helpdesk.db')
    cursor = conn.cursor()

    # Drop tables if they exist
    cursor.execute('DROP TABLE IF EXISTS tickets')
    cursor.execute('DROP TABLE IF EXISTS users')

    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            email TEXT,
            role TEXT NOT NULL CHECK(role IN ('apprentice', 'admin'))
        )
    ''')

    # Create tickets table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tickets (
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

    conn.commit()
    conn.close()


if __name__ == '__main__':
    init_db()
