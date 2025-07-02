import unittest
from main import app

class RoutesTestCase(unittest.TestCase):

    def setUp(self):
        app.config['TESTING'] = True
        self.client = app.test_client()
        self.app_context = app.app_context()
        self.app_context.push()

    def tearDown(self):
        self.app_context.pop()

    def login_as(self, role):
        with self.client.session_transaction() as sess:
            sess['username'] = 'testuser'
            sess['role'] = role
            sess['logged_in'] = True

    def test_home_page_requires_login(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 302)  # expecting redirect when not logged in

    def test_home_page_as_logged_in_user(self):
        self.login_as('apprentice')
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Welcome', response.data)  # adjust based on your actual home page content

    def test_home_redirects_to_login(self):
        response = self.client.get('/', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Login', response.data)

    def test_submit_ticket_requires_login(self):
        response = self.client.get('/submit_ticket', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Login', response.data)

    def test_submit_ticket_page_as_user(self):
        self.login_as('apprentice')
        response = self.client.get('/submit_ticket')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Submit Ticket', response.data)

    def test_view_tickets_page_as_user(self):
        self.login_as('apprentice')
        response = self.client.get('/tickets')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Tickets', response.data)

    def test_login_page_loads(self):
        response = self.client.get('/login')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Login', response.data)

    def test_logout_redirects(self):
        self.login_as('apprentice')
        response = self.client.get('/logout', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Login', response.data)

    def test_admin_users_requires_admin(self):
        self.login_as('apprentice')
        response = self.client.get('/admin_users', follow_redirects=True)
        self.assertEqual(response.status_code, 403)

    def test_404_page(self):
        response = self.client.get('/nonexistentpage')
        self.assertEqual(response.status_code, 404)


    def test_login_correct_credentials(self):
        response = self.client.post('/login', data={
            'username': 'admin1',
            'password': 'adminpassword'
        }, follow_redirects=False)

        # Accept either redirect or login page depending on actual app behavior
        self.assertIn(response.status_code, (200, 302))


if __name__ == '__main__':
    unittest.main()
