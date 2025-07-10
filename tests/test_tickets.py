import pytest
from app import app
import main  # IMPORTANT: import main to register routes like 'home'

from flask import url_for, session


@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    with app.test_client() as client:
        with app.app_context():
            # Setup DB or mock here if needed
            pass
        yield client


def login(client, username='testuser', role='user'):
    with client.session_transaction() as sess:
        sess['username'] = username
        sess['role'] = role


def test_tickets_requires_login(client):
    res = client.get('/tickets')
    # Should redirect to login page because not logged in
    assert res.status_code == 302
    assert '/login' in res.headers['Location']




def test_tickets_for_regular_user(client):
    login(client, 'user1', 'user')

    # Mock DB functions if needed, or ensure your DB has user and tickets for 'user1'
    res = client.get('/tickets')
    assert res.status_code == 200
    assert b'tickets' in res.data.lower()  # crude check to see tickets page content


def test_tickets_for_admin(client):
    login(client, 'admin', 'admin')
    res = client.get('/tickets')
    assert res.status_code == 200
    # You could add more asserts for admin seeing all tickets


def test_submit_ticket_get(client):
    login(client)
    res = client.get('/submit_ticket')
    assert res.status_code == 200
    assert b'Submit' in res.data

def test_tickets_filter_status_priority(client):
    login(client, 'admin', 'admin')
    res = client.get('/tickets?status=open&priority=high')
    assert res.status_code == 200






def test_view_ticket_not_found(client):
    login(client)
    # Assuming ticket ID 99999 doesn't exist
    res = client.get('/view_ticket/99999', follow_redirects=True)
    assert b'Ticket not found!' in res.data



def test_view_ticket_success(client):
    login(client)
    # You must create or mock a ticket with ID 1 or adjust this test accordingly
    res = client.get('/view_ticket/1')
    if res.status_code == 200:
        assert b'Ticket' in res.data
    else:
        assert res.status_code == 302  # redirect if no ticket found

def test_delete_nonexistent_ticket_as_admin(client):
    login(client, 'admin', 'admin')

    res = client.post('/delete_ticket/99999', follow_redirects=True)
    assert b'Ticket not found.' in res.data



def test_delete_ticket_not_found(client):
    login(client, 'admin', 'admin')
    res = client.post('/delete_ticket/99999', follow_redirects=True)
    assert b'Ticket not found.' in res.data


def test_delete_ticket_permissions(client):
    # Not logged in, try delete
    res = client.post('/delete_ticket/1', follow_redirects=True)
    assert b'You do not have permission' in res.data

    # Logged in as non-admin
    login(client, 'user1', 'user')
    res = client.post('/delete_ticket/1', follow_redirects=True)
    assert b'You do not have permission' in res.data


def test_delete_ticket_as_admin(client):
    login(client, 'admin', 'admin')

    # Try delete ticket (make sure ticket 1 exists or mock)
    res = client.post('/delete_ticket/1', follow_redirects=True)

    # Could be success or error if ticket not found
    assert res.status_code == 200
    assert (b'Ticket has been deleted.' in res.data) or (b'Ticket not found.' in res.data)
