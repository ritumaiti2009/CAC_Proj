import os

from flask import Flask, redirect, render_template, request, session
from dotenv import load_dotenv
from werkzeug.security import check_password_hash, generate_password_hash

from db_handler import run_sql, init_db
from email_handler import send_email
from helpers import alert, login_required, admin_required
from image_handler import save_image, del_image

# Configure application
app = Flask(__name__)
app.secret_key = "fbla_lost_and_found".encode(
    "utf8"
)  # Required for flask session security


# Load .env for secured username and password of mail
load_dotenv()


# Set up config for email
app.config.update(
    MAIL_SERVER="smtp.gmail.com",
    MAIL_PORT=587,
    MAIL_USE_TLS=True,
    MAIL_USERNAME=os.getenv("MAIL_USERNAME"),
    MAIL_PASSWORD=os.getenv("MAIL_PASSWORD"),
    MAIL_DEFAULT_SENDER=os.getenv("MAIL_USERNAME"),
)


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
        # Check if user entered correct password confirmation
        if request.form["password"] != request.form["password_confirm"]:
            return alert(
                "Unable to register: Incorrect Password Confirmation", "/register", 409
            )

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
            send_email(
                app,
                "Your Email has been used to Register in VRP",
                """
                Dear user

                Your email has recently been used to register an account with Viking Recovery Portal.
                If this wasn't you, please contact us!

                Best Wishes,
                Kevin from VRP
                """,
                f"{email}",
            )
            return alert("Successfully registed!", "/login")
        except:
            return alert("Unable to register: Email already exists", "/register", 409)

    # Return user to homepage if they are logged in
    if "user" in session:
        return redirect("/")
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
            return alert(
                "Unable to login: Failed to fetch login information", "/login", 500
            )

        # Authenticate password
        if user and check_password_hash(user[0][2], password):
            session["user_id"] = user[0][0]
            session["user"] = email
            if user[0][5]:
                session["name"] = f"{user[0][5]} {user[0][4]}"
            else:
                session["name"] = f"{user[0][3]} {user[0][4]}"
            session["role"] = user[0][7]
            return alert("Successfully logged in!", "/")
        else:
            return alert("Unable to login: Incorrect email or password", "/login", 401)

    # Return html layout when GET method received
    if "user" in session:
        return redirect("/")
    return render_template("login.html")


# Set up logging out function
@app.route("/logout")
@login_required
def logout():
    # Remove user from session and return None
    session.pop("user", None)
    return alert("Successfully logged out!", "/login")


# Set up account setting page
@app.route("/setting", methods=["GET", "POST"])
@login_required
def setting():
    if request.method == "POST":
        # Get account password from db
        try:
            account_password = run_sql(
                "SELECT password FROM users WHERE email = ?", (session.get("user"),)
            )
        except:
            return alert(
                "Failed to Update Account: Failed to fetch login information",
                "/setting",
                500,
            )

        # Authenticate password
        password = request.form["password"]
        if not account_password or not check_password_hash(
            account_password[0][0], password
        ):
            return alert(
                "Failed to Update Account: Incorrect Password", "/setting", 401
            )

        try:
            # Get required attributes
            email = request.form["email"]
            first_name = request.form["first_name"]
            last_name = request.form["last_name"]
            preferred_name = request.form["preferred_name"].strip() or None
            phone_num = request.form["phone_num"].strip() or None

            # Update sql
            run_sql(
                """
                UPDATE users
                SET first_name = ?,
                last_name = ?,
                email = ?,
                preferred_name = ?,
                phone_num = ?
                WHERE id = ?
                """,
                (
                    first_name,
                    last_name,
                    email,
                    preferred_name,
                    phone_num,
                    session.get("user_id"),
                ),
            )

            # Update session info
            session["user"] = email
            if preferred_name:
                session["name"] = f"{preferred_name} {last_name}"
            else:
                session["name"] = f"{first_name} {last_name}"

            return alert("Successfully updated account informations!", "/")
        except Exception as e:
            return alert(f"Failed to Update Account {e}", "/setting", 500)
    else:
        user_info = run_sql(
            """
            SELECT
            first_name,
            last_name,
            email,
            preferred_name,
            phone_num
            FROM users WHERE id = ?
            """,
            (session.get("user_id"),),
        )
        return render_template("settings.html", user=user_info)


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
        return alert("Report successfully submitted! (Must wait for approval)", "/")
    except:
        return alert("Unable to upload: Check inputs", "/", 400)


# Handles displaying items
@app.route("/items", methods=["GET", "POST"])
def items():
    # Default query
    query = """
            SELECT 
            items.id AS id, 
            items.title AS title, 
            items.description AS description, 
            items.image_path AS image_path, 
            datetime(items.date_reported, 'localtime') AS date_reported,
            items.user_id AS poster_user_id,
            items.status AS status,
            items.approved AS approved,
            requests.user_id AS requester_user_id 
            FROM items 
            LEFT JOIN requests
            ON items.id = requests.item_id
            """

    order_query = "ORDER BY items.date_reported DESC LIMIT ?"

    params = []

    # Check if is checking user's specific items
    user_specific = request.args.get("user_specific", type=int) or 0
    if user_specific == 1:
        query += " WHERE items.user_id = ?"
        params.append(session.get("user_id"))
    else:
        query += " WHERE items.approved = true"

    # Get limit per pages
    limit = request.args.get("limit", 12, type=int)
    params.append(limit)

    # Search up specific posts
    if request.method == "POST":
        # Get keyword for querying
        keyword = request.form["keyword"]
        status = request.form.get("status") or "o"

        try:
            # Add search request to params
            for i in range(2):
                params.append(f"%{keyword}%")
            params.append(f"%{status}%")

            items_list = run_sql(
                f"""
                    {query}
                      AND (items.title LIKE ? OR items.description LIKE ?) AND items.status LIKE ?
                      {order_query}
                      """,
                (params),
            )
        except:
            return alert("Failed to fetch items", "/", 500)
    else:
        try:
            if request.args.get("user_specific") == "true":
                items_list = run_sql(
                    f"{query} {order_query}", (params)
                )
            else:
                items_list = run_sql(f"{query} {order_query}", (params))
        except Exception as e:
            return alert(f"Failed to fetch items {e}", "/", 500)

    return render_template("items.html", items=items_list, user_specific=user_specific)


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
        image = request.files.get("image") or None

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

            # Send confirmation email for original poster
            op = run_sql("SELECT title, email FROM items WHERE id = ?", (id,))
            requester = run_sql(
                """
                SELECT 
                COALESCE(users.preferred_name, 
                CONCAT(users.first_name, ' ', users.last_name)),
                email
                FROM users WHERE id = ?
                """,
                (user_id,),
            )

            send_email(
                app,
                "Confirm Request",
                f"""
                Dear user,

                Your post of id {id} titled "{op[0][0]}" had gotten a request from {requester[0][0]} at {requester[0][1]}.
                It comes with a message "{message}"
                To confirm please go to "Request For You" on the Viking Recovery Portal Page.

                Best Wishes,
                Kevin from VRP
                """,
                (op[0][1]),
            )

            return alert(
                "Request successfully submitted! (Must wait for approval)", "/"
            )
        except:
            return alert("Unable to upload: Check inputs", "/", 400)
    # Request form
    return render_template("request.html", item_id=id)


# Lists sent requests of a user
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
                users.email AS email,
                items.name AS name,
                users.phone_num AS phone_num
                """

    tail_query = "FROM requests INNER JOIN items ON requests.item_id = items.id INNER JOIN users ON requests.user_id = users.id"

    tail_approved_query = f"""
                {tail_query}
                WHERE requests.status = 'approved' AND requests.user_id = ?
                """

    tail_unapproved_query = f"""
                {tail_query}
                WHERE requests.status != 'approved' AND requests.user_id = ?
                """

    tail_search_query = """
                AND (requests.message LIKE ? OR 
                items.title LIKE ? OR items.description LIKE ?) AND items.status LIKE ?
                """

    order_query = "ORDER BY requests.date_requested DESC LIMIT ?"

    # Get limit per pages
    limit = request.args.get("limit", 12, type=int)

    # Search up specific posts
    if request.method == "POST":
        # Get keyword for querying
        keyword = request.form["keyword"]
        status = request.form.get("status") or "o"

        try:
            # Get all approved requests with contact info
            requests_list = run_sql(
                f"""
                      {header_query},
                      {header_extra_query}
                      {tail_approved_query}
                      {tail_search_query}
                      {order_query}
                      """,
                (
                    session.get("user_id"),
                    f"%{keyword}%",
                    f"%{keyword}%",
                    f"%{keyword}%",
                    f"%{status}%",
                    limit
                ),
            )

            # Get all non-approved requests with contact info
            requests_list.extend(
                run_sql(
                    f"""
                        {header_query}
                        {tail_unapproved_query}
                        {tail_search_query}
                        {order_query}
                        """,
                    (
                        session.get("user_id"),
                        f"%{keyword}%",
                        f"%{keyword}%",
                        f"%{keyword}%",
                        f"%{status}%",
                        limit
                    ),
                )
            )
        except:
            return alert("Failed to fetch requests", "/", 500)
    else:
        try:
            # Get all approved requests with contact info
            requests_list = run_sql(
                f"""
                      {header_query},
                      {header_extra_query}
                      {tail_approved_query}
                      {order_query}
                      """,
                (session.get("user_id"), limit),
            )

            # Get all non-approved requests with contact info
            requests_list.extend(
                run_sql(
                    f"""
                        {header_query}
                        {tail_unapproved_query}
                        {order_query}
                        """,
                    (session.get("user_id"), limit),
                )
            )
        except:
            return alert("Failed to fetch requests", "/", 500)

    return render_template("requests.html", requests=requests_list, for_user=False)


# Lists requests for user
@app.route("/requests_for", methods=["GET", "POST"])
@login_required
def requests_for():
    # Queries variables
    header_query = """
                SELECT 
                requests.id AS id,
                items.title AS title,
                items.status AS item_status,
                requests.message AS message,
                datetime(requests.date_requested, 'localtime') AS date_requested,
                requests.image_path AS image_path,
                requests.status AS request_status,
                users.email AS email,
                COALESCE(users.preferred_name, 
                CONCAT(users.first_name, ' ', users.last_name)) 
                AS name,
                users.phone_num AS phone_num
                """

    tail_query = """
                FROM requests
                INNER JOIN items ON requests.item_id = items.id
                INNER JOIN users ON requests.user_id = users.id
                WHERE items.user_id = ?
                """

    tail_search_query = """
                AND (requests.message LIKE ? OR 
                items.title LIKE ? OR items.description LIKE ?)
                AND items.status LIKE ?
                """

    date_order_query = "ORDER BY requests.date_requested DESC LIMIT ?"

    # Get limit per pages
    limit = request.args.get("limit", 12, type=int)

    # Search up specific posts
    if request.method == "POST":
        # Get keyword for querying
        keyword = request.form["keyword"]
        status = request.form.get("status") or "o"

        try:
            # Get all approved requests with contact info
            requests_list = run_sql(
                f"""
                      {header_query}
                      {tail_query}
                      {tail_search_query}
                      {date_order_query}
                      """,
                (
                    session.get("user_id"),
                    f"%{keyword}%",
                    f"%{keyword}%",
                    f"%{keyword}%",
                    f"%{status}%",
                    limit
                ),
            )
        except:
            return alert("Failed to fetch requests", "/", 500)
    else:
        try:
            # Get all approved requests with contact info
            requests_list = run_sql(
                f"""
                      {header_query}
                      {tail_query}
                      {date_order_query}
                      """,
                (session.get("user_id"), limit),
            )
        except:
            return alert("Failed to fetch requests", "/", 500)

    return render_template("requests.html", requests=requests_list, for_user=True)


# Handles management of posts for admin
@app.route("/manage_items", methods=["GET", "POST"])
@login_required
@admin_required
def manage_items():
    # Default query
    query = """
                SELECT *, 
                datetime(date_reported, 'localtime') AS date_reported
                FROM items
                """
    
    order_query = "ORDER BY items.date_reported DESC LIMIT ?"
    
    # Get limit per pages
    limit = request.args.get("limit", 12, type=int)

    # Allow searching
    if request.method == "POST":
        # Get keyword for querying
        keyword = request.form["keyword"]
        status = request.form.get("status") or "o"

        try:
            items_list = run_sql(
                f"""
                      {query}
                      WHERE (title LIKE ? OR description LIKE ?) AND status LIKE ?
                      {order_query}
                      """,
                (f"%{keyword}%", f"%{keyword}%", f"%{status}%", limit),
            )
        except Exception as e:
            return alert("Failed to fetch items", "/", 500)
    else:
        try:
            items_list = run_sql(f"{query} {order_query}", (limit,))
        except:
            return alert("Failed to fetch items", "/", 500)

    return render_template("manage_item.html", items=items_list)


# Approve submission only by Admin
@app.route("/approve_item/<int:id>", methods=["POST"])
@login_required
@admin_required
def approve_item(id):
    try:
        run_sql("UPDATE items SET approved = true WHERE id = ?", (id,))
    except:
        return alert("Failed to update", "/manage_items", 500)
    return alert("Successfully approved item!", "/manage_items")


# Delete submission only if by user or done by an Admin
@app.route("/delete_item/<int:id>", methods=["POST"])
@login_required
def delete_item(id):
    # Checking if user_id matches or they're an Admin
    user_id = run_sql("SELECT user_id FROM items WHERE id = ?", (id,))
    if session.get("role") == "admin" or user_id[0][0] == session.get("user_id"):
        try:
            # Delete image if it exists
            row = run_sql("SELECT image_path FROM items WHERE id = ?", (id,))
            if row[0][0]:
                del_image(row[0][0])

            # Delete entry
            run_sql("DELETE FROM items WHERE id = ?", (id,))
        except:
            if session.get("role") == "admin":
                return alert("Failed to delete", "/manage_items", 500)
            else:
                return alert("Failed to delete", "/", 500)
        if session.get("role") == "admin":
            return alert("Successfully deleted item!", "/manage_items")
        else:
            return alert("Successfully deleted item!", "/")
    return alert("Failed to delete: Unauthorized", "/", 401)


# Handles resolving items post
@app.route("/resolve_item/<int:id>", methods=["POST"])
@login_required
def resolve_item(id):
    # Checking if user_id matches or they're an Admin
    user_id = run_sql("SELECT user_id FROM items WHERE id = ?", (id,))
    if session.get("role") == "admin" or user_id[0][0] == session.get("user_id"):
        try:
            # Update entry
            run_sql("UPDATE items SET status = 'resolved' WHERE id = ?", (id,))
        except:
            if session.get("role") == "admin":
                return alert("Failed to update", "/manage_items", 500)
            else:
                return alert("Failed to update", "/", 500)
        if session.get("role") == "admin":
            return alert("Successfully updated item!", "/manage_items")
        else:
            return alert("Successfully updated item!", "/")
    return alert("Failed to update: Unauthorized", "/", 401)


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
                    users.phone_num AS user_phone_num,
                    requests.message AS message,
                    datetime(requests.date_requested, 'localtime') AS date_requested,
                    requests.image_path AS image_path,
                    requests.status AS request_status
                    FROM requests
                    INNER JOIN items ON requests.item_id = items.id
                    INNER JOIN users ON requests.user_id = users.id
                    """
    
    order_query = "ORDER BY requests.date_requested DESC LIMIT ?"
    
    # Get limit per pages
    limit = request.args.get("limit", 12, type=int)

    # Allow searching
    if request.method == "POST":
        # Get keyword for querying
        keyword = request.form["keyword"]
        status = request.form.get("status") or "o"

        try:
            request_list = run_sql(
                f"""
                    {query}
                    WHERE (requests.message LIKE ? OR 
                    items.title LIKE ? OR items.description LIKE ?)
                    AND items.status LIKE ?
                    {order_query}
                    """,
                (f"%{keyword}%", f"%{keyword}%", f"%{keyword}%", f"%{status}%", limit),
            )
        except:
            return alert("Failed to fetch requests", "/", 500)
    else:
        try:
            request_list = run_sql(f"{query} {order_query}", (limit,))
        except:
            return alert("Failed to fetch requests", "/", 500)

    return render_template("manage_request.html", requests=request_list)


# Approve request
@app.route("/approve_request/<int:id>", methods=["POST"])
@login_required
def approve_request(id):
    try:
        run_sql("UPDATE requests SET status = 'approved' WHERE id = ?", (id,))
    except:
        if session.get("role") == "admin":
            return alert("Failed to update", "/manage_requests", 500)
        return alert("Failed to update", "/", 500)
    if session.get("role") == "admin":
        return alert("Successfully approved request!", "/manage_requests")
    return alert("Successfully approved request!", "/")


# Reject request
@app.route("/reject_request/<int:id>", methods=["POST"])
@login_required
def reject_request(id):
    try:
        run_sql("UPDATE requests SET status = 'rejected' WHERE id = ?", (id,))
    except:
        return alert("Failed to update", "/manage_requests", 500)
    return alert("Successfully deleted rquest!", "/manage_requests")


"""Debugging"""


# Check if Flask is ran directly
if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=8000)
    # Bellow is the code to host a server to run on local devices
    # app.run(host="0.0.0.0", port=8000, debug=True)
