from flask import jsonify
from app import app
from app.db import get_db_connection


@app.route('/api/tickets', methods=['GET'])
def api_tickets():
    conn = get_db_connection()
    tickets = conn.execute('SELECT * FROM tickets').fetchall()
    conn.close()
    return jsonify([dict(ticket) for ticket in tickets])
