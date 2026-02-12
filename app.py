import os
import sqlite3

from flask import Flask, flash, redirect, render_template, request, session  
from flask_session import Session   
from datetime import timedelta
from werkzeug.security import check_password_hash, generate_password_hash

# Configure application
app = Flask(__name__)
app.secret_key = "fbla_lost_and_found".encode('utf8') # Required for flask session security

# Set up database
def init_db():
    # Connects to the database and make a cursor to interact with it
    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    # Create databases

    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
              id INTERGER PRIMARY KEY AUTOINCREMENET,
              email TEXT UNIQUE NOT NULL,
              password TEXT NOT NULL,
              first_name TEXT NOT NULL,
              last_name TEXT NOT NULL,
              preferred_name TEXT,
              homeroom_class TEXT NOT NULL,
              phone_num TEXT
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS items (
              id INTERGER PRIMARY KEY AUTOINCREMENET,
              user_id INTERGER FOREIGN KEY REFERENCES Persons(PersonID) NOT NULL,
              title TEXT NOT NULL,
              description TEXT,
              image_path TEXT,
              date_reported DATETIME DEFAULT CURRENT_TIMESTAMP,
              status TEXT NOT NULL DEFAULT 'lost'
        )
    ''')

    conn.commit()
    conn.close()
init_db()