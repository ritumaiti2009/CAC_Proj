from flask import redirect, render_template, session

def error(message, code):
    return render_template("error.html", num=code, m=message), code