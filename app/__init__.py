# app/__init__.py
import os
from flask import Flask
from flask_bcrypt import Bcrypt
from flask_mail import Mail
from itsdangerous import URLSafeTimedSerializer

def env_bool(name: str, default: str = "false") -> bool:
    return os.getenv(name, default).strip().lower() in {"1", "true", "yes", "on"}

app = Flask(__name__)

# after app = Flask(__name__)
import os

sender_email = os.getenv("MAIL_DEFAULT_EMAIL") or os.getenv("MAIL_USERNAME") or "no-reply@example.com"

app.config.update(
    SECRET_KEY=os.getenv("SECRET_KEY", "dev-change-me"),
    MAIL_SERVER=os.getenv("MAIL_SERVER", "smtp.gmail.com"),
    MAIL_PORT=int(os.getenv("MAIL_PORT", "587")),
    MAIL_USE_TLS=os.getenv("MAIL_USE_TLS", "true").lower() in ("1","true","yes","on"),
    MAIL_USE_SSL=os.getenv("MAIL_USE_SSL", "false").lower() in ("1","true","yes","on"),
    MAIL_USERNAME=os.getenv("MAIL_USERNAME", ""),
    MAIL_PASSWORD=os.getenv("MAIL_PASSWORD", ""),
    MAIL_DEFAULT_SENDER=(
        os.getenv("MAIL_DEFAULT_NAME", "Apprentice Helpdesk"),
        sender_email,
    ),
    MAIL_SUPPRESS_SEND=os.getenv("MAIL_SUPPRESS_SEND", "false").lower() in ("1","true","yes","on"),
)


# Keep app.secret_key in sync
app.secret_key = app.config["SECRET_KEY"]

# ---- Extensions ----
bcrypt = Bcrypt(app)
mail = Mail(app)
ts = URLSafeTimedSerializer(app.config["SECRET_KEY"])

# ---- Import routes AFTER config & extensions ----
from app import auth, users, tickets, api  # noqa: E402,F401
