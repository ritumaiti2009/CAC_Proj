from flask import flash, redirect, session
from functools import wraps


# Display alert for success and error statement
def alert(message, redirect_url, code=None):
    if code is None:
        flash(message, "success")
    else:
        flash(f"{message} ({code})", "error")
    return redirect(redirect_url)


# Decorate route to require login
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user") is None:
            return redirect("/login")
        return f(*args, **kwargs)

    return decorated_function


# Decorate route to only allow admin
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("role") != "admin":
            return redirect("/login")
        return f(*args, **kwargs)

    return decorated_function
