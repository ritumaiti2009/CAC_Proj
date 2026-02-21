from flask import Flask, redirect, render_template, request, session
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import error, login_required, admin_required
from image_handler import save_image, del_image
from db_handler import run_sql, init_db

# Configure application
app = Flask(__name__)
app.secret_key = "fbla_lost_and_found".encode(
    "utf8"
)  # Required for flask session security


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
        try:
            run_sql(
                """
                INSERT INTO users (email, password, first_name, last_name, preferred_name, phone_num) 
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (email, password, first_name, last_name, preferred_name, phone_num),
            )
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
            user = run_sql("SELECT * FROM users WHERE email = ?", (email,))
        except:
            return error("Unable to login: Failed to fetch login information", 401)

        # Authenticate password
        if user and check_password_hash(user[0][2], password):
            session["user_id"] = user[0][0]
            session["user"] = email
            if user[0][5]:
                session["name"] = f"{user[0][5]} {user[0][4]}"
            else:
                session["name"] = f"{user[0][3]} {user[0][4]}"
            session["status"] = user[0][7]
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
    filepath = save_image(image)

    # Upload to database
    try:
        run_sql(
            """
            INSERT INTO items (user_id, email, name, title, description, image_path, status) 
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (user_id, email, name, title, description, filepath, status),
        )
        return redirect("/")
    except:
        return error("Unable to upload: Check inputs", 400)


# Handles displaying lost items
@app.route("/lost", methods=["GET", "POST"])
def lost():
    # Default query
    query = """
            SELECT 
            items.id AS id, 
            items.title AS title, 
            items.description AS description, 
            items.image_path AS image_path, 
            datetime(items.date_reported, 'localtime') AS date_reported,
            requests.user_id AS user_id 
            FROM items 
            LEFT JOIN requests
            ON items.id = requests.item_id
            WHERE items.status = 'lost' AND items.approved = true
            """

    # Search up specific posts
    if request.method == "POST":
        # Get keyword for querying
        keyword = request.form["keyword"]

        try:
            items_list = run_sql(
                f"""
                    {query}
                      AND (items.title LIKE ? OR items.description LIKE ?)
                      ORDER BY items.date_reported DESC
                      """,
                (f"%{keyword}%", f"%{keyword}%"),
            )
        except:
            return error("Failed to fetch items", 500)
    else:
        try:
            items_list = run_sql(f"{query} ORDER BY items.date_reported DESC")
        except:
            return error("Failed to fetch items", 500)

    return render_template("lost.html", items=items_list)


# Handles displaying found items
@app.route("/found", methods=["GET", "POST"])
def found():
    # Default query
    query = """
                SELECT 
                items.id AS id, 
                items.title AS title, 
                items.description AS description, 
                items.image_path AS image_path, 
                datetime(items.date_reported, 'localtime') AS date_reported,
                requests.user_id AS user_id 
                FROM items 
                LEFT JOIN requests
                ON items.id = requests.item_id
                WHERE items.status = 'found' AND items.approved = true
                """

    # Search up specific posts
    if request.method == "POST":
        # Get keyword for querying
        keyword = request.form["keyword"]

        try:
            items_list = run_sql(
                f"""
                      {query}
                      AND (items.title LIKE ? OR items.description LIKE ?)
                      ORDER BY items.date_reported DESC
                      """,
                (f"%{keyword}%", f"%{keyword}%"),
            )
        except:
            return error("Failed to fetch items", 500)
    else:
        try:
            items_list = run_sql(f"{query} ORDER BY items.date_reported DESC")
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
        filepath = save_image(image)

        # Upload to database
        try:
            run_sql(
                """
                INSERT INTO requests (user_id, item_id, message, image_path) 
                VALUES (?, ?, ?, ?)
                """,
                (user_id, id, message, filepath),
            )
            return redirect("/")
        except:
            return error("Unable to upload: Check inputs", 400)
    # Request form
    return render_template("request.html", item_id=id)


# Lists requests for user
@app.route("/requests", methods=["GET", "POST"])
@login_required
def requests():
    # Queries variables
    header_query = """
                SELECT 
                items.title AS title,
                items.status AS item_status,
                requests.message AS message,
                datetime(requests.date_requested, 'localtime') AS date_requested,
                requests.image_path AS image_path,
                requests.status AS request_status
                """

    header_extra_query = """
                items.email AS email,
                items.name AS name
                """

    tail_approved_query = """
                FROM requests
                INNER JOIN items ON requests.item_id = items.id
                WHERE requests.status = 'approved' AND requests.user_id = ?
                """

    tail_unapproved_query = """
                FROM requests
                INNER JOIN items ON requests.item_id = items.id
                WHERE requests.status != 'approved' AND requests.user_id = ?
                """

    tail_search_query = """
                AND (requests.message LIKE ? OR 
                items.title LIKE ? OR items.description LIKE ?)
                """
    
    date_order_query = "ORDER BY requests.date_requested DESC"

    # Search up specific posts
    if request.method == "POST":
        # Get keyword for querying
        keyword = request.form["keyword"]

        try:
            # Get all approved requests with contact info
            requests_list = run_sql(
                f"""
                      {header_query},
                      {header_extra_query}
                      {tail_approved_query}
                      {tail_search_query}
                      {date_order_query}
                      """,
                (
                    session.get("user_id"),
                    f"%{keyword}%",
                    f"%{keyword}%",
                    f"%{keyword}%",
                ),
            )

            # Get all non-approved requests with contact info
            requests_list.extend(
                run_sql(
                    f"""
                        {header_query}
                        {tail_unapproved_query}
                        {tail_search_query}
                        {date_order_query}
                        """,
                    (
                        session.get("user_id"),
                        f"%{keyword}%",
                        f"%{keyword}%",
                        f"%{keyword}%",
                    ),
                )
            )
        except:
            return error("Failed to fetch requests", 500)
    else:
        try:
            # Get all approved requests with contact info
            requests_list = run_sql(
                f"""
                      {header_query},
                      {header_extra_query}
                      {tail_approved_query}
                      {date_order_query}
                      """,
                (session.get("user_id"),),
            )

            # Get all non-approved requests with contact info
            requests_list.extend(
                run_sql(
                    f"""
                        {header_query}
                        {tail_unapproved_query}
                        {date_order_query}
                        """,
                    (session.get("user_id"),),
                )
            )
        except:
            return error("Failed to fetch requests", 500)

    return render_template("requests.html", requests=requests_list)


# Handles management of posts for admin
@app.route("/manage_items", methods=["GET", "POST"])
@login_required
@admin_required
def manage_items():
    # Default query
    query = """
                SELECT *, 
                datetime(date_reported, 'localtime') AS localdate
                FROM items
                """

    # Allow searching
    if request.method == "POST":
        # Get keyword for querying
        keyword = request.form["keyword"]

        try:
            items_list = run_sql(
                f"""
                      {query}
                      FROM items WHERE title LIKE ? OR description LIKE ?
                      ORDER BY items.date_reported DESC
                      """,
                (f"%{keyword}%", f"%{keyword}%"),
            )
        except:
            return error("Failed to fetch items", 500)
    else:
        try:
            items_list = run_sql(f"{query} ORDER BY items.date_reported DESC")
        except:
            return error("Failed to fetch items", 500)

    return render_template("manage_item.html", items=items_list)


# Approve submission
@app.route("/approve_item/<int:id>", methods=["POST"])
@login_required
@admin_required
def approve_item(id):
    try:
        run_sql("UPDATE items SET approved = true WHERE id = ?", (id,))
    except:
        return error("Failed to update", 500)
    return redirect("/")


# Delete submission
@app.route("/delete_item/<int:id>", methods=["POST"])
@login_required
@admin_required
def delete_item(id):
    try:
        # Delete image if it exists
        row = run_sql("SELECT image_path FROM items WHERE id = ?", (id,))
        if row:
            del_image(row[0][0])

        # Delete entry
        run_sql("DELETE FROM items WHERE id = ?", (id,))
    except:
        return error("Failed to delete", 500)
    return redirect("/")


# Handles management of requests for admin
@app.route("/manage_requests", methods=["GET", "POST"])
@login_required
@admin_required
def manage_requests():
    # Default query
    query = """
                    SELECT 
                    requests.id as id,
                    items.title AS title,
                    items.status AS item_status,
                    items.email AS poster_email,
                    items.name AS poster_name,
                    users.email AS user_email,
                    COALESCE(users.preferred_name, 
                    CONCAT(users.first_name, ' ', users.last_name)) 
                    AS user_name,
                    requests.message AS message,
                    datetime(requests.date_requested, 'localtime') AS date_requested,
                    requests.image_path AS image_path,
                    requests.status AS request_status
                    FROM requests
                    INNER JOIN items ON requests.item_id = items.id
                    INNER JOIN users ON requests.user_id = users.id
                    """
    # Allow searching
    if request.method == "POST":
        # Get keyword for querying
        keyword = request.form["keyword"]

        try:
            request_list = run_sql(
                f"""
                    {query}
                    WHERE requests.message LIKE ? OR 
                    items.title LIKE ? OR items.description LIKE ?
                    ORDER BY requests.date_requested DESC
                    """,
                (f"%{keyword}%", f"%{keyword}%", f"%{keyword}%"),
            )
        except:
            return error("Failed to fetch requests", 500)
    else:
        try:
            request_list = run_sql(f"{query} ORDER BY requests.date_requested DESC")
        except:
            return error("Failed to fetch requests", 500)

    return render_template("manage_request.html", requests=request_list)


# Approve request
@app.route("/approve_request/<int:id>", methods=["POST"])
@login_required
@admin_required
def approve_request(id):
    try:
        run_sql("UPDATE requests SET status = 'approved' WHERE id = ?", (id,))
    except:
        return error("Failed to update", 500)
    return redirect("/")


# Reject request
@app.route("/reject_request/<int:id>", methods=["POST"])
@login_required
@admin_required
def reject_request(id):
    try:
        run_sql("UPDATE requests SET status = 'rejected' WHERE id = ?", (id,))
    except:
        return error("Failed to update", 500)
    return redirect("/")


"""Debugging"""


# Check if Flask is ran directly
if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=8000)
