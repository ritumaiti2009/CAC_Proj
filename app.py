import os
import sqlite3

from flask import Flask, flash, redirect, render_template, request, session  
from flask_session import Session   
from datetime import timedelta
from werkzeug.security import check_password_hash, generate_password_hash

# Configure application
app = Flask(__name__)
app.secret_key = "fbla_lost_and_found".encode('utf8') # Required for flask session security

# Const for database name
DATABASE = "database.db"

# Set up database
def init_db():
    # Connects to the database and make a cursor to interact with it
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()

    # Create databases

    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              email TEXT UNIQUE NOT NULL,
              password TEXT NOT NULL,
              first_name TEXT NOT NULL,
              last_name TEXT NOT NULL,
              preferred_name TEXT,
              phone_num TEXT,
              status TEXT NOT NULL DEFAULT 'student'
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS items (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              user_id INTEGER NOT NULL REFERENCES users(id),
              title TEXT NOT NULL,
              description TEXT,
              image_path TEXT,
              date_reported DATETIME DEFAULT CURRENT_TIMESTAMP,
              status TEXT NOT NULL DEFAULT 'lost'
        )
    ''')

    conn.commit()
    conn.close()

# Set up default homepage 
@app.route("/") 
def home():
    # Check for session
    if "user" in session:
        return f"""
        <h2>Welcome {session['user']}!</h2>
        <a href='/logout'>Logout</a>
        """
    return redirect("/login")

# Set up registration function
@app.route("/register", methods=["GET", "POST"])
def register():
    # Attempt to register new account when a POST received
    if(request.method == "POST"):
        email = request.form["email"]
        password = generate_password_hash(request.form["password"])
        first_name = request.form["first_name"]
        last_name = request.form["last_name"]

        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()

        try:
            c.execute("INSERT INTO users (email, password, first_name, last_name)", (email, password, first_name, last_name))
            conn.commit()
            conn.close()
            return redirect(".login")
        except:
            return "Unable to log in: Email already exists"
    
    # Return html layout when GET method received
    return """
    <h2>Register<h2>
    <form method="post">
        First Name: <input type="text" name="first_name"><br><br>
        Last Name: <input type="text" name="last_name"><br><br>
        Email: <input type="email" name="email"><br><br>
        Password: <input type="password" name="password"><br><br>
        <button type="submit">Register</button>
    </form>
    <a href='/login'>Login</a>
    """

# Set up logging in function
@app.route("/login", methods=["GET", "POST"])
def login():
    # Attempt to log user in when POST method received
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE email = ?", (email,)) 
        user = c.fetchone()
        conn.close()

        # Authenticate password
        if user and check_password_hash(user[2], password):
            session["user"] = email
            return redirect("/")
        else:
            return "Unable to login: Incorrect email or password"

    # Return html layout when GET method received
    return """
    <h2>Login<h2>
    <form method="post">
        Email: <input type="email" name="email"><br><br>
        Password: <input type="password" name="password"><br><br>
        <button type="submit">Login</button>
    </form>
    <a href='/register'>Login</a>
    """

# Set up logging out function
@app.route("/logout")
def logout():
    # Remove user from session and return None
    session.pop("user", None)
    return redirect("/login")

# Debugging
if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=8000)