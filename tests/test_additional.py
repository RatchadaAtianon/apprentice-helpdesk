import unittest
from flask_bcrypt import Bcrypt
from main import app
from app.db import get_db_connection



class AdditionalTests(unittest.TestCase):
    def setUp(self):
        # Configure test environment
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['SECRET_KEY'] = 'test-secret-key'

        self.client = app.test_client()
        self.app_context = app.app_context()
        self.app_context.push()

        # Initialise Bcrypt
        self.bcrypt = Bcrypt(app)

        # Set up test database
        self.setup_test_data()

    def setup_test_data(self):
        conn = get_db_connection()

        # Clear existing test data
        conn.execute('DELETE FROM tickets')
        conn.execute('DELETE FROM users')

        # Create test users with properly hashed passwords
        hashed_password = self.bcrypt.generate_password_hash('testpassword').decode('utf-8')

        # Admin user (id=1)
        conn.execute('''
            INSERT INTO users (id, username, email, password, role) 
            VALUES (?, ?, ?, ?, ?)
        ''', (1, 'adminuser', 'admin@example.com', hashed_password, 'admin'))

        # Apprentice user (id=2)
        conn.execute('''
            INSERT INTO users (id, username, email, password, role) 
            VALUES (?, ?, ?, ?, ?)
        ''', (2, 'apprenticeuser', 'apprentice@example.com', hashed_password, 'apprentice'))

        # Test ticket owned by apprentice
        conn.execute('''
            INSERT INTO tickets (id, title, description, priority, status, user_id)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (1, 'Test Ticket', 'Test Description', 'Medium', 'open', 2))

        conn.commit()
        conn.close()

    def tearDown(self):
        # Clean up database
        conn = get_db_connection()
        conn.execute('DELETE FROM tickets')
        conn.execute('DELETE FROM users')
        conn.commit()
        conn.close()

        self.app_context.pop()

    # Helper methods
    def login(self, username, password):
        return self.client.post('/login',
                                data={'username': username, 'password': password},
                                follow_redirects=True)

    def login_as_admin(self):
        with self.client:
            response = self.login('adminuser', 'testpassword')
            self.assertEqual(response.status_code, 200)
            return response

    def login_as_apprentice(self):
        with self.client:
            response = self.login('apprenticeuser', 'testpassword')
            self.assertEqual(response.status_code, 200)
            return response

    # Test cases
    def test_register_existing_user(self):
        response = self.client.post('/register',
                                    data={
                                        'username': 'apprenticeuser',
                                        'email': 'existing@example.com',
                                        'password': 'password123'
                                    },
                                    follow_redirects=True)
        self.assertIn(b'Email or username is already registered', response.data)

    def test_edit_user_no_permission(self):
        self.login_as_apprentice()
        response = self.client.get('/admin/users/edit/1', follow_redirects=True)
        # Check for either redirect or permission message
        self.assertTrue(
            response.status_code == 302 or
            b'You do not have permission' in response.data or
            b'Forbidden' in response.data
        )

    def test_delete_user_no_permission(self):
        self.login_as_apprentice()
        response = self.client.post('/admin/users/delete/1', follow_redirects=True)
        # Check for either redirect or permission message
        self.assertTrue(
            response.status_code == 302 or
            b'You do not have permission' in response.data or
            b'Forbidden' in response.data
        )



    def test_edit_ticket_get(self):
        self.login_as_apprentice()
        response = self.client.get('/edit_ticket/1')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Edit Ticket', response.data)

    def test_edit_ticket_post_valid(self):
        self.login_as_apprentice()
        response = self.client.post('/edit_ticket/1',
                                    data={
                                        'title': 'Updated title',
                                        'description': 'Updated description',
                                        'priority': 'High',
                                        'status': 'open'
                                    },
                                    follow_redirects=True)
        self.assertIn(b'Ticket updated successfully', response.data)

    def test_edit_ticket_post_invalid(self):
        self.login_as_apprentice()
        response = self.client.post('/edit_ticket/1',
                                    data={
                                        'title': '',
                                        'description': '',
                                        'priority': 'Low',
                                        'status': 'open'
                                    },
                                    follow_redirects=True)
        self.assertIn(b'Title and description are required', response.data)

    def test_api_tickets(self):
        self.login_as_apprentice()
        response = self.client.get('/api/tickets')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.is_json)
        data = response.get_json()
        self.assertIsInstance(data, list)
        self.assertGreater(len(data), 0)  # Should have at least our test ticket


if __name__ == '__main__':
    unittest.main()