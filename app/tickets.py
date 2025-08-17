from flask import render_template, request, redirect, url_for, session, flash
from app import app
from app.db import get_db_connection, get_user_id, get_ticket_by_id


def login_required(f):
    from functools import wraps
    from flask import redirect, url_for, flash

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            flash('You need to log in to view this page.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)

    return decorated_function


def admin_required(f):
    from functools import wraps

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session or session.get('role') != 'admin':
            flash('You do not have permission to view this page.', 'error')
            return redirect(url_for('home'))
        return f(*args, **kwargs)

    return decorated_function


@app.route('/tickets')
@login_required
def tickets():
    conn = get_db_connection()

    # Base query + join so we can filter by username and show it in the template
    query = '''
        SELECT
            tickets.*,
            users.username,
            users.id AS apprentice_id
        FROM tickets
        JOIN users ON tickets.user_id = users.id
        WHERE 1=1
    '''
    params = []

    is_admin = (session.get('role') == 'admin')

    # Restrict non-admins to their own tickets
    if not is_admin:
        query += ' AND tickets.user_id = ?'
        params.append(get_user_id(session['username']))

    # Common filters
    status_filter = (request.args.get('status') or '').strip()
    if status_filter:
        query += ' AND tickets.status = ?'
        params.append(status_filter)

    priority_filter = (request.args.get('priority') or '').strip()
    if priority_filter:
        query += ' AND tickets.priority = ?'
        params.append(priority_filter)

    # Admin-only filters
    if is_admin:
        apprentice_name = (request.args.get('apprentice_name') or '').strip()
        if apprentice_name:
            # case-insensitive partial match
            query += ' AND LOWER(users.username) LIKE ?'
            params.append(f"%{apprentice_name.lower()}%")

        apprentice_id = (request.args.get('apprentice_id') or '').strip()
        if apprentice_id:
            if apprentice_id.isdigit():
                query += ' AND users.id = ?'
                params.append(int(apprentice_id))
            else:
                flash('Apprentice ID must be numeric.', 'warning')
                # (No ID filter applied)

    # Order newest first (use created_at if available)
    query += ' ORDER BY tickets.id DESC'

    tickets = conn.execute(query, params).fetchall()
    conn.close()

    return render_template('tickets.html', tickets=tickets)


@app.route('/submit_ticket', methods=['GET', 'POST'])
@login_required
def submit_ticket():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        priority = request.form['priority']
        user_id = get_user_id(session['username'])

        conn = get_db_connection()
        conn.execute(
            'INSERT INTO tickets (user_id, title, description, priority, status) VALUES (?, ?, ?, ?, ?)',
            (user_id, title, description, priority, 'open')
        )
        conn.commit()
        conn.close()

        flash('Ticket submitted successfully!', 'success')
        return redirect(url_for('tickets'))

    return render_template('submit_ticket.html')


@app.route('/view_ticket/<int:ticket_id>')
@login_required
def view_ticket(ticket_id):
    ticket = get_ticket_by_id(ticket_id)
    if not ticket:
        flash("Ticket not found!", "error")
        return redirect(url_for('tickets'))
    return render_template('view_ticket.html', ticket=ticket)


@app.route('/edit_ticket/<int:ticket_id>', methods=['GET', 'POST'])
@login_required
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
            conn.close()
            return redirect(url_for('edit_ticket', ticket_id=ticket_id))

        conn.execute(
            'UPDATE tickets SET title = ?, description = ?, priority = ?, status = ? WHERE id = ?',
            (title, description, priority, status, ticket_id)
        )
        conn.commit()
        conn.close()

        flash('Ticket updated successfully!', 'success')
        return redirect(url_for('tickets'))

    conn.close()
    return render_template('edit_ticket.html', ticket=ticket)


@app.route('/delete_ticket/<int:ticket_id>', methods=['POST'])
@admin_required
def delete_ticket(ticket_id):
    conn = get_db_connection()
    ticket = conn.execute('SELECT * FROM tickets WHERE id = ?', (ticket_id,)).fetchone()
    if not ticket:
        conn.close()
        flash('Ticket not found.', 'error')
        return redirect(url_for('tickets'))

    conn.execute('DELETE FROM tickets WHERE id = ?', (ticket_id,))
    conn.commit()
    conn.close()

    flash(f"Ticket '{ticket['title']}' has been deleted.", 'success')
    return redirect(url_for('tickets'))
