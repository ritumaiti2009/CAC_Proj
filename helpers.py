from flask import redirect, render_template, session
from functools import wraps

# Display error and return code
def error(message, code):
    return render_template("error.html", num=code, m=message), code

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
        if session.get("status") != "admin":
            return redirect("/login")
        return f(*args, **kwargs)

    return decorated_function