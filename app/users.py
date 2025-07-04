from flask import render_template, request, redirect, url_for, session, flash
from app import app
from app.db import get_db_connection

def admin_required(f):
    from functools import wraps
    from flask import abort

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            flash('You need to log in to manage users.', 'error')
            return redirect(url_for('login'))
        conn = get_db_connection()
        user = conn.execute('SELECT role FROM users WHERE username = ?', (session['username'],)).fetchone()
        conn.close()
        if not user or user['role'] != 'admin':
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

@app.route('/admin_users')
@admin_required
def admin_users():
    conn = get_db_connection()
    role_filter = request.args.get('role')
    if role_filter:
        users = conn.execute('SELECT * FROM users WHERE role = ?', (role_filter,)).fetchall()
    else:
        users = conn.execute('SELECT * FROM users').fetchall()
    conn.close()
    return render_template('admin_users.html', users=users, role=role_filter)

@app.route('/admin/users/edit/<int:user_id>', methods=['GET', 'POST'])
@admin_required
def edit_user(user_id):
    conn = get_db_connection()
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        role = request.form['role']

        conn.execute('UPDATE users SET username = ?, email = ?, role = ? WHERE id = ?',
                     (username, email, role, user_id))
        conn.commit()
        conn.close()

        flash('User updated successfully!', 'success')
        return redirect(url_for('admin_users'))

    user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    conn.close()
    return render_template('edit_user.html', user=user)

@app.route('/admin/users/delete/<int:user_id>', methods=['POST'])
@admin_required
def delete_user(user_id):
    try:
        conn = get_db_connection()
        conn.execute('DELETE FROM users WHERE id = ?', (user_id,))
        conn.commit()
        conn.close()
        flash('User deleted successfully!', 'success')
    except Exception as e:
        flash(f'An error occurred: {str(e)}', 'error')
    return redirect(url_for('admin_users'))
