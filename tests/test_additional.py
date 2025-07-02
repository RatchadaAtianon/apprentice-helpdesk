import unittest
from main import app, get_db_connection
from flask import session

class AdditionalTests(unittest.TestCase):

    def setUp(self):
        app.config['TESTING'] = True
        self.client = app.test_client()
        self.app_context = app.app_context()
        self.app_context.push()

        # Insert a test user for registration conflict tests
        conn = get_db_connection()
        conn.execute('DELETE FROM users WHERE username = ?', ('testuser',))
        conn.execute('INSERT INTO users (username, email, password, role) VALUES (?, ?, ?, ?)',
                     ('testuser', 'test@example.com', 'hashedpassword', 'apprentice'))
        conn.commit()
        conn.close()

    def tearDown(self):
        self.app_context.pop()

    def login_as_admin(self):
        self.client.post('/login', data=dict(
            username='adminuser',
            password='adminpassword'
        ), follow_redirects=True)


    def login_as_apprentice(self):
        self.client.post('/login', data={
            'username': 'apprentice3',
            'password': 'password123'
        })

    # 1. Registration tests


    def test_register_existing_user(self):
        response = self.client.post('/register', data={
            'username': 'testuser',  # already exists from setUp
            'email': 'test@example.com',
            'password': 'password123'
        }, follow_redirects=True)
        self.assertIn(b'Email or username is already registered', response.data)

    # 2. Edit user (admin only)



    def test_edit_user_no_permission(self):
        self.login_as_apprentice()
        response = self.client.get('/admin/users/edit/1', follow_redirects=True)
        self.assertIn(b'You do not have permission', response.data)



    def test_delete_user_no_permission(self):
        self.login_as_apprentice()
        response = self.client.post('/admin/users/delete/1', follow_redirects=True)
        self.assertIn(b'You do not have permission', response.data)

    # 4. Delete closed tickets (admin only)


    def test_delete_closed_tickets_no_permission(self):
        self.login_as_apprentice()
        response = self.client.post('/admin/tickets/delete_closed', follow_redirects=True)
        self.assertIn(b'You do not have permission', response.data)

    # 5. Edit ticket GET and POST
    def test_edit_ticket_get(self):
        self.login_as_apprentice()
        # Assuming ticket with id=1 exists
        response = self.client.get('/edit_ticket/1')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Edit Ticket', response.data)

    def test_edit_ticket_post_valid(self):
        self.login_as_apprentice()
        response = self.client.post('/edit_ticket/1', data={
            'title': 'Updated title',
            'description': 'Updated description',
            'priority': 'High',
            'status': 'open'
        }, follow_redirects=True)
        self.assertIn(b'Ticket updated successfully', response.data)

    def test_edit_ticket_post_invalid(self):
        self.login_as_apprentice()
        response = self.client.post('/edit_ticket/1', data={
            'title': '',
            'description': '',
            'priority': 'Low',
            'status': 'open'
        }, follow_redirects=True)
        self.assertIn(b'Title and description are required', response.data)

    # 6. Search route tests



    # 7. API tickets endpoint
    def test_api_tickets(self):
        self.login_as_apprentice()
        response = self.client.get('/api/tickets')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.is_json)
        data = response.get_json()
        self.assertIsInstance(data, list)

if __name__ == '__main__':
    unittest.main()
