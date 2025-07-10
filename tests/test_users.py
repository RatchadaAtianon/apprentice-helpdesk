import pytest
from unittest.mock import patch, MagicMock
from flask import url_for
import pytest

from main import app  # Import the Flask app with all routes from main.py

@pytest.fixture
def client():
    with app.test_client() as client:
        yield client


# Helper to mock a DB row
def make_user_row(id=1, username='admin', email='admin@example.com', role='admin'):
    return {'id': id, 'username': username, 'email': email, 'role': role}


# Mock get_db_connection to return a connection with mocked execute
class MockConnection:
    def __init__(self, users=None):
        self.users = users or []
        self.committed = False

    def execute(self, query, params=()):
        # Handle different queries here based on query string or params
        if 'SELECT role FROM users' in query:
            # Return a user row for role check
            mock_cursor = MagicMock()
            mock_cursor.fetchone.return_value = self.users[0] if self.users else None
            return mock_cursor
        elif 'SELECT * FROM users WHERE role' in query:
            mock_cursor = MagicMock()
            mock_cursor.fetchall.return_value = self.users
            return mock_cursor
        elif 'SELECT * FROM users WHERE id' in query:
            mock_cursor = MagicMock()
            mock_cursor.fetchone.return_value = self.users[0] if self.users else None
            return mock_cursor
        elif 'SELECT * FROM users' in query:
            mock_cursor = MagicMock()
            mock_cursor.fetchall.return_value = self.users
            return mock_cursor
        elif query.startswith('UPDATE users SET'):
            return MagicMock()
        elif query.startswith('DELETE FROM users'):
            return MagicMock()
        else:
            return MagicMock()

    def commit(self):
        self.committed = True

    def close(self):
        pass

# Test that access to admin_users redirects if no login
def test_admin_users_redirects_if_not_logged_in(client):
    response = client.get('/admin_users', follow_redirects=False)
    assert response.status_code == 302
    assert '/login' in response.headers['Location']

# Test admin_users page with admin logged in
@patch('app.users.get_db_connection')
def test_admin_users_page_with_admin(mock_get_conn, client):
    mock_conn = MockConnection(users=[make_user_row()])
    mock_get_conn.return_value = mock_conn

    with client.session_transaction() as sess:
        sess['username'] = 'admin'

    response = client.get('/admin_users')
    assert response.status_code == 200
    assert b'admin_users.html' not in response.data  # Template name won't be in response, but we can check content if needed

# Test admin_users filtering by role
@patch('app.users.get_db_connection')
def test_admin_users_filter_role(mock_get_conn, client):
    # Return an admin user for 'admin' username
    mock_conn = MockConnection(users=[make_user_row(username='admin', role='admin')])
    mock_get_conn.return_value = mock_conn

    with client.session_transaction() as sess:
        sess['username'] = 'admin'

    response = client.get('/admin_users?role=user')
    assert response.status_code == 200


# Test edit_user GET displays form
@patch('app.users.get_db_connection')
def test_edit_user_get(mock_get_conn, client):
    mock_conn = MockConnection(users=[make_user_row()])
    mock_get_conn.return_value = mock_conn

    with client.session_transaction() as sess:
        sess['username'] = 'admin'

    response = client.get('/admin/users/edit/1')
    assert response.status_code == 200

# Test edit_user POST updates user and redirects
@patch('app.users.get_db_connection')
def test_edit_user_post(mock_get_conn, client):
    mock_conn = MockConnection(users=[make_user_row()])
    mock_get_conn.return_value = mock_conn

    with client.session_transaction() as sess:
        sess['username'] = 'admin'

    data = {'username': 'newuser', 'email': 'new@example.com', 'role': 'user'}
    response = client.post('/admin/users/edit/1', data=data, follow_redirects=False)
    assert response.status_code == 302
    assert '/admin_users' in response.headers['Location']
    assert mock_conn.committed is True

# Test delete_user POST deletes user and redirects
@patch('app.users.get_db_connection')
def test_delete_user_post(mock_get_conn, client):
    mock_conn = MockConnection(users=[make_user_row()])
    mock_get_conn.return_value = mock_conn

    with client.session_transaction() as sess:
        sess['username'] = 'admin'

    response = client.post('/admin/users/delete/1', follow_redirects=False)
    assert response.status_code == 302
    assert '/admin_users' in response.headers['Location']
    assert mock_conn.committed is True

# Test access forbidden if user is not admin
@patch('app.users.get_db_connection')
def test_access_forbidden_for_non_admin(mock_get_conn, client):
    # Non-admin role
    mock_conn = MockConnection(users=[make_user_row(role='user')])
    mock_get_conn.return_value = mock_conn

    with client.session_transaction() as sess:
        sess['username'] = 'user'

    response = client.get('/admin_users')
    assert response.status_code == 403
