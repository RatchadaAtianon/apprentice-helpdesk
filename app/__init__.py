# app/__init__.py
import os
from flask import Flask
from flask_bcrypt import Bcrypt
from flask_mail import Mail
from itsdangerous import URLSafeTimedSerializer


def env_bool(name: str, default: str = "false") -> bool:
    return os.getenv(name, default).strip().lower() in {"1", "true", "yes", "on"}


app = Flask(__name__)

# -------- Core config --------
# Booleans from env
use_ssl = env_bool("MAIL_USE_SSL", "false")
use_tls = env_bool("MAIL_USE_TLS", "true")

# Avoid enabling both SSL and TLS
if use_ssl:
    use_tls = False

# Sender (fall back to username, then a dummy address)
sender_email = os.getenv("MAIL_DEFAULT_EMAIL") or os.getenv("MAIL_USERNAME") or "no-reply@example.com"
sender_name = os.getenv("MAIL_DEFAULT_NAME", "Apprentice Helpdesk")

app.config.update(
    # Flask
    SECRET_KEY=os.getenv("SECRET_KEY", "dev-change-me"),
    TESTING=env_bool("TESTING", "false"),

    # Mail
    MAIL_SERVER=os.getenv("MAIL_SERVER", "smtp.gmail.com"),
    MAIL_PORT=int(os.getenv("MAIL_PORT", "465" if use_ssl else "587")),
    MAIL_USE_TLS=use_tls,
    MAIL_USE_SSL=use_ssl,
    MAIL_USERNAME=os.getenv("MAIL_USERNAME", ""),
    MAIL_PASSWORD=os.getenv("MAIL_PASSWORD", ""),
    MAIL_DEFAULT_SENDER=(sender_name, sender_email),
    MAIL_SUPPRESS_SEND=env_bool("MAIL_SUPPRESS_SEND", "false"),
)

# Do not actually send emails during tests
if app.config["TESTING"]:
    app.config["MAIL_SUPPRESS_SEND"] = True

# Keep app.secret_key in sync
app.secret_key = app.config["SECRET_KEY"]

# -------- Extensions --------
bcrypt = Bcrypt(app)
mail = Mail(app)
ts = URLSafeTimedSerializer(app.config["SECRET_KEY"])

# -------- Import routes AFTER config & extensions --------
from app import auth, users, tickets, api  # noqa: E402,F401
