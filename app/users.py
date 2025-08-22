import os
from functools import wraps

from flask import (
    render_template, request, redirect, url_for, session, flash, abort
)
from werkzeug.security import generate_password_hash

from app import app
from app.db import get_db_connection

# --- Email + token deps ---
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired

# ------------------ App/Email Config ------------------
# Make sure SECRET_KEY is set elsewhere in your app; fallback here if needed
app.config.setdefault("SECRET_KEY", os.environ.get("SECRET_KEY", "change-me"))

# SMTP settings (use env vars in production)
app.config.setdefault("MAIL_SERVER", os.environ.get("MAIL_SERVER", "smtp.gmail.com"))
app.config.setdefault("MAIL_PORT", int(os.environ.get("MAIL_PORT", "587")))
app.config.setdefault("MAIL_USE_TLS", os.environ.get("MAIL_USE_TLS", "true").lower() == "true")
app.config.setdefault("MAIL_USERNAME", os.environ.get("MAIL_USERNAME", ""))   # your email/login
app.config.setdefault("MAIL_PASSWORD", os.environ.get("MAIL_PASSWORD", ""))   # app password
app.config.setdefault(
    "MAIL_DEFAULT_SENDER",
    (
        os.environ.get("MAIL_DEFAULT_NAME", "Apprentice Helpdesk"),
        os.environ.get("MAIL_DEFAULT_EMAIL", os.environ.get("MAIL_USERNAME", "")),
    ),
)

mail = Mail(app)
ts = URLSafeTimedSerializer(app.config["SECRET_KEY"])


# ------------------ Auth/Role Decorators ------------------
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "username" not in session:
            flash("You need to log in to manage users.", "error")
            return redirect(url_for("login"))
        conn = get_db_connection()
        user = conn.execute(
            "SELECT role FROM users WHERE username = ?", (session["username"],)
        ).fetchone()
        conn.close()
        if not user or user["role"] != "admin":
            abort(403)
        return f(*args, **kwargs)

    return decorated_function


# ------------------ Forgot / Reset Password ------------------
@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = (request.form.get("email") or "").strip().lower()
        if not email:
            flash("Please enter your email address.", "error")
            return redirect(url_for("forgot_password"))

        # Look up the user by email
        conn = get_db_connection()
        user = conn.execute(
            "SELECT id, username, email FROM users WHERE LOWER(email) = ?",
            (email,),
        ).fetchone()
        conn.close()

        # Always behave the same (avoid account enumeration)
        if user:
            token = ts.dumps(email, salt="pwd-reset")
            reset_url = url_for("reset_password", token=token, _external=True)

            try:
                msg = Message(
                    subject="Reset your password",
                    recipients=[email],
                    body=(
                        f"Hi {user['username']},\n\n"
                        "We received a request to reset your password.\n\n"
                        "Click the link below to choose a new password (valid for 1 hour):\n"
                        f"{reset_url}\n\n"
                        "If you didn't request this, you can ignore this email."
                    ),
                )
                mail.send(msg)
            except Exception as e:
                # Fallback for local/dev: log the link so you can test without SMTP
                app.logger.warning("Reset email failed to send: %s", e)
                app.logger.info("Password reset link (dev): %s", reset_url)

        flash("If an account with that email exists, a reset link has been sent.", "success")
        return redirect(url_for("login"))

    return render_template("forgot_password.html")


@app.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    # Verify token (1 hour expiry)
    try:
        email = ts.loads(token, salt="pwd-reset", max_age=3600)
    except SignatureExpired:
        flash("Reset link has expired. Please request a new one.", "error")
        return redirect(url_for("forgot_password"))
    except BadSignature:
        flash("Invalid reset link.", "error")
        return redirect(url_for("forgot_password"))

    if request.method == "POST":
        pwd = (request.form.get("password") or "")
        confirm = (request.form.get("confirm_password") or "")
        if len(pwd) < 8:
            flash("Password must be at least 8 characters.", "error")
            return redirect(request.url)
        if pwd != confirm:
            flash("Passwords do not match.", "error")
            return redirect(request.url)

        # Update password
        conn = get_db_connection()
        conn.execute(
            "UPDATE users SET password = ? WHERE LOWER(email) = ?",
            (generate_password_hash(pwd), email.lower()),
        )
        conn.commit()
        conn.close()

        flash("Your password has been reset. You can now log in.", "success")
        return redirect(url_for("login"))

    return render_template("reset_password.html", token=token)


# ------------------ Admin: Manage Users ------------------
@app.route("/admin_users")
@admin_required
def admin_users():
    conn = get_db_connection()
    role_filter = request.args.get("role")
    if role_filter:
        users = conn.execute(
            "SELECT * FROM users WHERE role = ?", (role_filter,)
        ).fetchall()
    else:
        users = conn.execute("SELECT * FROM users").fetchall()
    conn.close()
    return render_template("admin_users.html", users=users, role=role_filter)


@app.route("/admin/users/edit/<int:user_id>", methods=["GET", "POST"])
@admin_required
def edit_user(user_id):
    conn = get_db_connection()
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        role = request.form["role"]

        conn.execute(
            "UPDATE users SET username = ?, email = ?, role = ? WHERE id = ?",
            (username, email, role, user_id),
        )
        conn.commit()
        conn.close()

        flash("User updated successfully!", "success")
        return redirect(url_for("admin_users"))

    user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    return render_template("edit_user.html", user=user)


@app.route("/admin/users/delete/<int:user_id>", methods=["POST"])
@admin_required
def delete_user(user_id):
    try:
        conn = get_db_connection()
        conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()
        conn.close()
        flash("User deleted successfully!", "success")
    except Exception as e:
        flash(f"An error occurred: {str(e)}", "error")
    return redirect(url_for("admin_users"))
