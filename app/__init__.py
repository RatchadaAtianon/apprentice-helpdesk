from flask import Flask
from flask_bcrypt import Bcrypt

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Use env var in production!

bcrypt = Bcrypt(app)

from app import auth, users, tickets, api  # Import your route modules here
