import unittest
from main import app, get_db_connection
from flask import session

class RoutesTestCase(unittest.TestCase):
    def setUp(self):
        # Creates a test client
        self.app = app.test_client()
        self.app.testing = True

    def login_as(self, role):
        with self.app.session_transaction() as sess:
            sess['username'] = 'testuser'
        sess['role'] = role

    def test_home_redirects_to_login(self):
        response = self.app.get('/', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Login', response.data)

    def test_submit_ticket_requires_login(self):
        response = self.app.get('/submit_ticket', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Login', response.data)

    def test_submit_ticket_page_as_user(self):
        self.login_as('apprentice')
        response = self.app.get('/submit_ticket')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Submit Ticket', response.data)

    def test_view_tickets_page_as_user(self):
        self.login_as('apprentice')
        response = self.app.get('/tickets')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Tickets', response.data)

    def test_login_page_loads(self):
        response = self.app.get('/login')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Login', response.data)

    def test_logout_redirects(self):
        self.login_as('apprentice')
        response = self.app.get('/logout', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Login', response.data)

    def test_admin_users_requires_admin(self):
        # Try as regular user
        self.login_as('apprentice')
        response = self.app.get('/admin_users', follow_redirects=True)
        self.assertEqual(response.status_code, 403)


    def test_404_page(self):
        response = self.app.get('/nonexistentpage')
        self.assertEqual(response.status_code, 404)

if __name__ == '__main__':
    unittest.main()
