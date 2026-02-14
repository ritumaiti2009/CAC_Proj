import os
import sqlite3

from flask import Flask, redirect, render_template, request, session
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

from helpers import error, login_required, admin_required

# Configure application
app = Flask(__name__)
app.secret_key = "fbla_lost_and_found".encode(
    "utf8"
)  # Required for flask session security

# Const for database name
DATABASE = "database.db"

# Handles image collection
UPLOAD_PATH = "static/uploads"
app.config["UPLOAD_PATH"] = UPLOAD_PATH
os.makedirs(UPLOAD_PATH, exist_ok=True)

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}


"""Handles Image Files"""


# Check if file is accepted by checking if file type matches the accepted ones
def check_allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# Get unique filename for image upload
def get_unique_filepath(filename):

    # Seperate name from extension
    base, ext = os.path.splitext(filename)

    counter = 1
    unique_name = filename
    while os.path.exists(os.path.join(app.config["UPLOAD_PATH"], unique_name)):
        unique_name = f"{base}_{counter}{ext}"
        counter += 1
    return os.path.join(app.config["UPLOAD_PATH"], unique_name)


# Save image to UPLOAD_PATH
def save_iamge(image):
    filepath = None
    if image and image.filename != "":
        if check_allowed_file(image.filename):
            filename = secure_filename(image.filename)
            filepath = get_unique_filepath(filename)
            image.save(filepath)
            return filepath
        else:
            return error("Error uploading image: Invalid file type", 415)


"""Handles Database"""


# Set up database
def init_db():
    # Connects to the database and make a cursor to interact with it
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()

    # Create databases

    c.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              email TEXT UNIQUE NOT NULL,
              password TEXT NOT NULL,
              first_name TEXT NOT NULL,
              last_name TEXT NOT NULL,
              preferred_name TEXT DEFAULT NULL,
              phone_num TEXT DEFAULT NULL,
              status TEXT NOT NULL DEFAULT 'student'
        )
    """
    )

    c.execute(
        """
        CREATE TABLE IF NOT EXISTS items (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              user_id INTEGER REFERENCES users(id) DEFAULT NULL,
              email TEXT NOT NULL,
              name TEXT NOT NULL,
              title TEXT NOT NULL,
              description TEXT,
              image_path TEXT,
              date_reported DATETIME DEFAULT CURRENT_TIMESTAMP,
              status TEXT NOT NULL DEFAULT 'lost',
              approved BOOLEAN NOT NULL DEFAULT false
        )
    """
    )

    c.execute(
        """
        CREATE TABLE IF NOT EXISTS requests (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              user_id INTEGER REFERENCES users(id),
              item_id INTERGER REFERENCES items(id),
              message TEXT NOT NULL,
              image_path TEXT,
              status TEXT NOT NULL DEFAULT 'pending',
              date_requested DATETIME DEFAULT CURRENT_TIMESTAMP,
              UNIQUE (user_id, item_id)
        )
    """
    )


    conn.commit()
    conn.close()


# Receive items post from database
def select_items(status):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()

    try:
        c.execute("SELECT * FROM items WHERE status = ? AND approved = true", (status))
        items = c.fetchall()
        conn.close()
        return items
    except:
        return error("Failed to fetch items", 500)


"""App routes"""


# Set up default indexpage
@app.route("/")
def index():
    # Check for session
    if "user" in session:
        return render_template("index.html", user=session.get("user"))
    else:
        return render_template("index.html", user="guest")


# Set up registration function
@app.route("/register", methods=["GET", "POST"])
def register():
    # Attempt to register new account when a POST received
    if request.method == "POST":
        # Get required attributes
        email = request.form["email"]
        password = generate_password_hash(
            request.form["password"], method="pbkdf2:sha256"
        )  # Set hashing style to avoid scrypt
        first_name = request.form["first_name"]
        last_name = request.form["last_name"]

        # Get optional attribute and check if it is empty
        preferred_name = request.form["preferred_name"].strip() or None
        phone_num = request.form["phone_num"].strip() or None

        # Upload to database
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()

        try:
            c.execute(
                """
                INSERT INTO users (email, password, first_name, last_name, preferred_name, phone_num) 
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (email, password, first_name, last_name, preferred_name, phone_num),
            )
            conn.commit()
            conn.close()
            return redirect("/login")
        except:
            return error("Unable to register: Email already exists", 409)

    # Return html layout when GET method received
    return render_template("register.html")


# Set up logging in function
@app.route("/login", methods=["GET", "POST"])
def login():
    # Attempt to log user in when POST method received
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        try:
            conn = sqlite3.connect(DATABASE)
            c = conn.cursor()
            c.execute("SELECT * FROM users WHERE email = ?", (email,))
            user = c.fetchone()
            conn.close()
        except:
            return error("Unable to login: Failed to fetch login information", 401)

        # Authenticate password
        if user and check_password_hash(user[2], password):
            session["user_id"] = user[0]
            session["user"] = email
            session["name"] = f"{user[3]} {user[4]}"
            session["status"] = user[7]
            return redirect("/")
        else:
            return error("Unable to login: Incorrect email or password", 401)

    # Return html layout when GET method received
    return render_template("login.html")


# Set up logging out function
@app.route("/logout")
@login_required
def logout():
    # Remove user from session and return None
    session.pop("user", None)
    return redirect("/login")


# Get item submissions
@app.route("/submit", methods=["POST"])
def submit():
    # Check for session
    if "user" in session:
        # Get user info from session
        user_id = session.get("user_id")
        email = session.get("user")
        name = session.get("name")

    else:
        # Get user info from form
        user_id = None
        email = request.form["email"]
        name = request.form["name"]

    # Get submission from form
    status = request.form["type"]
    title = request.form["title"]
    description = request.form["description"] or None
    image = request.files.get("image")

    # Save image and get path
    filepath = save_iamge(image)

    # Upload to database
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()

    try:
        c.execute(
            """
            INSERT INTO items (user_id, email, name, title, description, image_path, status) 
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (user_id, email, name, title, description, filepath, status),
        )
        conn.commit()
        conn.close()
        return redirect("/")
    except:
        return error("Unable to upload: Check inputs", 400)


# Handles displaying lost items
@app.route("/lost", methods=["GET", "POST"])
def lost():
    # Search up specific posts
    if request.method == "POST":
        # Get keyword for querying
        keyword = request.form["keyword"]

        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()

        try:
            c.execute(
                """
                      SELECT id, title, description, image_path, date_reported FROM items 
                      WHERE status = 'lost' AND approved = true 
                      AND (title LIKE ? OR description LIKE ?)
                      """,
                (f"%{keyword}%", f"%{keyword}%"),
            )
            items_list = c.fetchall()
            conn.close()
        except:
            return error("Failed to fetch items", 500)
    else:
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()

        try:
            c.execute("""
                      SELECT id, title, description, image_path, date_reported FROM items 
                      WHERE status = 'lost' AND approved = true
                      """)
            items_list = c.fetchall()
            conn.close()
        except:
            return error("Failed to fetch items", 500)

    return render_template("lost.html", items=items_list)


# Handles displaying found items
@app.route("/found", methods=["GET", "POST"])
def found():
    # Search up specific posts
    if request.method == "POST":
        # Get keyword for querying
        keyword = request.form["keyword"]

        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()

        try:
            c.execute(
                """
                      SELECT id, title, description, image_path, date_reported FROM items 
                      WHERE status = 'found' AND approved = true 
                      AND (title LIKE ? OR description LIKE ?)
                      """,
                (f"%{keyword}%", f"%{keyword}%"),
            )
            items_list = c.fetchall()
            conn.close()
        except:
            return error("Failed to fetch items", 500)
    else:
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()

        try:
            c.execute(
                """
                      SELECT id, title, description, image_path, date_reported FROM items 
                      WHERE status = 'found' AND approved = true
                      """
            )
            items_list = c.fetchall()
            conn.close()
        except:
            return error("Failed to fetch items", 500)

    return render_template("found.html", items=items_list)


# Allows user to file for information
@app.route("/request/<int:id>", methods=["GET", "POST"])
@login_required
def request_item(id):
    # Sends request
    if request.method == "POST":
        # Get user info from session
        user_id = session.get("user_id")

        # Get submission from form
        message = request.form["message"]
        image = request.files.get("image")

        # Save image and get path
        filepath = save_iamge(image)

        # Upload to database
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()

        try:
            c.execute(
                """
                INSERT INTO requests (user_id, item_id, message,  image_path) 
                VALUES (?, ?, ?, ?)
                """,
                (user_id, id, message, filepath),
            )
            conn.commit()
            conn.close()
            return redirect("/")
        except:
            return error("Unable to upload: Check inputs", 400)
    # Request form
    return render_template("request.html", item_id=id)


# Handles management of posts for admin
@app.route("/manage", methods=["GET", "POST"])
@login_required
@admin_required
def manage():
    # Allow searching
    if request.method == "POST":
        # Get keyword for querying
        keyword = request.form["keyword"]

        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()

        try:
            c.execute(
                """
                      SELECT * FROM items 
                      WHERE title LIKE ? OR description LIKE ?
                      """,
                (f"%{keyword}%", f"%{keyword}%"),
            )
            items_list = c.fetchall()
            conn.close()
        except:
            return error("Failed to fetch items", 500)
    else:
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()

        try:
            c.execute("SELECT * FROM items")
            items_list = c.fetchall()
            conn.close()
        except:
            return error("Failed to fetch items", 500)

    return render_template("manage.html", items=items_list)


# Delete submission
@app.route("/delete_item/<int:id>", methods=["POST"])
@login_required
@admin_required
def delete_item(id):
    try:
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()

        # Delete image if it exists
        c.execute("SELECT image_path FROM items WHERE id = ?", (id,))
        row = c.fetchone()
        if row:
            image_path = row[0]
            os.remove(image_path)

        # Delete entry
        c.execute("DELETE FROM items WHERE id = ?", (id,))
        conn.commit()
        conn.close()
    except:
        return error("Failed to delete", 500)
    return redirect("/")


# Approve submission
@app.route("/approve_item/<int:id>", methods=["POST"])
@login_required
@admin_required
def approve_item(id):
    try:
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute("UPDATE items SET approved = true WHERE id = ?", (id,))
        conn.commit()
        conn.close()
    except:
        return error("Failed to update", 500)
    return redirect("/")


"""Debugging"""


# Check if Flask is ran directly
if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=8000)
