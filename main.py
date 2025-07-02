from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import sqlite3
from flask_bcrypt import Bcrypt

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Set a secret key for session management
bcrypt = Bcrypt(app)  # Initialise Bcrypt

def get_db_connection():
    conn = sqlite3.connect('helpdesk.db')
    conn.row_factory = sqlite3.Row  # This makes the rows behave like dictionaries
    return conn

def get_ticket_by_id(ticket_id):
    conn = get_db_connection()
    ticket = conn.execute('SELECT * FROM tickets WHERE id = ?', (ticket_id,)).fetchone()
    conn.close()
    return ticket  # Added return statement

def get_user_id(username):
    conn = get_db_connection()
    user = conn.execute('SELECT id FROM users WHERE username = ?', (username,)).fetchone()
    conn.close()
    return user['id'] if user else None

@app.route('/')
def home():
    if 'username' in session:
        return render_template('index.html')  # Render the welcome page if logged in
    return redirect(url_for('login'))  # Redirect to login if not logged in

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()

        if user and bcrypt.check_password_hash(user['password'], password):  # Check hashed password
            session['username'] = user['username']
            session['role'] = user['role']  # Store the role in the session

            flash('Login successful!', 'success')
            return redirect(url_for('home'))  # Redirect to the homepage

        flash('Invalid credentials. Please try again.', 'error')

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        # Hash the password
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        conn = get_db_connection()

        existing_user = conn.execute('SELECT * FROM users WHERE email = ? OR username = ?',
                                     (email, username)).fetchone()

        if existing_user:
            flash('Email or username is already registered. Please log in.', 'error')
            conn.close()
            return redirect(url_for('register'))

        # Insert the new user with the 'apprentice' role
        conn.execute('INSERT INTO users (username, email, password, role) VALUES (?, ?, ?, ?)',
                     (username, email, hashed_password, 'apprentice'))
        conn.commit()

        # Fetch the newly created user to get their role
        new_user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()

        # Store both username and role in session
        session['username'] = new_user['username']
        session['role'] = new_user['role']  # Store the role in the session

        flash('Registration successful! You are now logged in.', 'success')
        return redirect(url_for('home'))

    return render_template('register.html')

@app.route('/logout')
def logout():
    session.pop('username', None)  # Log the user out
    return redirect(url_for('login'))


@app.route('/faq')
def faq():
    return render_template('faq.html')

@app.route('/admin_users')
def admin_users():
    if 'username' not in session:
        flash('You need to log in to manage users.', 'error')
        return redirect(url_for('login'))

    conn = get_db_connection()
    role_filter = request.args.get('role')

    if role_filter:
        users = conn.execute('SELECT * FROM users WHERE role = ?', (role_filter,)).fetchall()
    else:
        users = conn.execute('SELECT * FROM users').fetchall()

    conn.close()
    return render_template('admin_users.html', users=users, role=role_filter)

@app.route('/admin/users/edit/<int:user_id>', methods=['GET', 'POST'])
def edit_user(user_id):
    if 'username' not in session or session.get('role') != 'admin':
        flash('You do not have permission to view this page.', 'error')
        return redirect(url_for('home'))

    conn = get_db_connection()

    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        role = request.form['role']

        conn.execute('UPDATE users SET username = ?, email = ?, role = ? WHERE id = ?', (username, email, role, user_id))
        conn.commit()
        conn.close()

        flash('User updated successfully!', 'success')
        return redirect(url_for('admin_users'))

    user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    conn.close()
    return render_template('edit_user.html', user=user)

@app.route('/admin/users/delete/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    if 'username' not in session or session.get('role') != 'admin':
        flash('You do not have permission to perform this action.', 'error')
        return redirect(url_for('home'))

    try:
        conn = get_db_connection()
        conn.execute('DELETE FROM users WHERE id = ?', (user_id,))
        conn.commit()
        conn.close()
        flash('User deleted successfully!', 'success')
    except Exception as e:
        flash(f'An error occurred: {str(e)}', 'error')

    return redirect(url_for('admin_users'))

@app.route('/admin/tickets/delete_closed', methods=['POST'])
def delete_ticket():
    if 'username' not in session or session.get('role') != 'admin':
        flash('You do not have permission to perform this action.', 'error')
        return redirect(url_for('home'))

    conn = get_db_connection()
    conn.execute('DELETE FROM tickets WHERE status = ?', ('closed',))
    conn.commit()
    conn.close()

    flash('Closed tickets have been deleted successfully!', 'success')
    return redirect(url_for('tickets'))

@app.route('/tickets')
def tickets():
    if 'username' not in session:
        flash('You need to log in to view your tickets.', 'error')
        return redirect(url_for('login'))

    conn = get_db_connection()

    if session.get('role') == 'admin':
        query = '''
            SELECT tickets.*, users.username
            FROM tickets
            JOIN users ON tickets.user_id = users.id
            WHERE 1 = 1  -- Placeholder to simplify query building
        '''
        params = []
    else:
        user_id = get_user_id(session['username'])
        query = '''
            SELECT tickets.*, users.username
            FROM tickets
            JOIN users ON tickets.user_id = users.id
            WHERE tickets.user_id = ?
        '''
        params = [user_id]

    # Handle status filter
    status_filter = request.args.get('status')
    if status_filter:
        query += ' AND tickets.status = ?'
        params.append(status_filter)

    # Handle priority filter
    priority_filter = request.args.get('priority')
    if priority_filter:
        query += ' AND tickets.priority = ?'
        params.append(priority_filter)

    tickets = conn.execute(query, params).fetchall()
    conn.close()

    return render_template('tickets.html', tickets=tickets)

@app.route('/view_ticket/<int:ticket_id>', methods=['GET'])
def view_ticket(ticket_id):
    ticket = get_ticket_by_id(ticket_id)

    if not ticket:
        flash("Ticket not found!", "danger")
        return redirect(url_for('tickets'))

    return render_template('view_ticket.html', ticket=ticket)


@app.route('/search')
def search():
    username_query = request.args.get('apprentice_username', '').strip()

    if not username_query:
        flash("No search term provided.", "error")
        return redirect(url_for('home'))

    conn = get_db_connection()
    # Query tickets joined with users, filter by username like input
    results = conn.execute('''
        SELECT tickets.*, users.username
        FROM tickets
        JOIN users ON tickets.user_id = users.id
        WHERE users.username LIKE ?
    ''', (f'%{username_query}%',)).fetchall()
    conn.close()

    return render_template('search_results.html', results=results, query=username_query)

@app.route('/submit_ticket', methods=['GET', 'POST'])
def submit_ticket():
    if request.method == 'POST':
        if 'username' not in session:
            return redirect(url_for('login'))

        title = request.form['title']
        description = request.form['description']
        priority = request.form['priority']
        user_id = get_user_id(session['username'])

        conn = get_db_connection()
        conn.execute('''
            INSERT INTO tickets (user_id, title, description, priority, status)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, title, description, priority, 'open'))
        conn.commit()
        conn.close()

        flash('Ticket submitted successfully!', 'success')
        return redirect(url_for('tickets'))

    return render_template('submit_ticket.html')

@app.route('/edit_ticket/<int:ticket_id>', methods=['GET', 'POST'])
def edit_ticket(ticket_id):
    conn = get_db_connection()
    ticket = conn.execute('SELECT * FROM tickets WHERE id = ?', (ticket_id,)).fetchone()

    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        priority = request.form['priority']
        status = request.form['status']

        if not title or not description:
            flash('Title and description are required!', 'error')
            return redirect(url_for('edit_ticket', ticket_id=ticket_id))

        conn.execute('''
            UPDATE tickets
            SET title = ?, description = ?, priority = ?, status = ?
            WHERE id = ?
        ''', (title, description, priority, status, ticket_id))
        conn.commit()
        conn.close()

        flash('Ticket updated successfully!', 'success')
        return redirect(url_for('tickets'))

    return render_template('edit_ticket.html', ticket=ticket)

@app.route('/api/tickets', methods=['GET'])
def api_tickets():
    conn = get_db_connection()
    tickets = conn.execute('SELECT * FROM tickets').fetchall()
    conn.close()

    return jsonify([dict(ticket) for ticket in tickets])  # Convert to a list of dictionaries

if __name__ == '__main__':
    app.run(debug=True)

