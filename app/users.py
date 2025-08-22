# app/users.py (or wherever this module lives)

from functools import wraps

from flask import (
    render_template, request, redirect, url_for, session, flash, abort
)

from flask_mail import Message

from app import app, bcrypt, mail, ts
from app.db import get_db_connection
from itsdangerous import BadSignature, SignatureExpired


# ------------------ Auth/Role Decorator ------------------
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "username" not in session:
            flash("You need to log in to manage users.", "error")
            return redirect(url_for("login"))
        conn = get_db_connection()
        user = conn.execute(
            "SELECT role FROM users WHERE username = ?",
            (session["username"],),
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
                # Dev fallback: log the link so you can test without SMTP working
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
        pwd = (request.form.get("password") or "").strip()
        confirm = (
            request.form.get("confirm_password")
            or request.form.get("confirmPassword")  # tolerate camelCase from older templates
            or ""
        )
        confirm = confirm.strip()

        # (Optional) debug without leaking secrets
        app.logger.debug("Reset form keys: %s", list(request.form.keys()))
        app.logger.debug("Lengths: pwd=%d confirm=%d", len(pwd), len(confirm))

        if len(pwd) < 8:
            flash("Password must be at least 8 characters.", "error")
            return redirect(request.url)

        if pwd != confirm:
            flash("Passwords do not match.", "error")
            return redirect(request.url)

        # Store a bcrypt hash (consistent with login)
        hashed = bcrypt.generate_password_hash(pwd).decode("utf-8")

        conn = get_db_connection()
        conn.execute(
            "UPDATE users SET password = ? WHERE LOWER(email) = ?",
            (hashed, email.lower()),
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
            "SELECT * FROM users WHERE role = ?",
            (role_filter,),
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
