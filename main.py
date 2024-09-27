from flask import Flask, render_template, redirect, url_for, session
import sqlite3
from flask_bcrypt import Bcrypt
from flask import flash
from flask import request
import re

bcrypt = Bcrypt()


def create_app():
    app = Flask(__name__)
    app.secret_key = 'your_secret_key'  # Set a secret key for session management
    bcrypt.init_app(app)  # Initialize Bcrypt with the app

    # Routes
    app.add_url_rule('/', 'home', home)
    app.add_url_rule('/view_ticket/<int:ticket_id>', 'view_ticket', view_ticket)
    app.add_url_rule('/admin/users/edit/<int:user_id>', 'edit_user', edit_user, methods=['GET', 'POST'])
    app.add_url_rule('/admin/users/delete/<int:user_id>', 'delete_user', delete_user, methods=['POST'])
    app.add_url_rule('/admin/tickets/delete_closed', 'delete_ticket', delete_ticket, methods=['POST'])
    app.add_url_rule('/register', 'register', register, methods=['GET', 'POST'])
    app.add_url_rule('/login', 'login', login, methods=['GET', 'POST'])
    app.add_url_rule('/admin_users', 'admin_users', admin_users)
    app.add_url_rule('/logout', 'logout', logout)
    app.add_url_rule('/tickets', 'tickets', tickets)
    app.add_url_rule('/submit_ticket', 'submit_ticket', submit_ticket, methods=['GET', 'POST'])
    app.add_url_rule('/edit_ticket/<int:ticket_id>', 'edit_ticket', edit_ticket, methods=['GET', 'POST'])

    return app

def get_db_connection():
    conn = sqlite3.connect('helpdesk.db')
    conn.row_factory = sqlite3.Row  # This makes the rows behave like dictionaries
    return conn



def create_user(username, password, email):
    # Hash the password
    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

    conn = get_db_connection()
    try:
        # Insert the new user with the 'apprentice' role
        conn.execute('INSERT INTO users (username, email, password, role) VALUES (?, ?, ?, ?)',
                     (username, email, hashed_password, 'apprentice'))
        conn.commit()

        # Fetch the newly created user to get their role
        new_user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()

        # Store both username and role in session
        session['username'] = new_user['username']
        session['role'] = new_user['role']  # Store the role in the session
    except sqlite3.Error as e:
        flash(f'An error occurred: {str(e)}', 'error')
        return False
    finally:
        conn.close()
    return True


def register():
    if request.method == 'GET':
        return render_template('register.html')

    username = request.form.get('username')
    password = request.form.get('password')
    email = request.form.get('email')

    # Check if username, email, and password are provided
    if not username or not password or not email:
        flash('All fields are required.', 'error')
        return redirect('/register')

    # Validate username (8-16 characters, no special characters)
    if not re.match(r'^[a-zA-Z0-9]{8,16}$', username):
        flash('Username must be between 8-16 characters and contain only letters and numbers.', 'error')
        return redirect('/register')

    # Validate password (minimum 8 characters)
    if len(password) < 8:
        flash('Password must be at least 8 characters long.', 'error')
        return redirect('/register')

    # Validate email format
    if not re.match(r'^[\w\.-]+@[\w\.-]+$', email):
        flash('Invalid email format.', 'error')
        return redirect('/register')

    conn = get_db_connection()
    try:
        # Check if the username or email already exists in the database
        existing_user = conn.execute('SELECT * FROM users WHERE username = ? OR email = ?', (username, email)).fetchone()
        if existing_user:
            flash('Username or email already exists.', 'error')
            return redirect('/register')

        # Proceed with user registration
        if create_user(username, password, email):
            flash('Registration successful!', 'success')
            return redirect('/home')
    except Exception as e:
        flash('An error occurred during registration. Please try again.', 'error')
    finally:
        conn.close()

    return redirect('/register')


def get_ticket_by_id(ticket_id):
    connection = sqlite3.connect('your_database.db')
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,))
    ticket = cursor.fetchone()
    connection.close()
    return ticket


def view_ticket(ticket_id):
    conn = get_db_connection()
    ticket = conn.execute('SELECT * FROM tickets WHERE id = ?', (ticket_id,)).fetchone()
    conn.close()

    if ticket is None:
        flash('Ticket not found.', 'danger')
        return redirect(url_for('tickets'))

    return render_template('view_ticket.html', ticket=ticket)




def edit_user(user_id):
    if 'username' not in session or session.get('role') != 'admin':
        flash('You do not have permission to view this page.', 'error')
        return redirect(url_for('home'))

    conn = get_db_connection()

    if request.method == 'POST':
        # Update user information
        username = request.form['username']
        email = request.form['email']
        role = request.form['role']

        conn.execute('UPDATE users SET username = ?, email = ?, role = ? WHERE id = ?', (username, email, role, user_id))
        conn.commit()
        conn.close()

        flash('User updated successfully!', 'success')
        return redirect(url_for('admin_users'))

    # Fetch user data for pre-filling the form
    user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    conn.close()

    return render_template('edit_user.html', user=user)



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
    except sqlite3.Error as e:
        flash(f'An error occurred while deleting the user: {str(e)}', 'error')
    except Exception as e:
        flash(f'An unexpected error occurred: {str(e)}', 'error')
    finally:
        if conn:
            conn.close()

    return redirect(url_for('admin_users'))  # Ensure it redirects to the correct route






def delete_ticket():
    if 'username' not in session or session.get('role') != 'admin':
        flash('You do not have permission to perform this action.', 'error')
        return redirect(url_for('home'))

    conn = get_db_connection()
    conn.execute('DELETE FROM tickets WHERE status = ?', ('closed',))  # Adjust the column name and value as needed
    conn.commit()
    conn.close()

    flash('Ticket has been deleted successfully!', 'success')
    return redirect(url_for('tickets'))  # Adjust the redirect as necessary






def home():
    if 'username' in session:
        return render_template('index.html')  # Render the welcome page if logged in
    return redirect(url_for('login'))  # Redirect to login if not logged in







def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        # Fetch the user based on the username
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()

        if user and bcrypt.check_password_hash(user['password'], password):  # Check hashed password
            session['username'] = user['username']
            session['role'] = user['role']  # Store the role in the session

            flash('Login successful!', 'success')
            return redirect(url_for('home'))  # Redirect to the homepage or admin dashboard based on role

        flash('Invalid credentials. Please try again.', 'error')

    return render_template('login.html')



def admin_users():
    if 'username' not in session:
        flash('You need to log in to manage users.', 'error')
        return redirect(url_for('login'))

    conn = get_db_connection()

    # Get the filter value from the URL parameters
    role_filter = request.args.get('role')

    if role_filter:
        # If a role filter is applied, fetch users by that role
        users = conn.execute('SELECT * FROM users WHERE role = ?', (role_filter,)).fetchall()
    else:
        # If no filter is applied, fetch all users
        users = conn.execute('SELECT * FROM users').fetchall()

    conn.close()

    # Pass the selected role back to the template to keep the filter value selected
    return render_template('admin_users.html', users=users, role=role_filter)



def logout():
    session.pop('username', None)  # Log the user out
    return redirect(url_for('login'))



def tickets():
    if 'username' not in session:
        flash('You need to log in to view your tickets.', 'error')
        return redirect(url_for('login'))

    conn = get_db_connection()


    # Admin sees all tickets; regular users see only their tickets
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


    apprentice_username_filter = request.args.get('apprentice_username')
    if apprentice_username_filter:
        query += ' AND users.username LIKE ?'
        params.append(f"%{apprentice_username_filter}%")  # Use LIKE for partial matches

    # Execute the query with the collected params
    tickets = conn.execute(query, params).fetchall()
    conn.close()

    return render_template('tickets.html', tickets=tickets)



def submit_ticket():
    if request.method == 'POST':
        if 'username' not in session:
            return redirect(url_for('login'))  # Ensure the user is logged in

        title = request.form['title']
        description = request.form['description']
        priority = request.form['priority']
        user_id = get_user_id(session['username'])  # Get the user ID based on the logged-in username

        conn = get_db_connection()
        conn.execute('''
            INSERT INTO tickets (user_id, title, description, priority, status)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, title, description, priority, 'open'))
        conn.commit()
        conn.close()

        flash('Ticket submitted successfully!', 'success')  # Flash success message
        return redirect(url_for('tickets'))  # Redirect to the home page after submission

    return render_template('submit_ticket.html')



def edit_ticket(ticket_id):
    conn = get_db_connection()

    # Get the current ticket data
    ticket = conn.execute('SELECT * FROM tickets WHERE id = ?', (ticket_id,)).fetchone()

    if request.method == 'POST':
        # Fetch form data
        title = request.form['title']
        description = request.form['description']
        priority = request.form['priority']
        status = request.form['status']

        # Ensure form fields are not empty
        if not title or not description:
            flash('Title and description are required!', 'error')
            return redirect(url_for('edit_ticket', ticket_id=ticket_id))

        # Update the ticket in the database
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


def get_user_id(username):
    conn = get_db_connection()
    user = conn.execute('SELECT id FROM users WHERE username = ?', (username,)).fetchone()
    conn.close()
    return user['id'] if user else None


def get_tickets():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM tickets')
    tickets = cursor.fetchall()
    conn.close()
    return tickets


if __name__ == '__main__':
    app = create_app()  # Create the app using the factory function
    app.run(debug=True)  # Run the application