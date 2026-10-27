import sqlite3

from werkzeug.security import generate_password_hash

# Const for database name
DATABASE = "database.db"

"""Handles querying and connection to database via Sqlite3"""


def run_sql(query, params=None):
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    if params:
        c.execute(query, params)
    else:
        c.execute(query)

    # Check if query returned a value
    if c.description:
        result = c.fetchall()
    else:
        result = None

    conn.commit()
    conn.close()

    return result


# Set up database
def init_db():
    # Database creating queries

    dbs_queries = [
        """
        CREATE TABLE IF NOT EXISTS users (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              email TEXT UNIQUE NOT NULL,
              password TEXT NOT NULL,
              first_name TEXT NOT NULL,
              last_name TEXT NOT NULL,
              preferred_name TEXT DEFAULT NULL,
              phone_num TEXT DEFAULT NULL,
              role TEXT NOT NULL DEFAULT 'student'
        )
    """,
        """
        CREATE TABLE IF NOT EXISTS items (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              user_id INTEGER REFERENCES users(id) DEFAULT NULL,
              email TEXT NOT NULL,
              name TEXT NOT NULL,
              title TEXT NOT NULL,
              description TEXT DEFAULT NULL,
              image_path TEXT DEFAULT NULL,
              date_reported DATETIME DEFAULT CURRENT_TIMESTAMP,
              status TEXT NOT NULL DEFAULT 'good',
              approved BOOLEAN NOT NULL DEFAULT false
        )
    """,
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
    """,
    ]

    # Run SQL queries
    for query in dbs_queries:
        run_sql(query)

    # Add listing fields to existing databases without changing saved items.
    columns = {row['name'] for row in run_sql('PRAGMA table_info(items)')}
    for name, sql_type in [('cost_cents', 'INTEGER'), ('school_location', 'TEXT'), ('author_name', 'TEXT')]:
        if name not in columns:
            run_sql(f'ALTER TABLE items ADD COLUMN {name} {sql_type}')

    # Convert legacy categories to the current listing categories.
    run_sql("UPDATE items SET status = CASE status WHEN 'lost' THEN 'good' WHEN 'found' THEN 'fair' WHEN 'resolved' THEN 'sold' END WHERE status IN ('lost', 'found', 'resolved')")

    # Create a default admin account

    # Check for an admin account
    admin = run_sql("SELECT id FROM users WHERE role = ? LIMIT 1", ("admin",))

    if not admin:
        # Set up admin password
        password = generate_password_hash(
            "111111111", method="pbkdf2:sha256"
        )  # Set hashing style to avoid scrypt

        run_sql(
            """
                INSERT INTO users (email, password, first_name, last_name, phone_num, role) 
                VALUES (?, ?, ?, ?, ?, ?)
                """,
            ("admin@test.com", password, "Admin", "Admin", "+12121234567", "admin"),
        )
