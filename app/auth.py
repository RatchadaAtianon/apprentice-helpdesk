from flask import render_template, request, redirect, url_for, session, flash
from app import app, bcrypt
from app.db import get_db_connection


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()

        if user and bcrypt.check_password_hash(user['password'], password):
            session['username'] = user['username']
            session['role'] = user['role']
            flash('Login successful!', 'success')
            return redirect(url_for('home'))

        flash('Invalid credentials. Please try again.', 'error')
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        conn = get_db_connection()
        existing_user = conn.execute('SELECT * FROM users WHERE email = ? OR username = ?',
                                     (email, username)).fetchone()

        if existing_user:
            flash('Email or username is already registered. Please log in.', 'error')
            conn.close()
            return redirect(url_for('register'))

        conn.execute('INSERT INTO users (username, email, password, role) VALUES (?, ?, ?, ?)',
                     (username, email, hashed_password, 'apprentice'))
        conn.commit()

        new_user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()

        session['username'] = new_user['username']
        session['role'] = new_user['role']

        flash('Registration successful! You are now logged in.', 'success')
        return redirect(url_for('home'))

    return render_template('register.html')


@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('role', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))
