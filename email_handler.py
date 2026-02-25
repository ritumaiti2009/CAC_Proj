import textwrap

from flask_mail import Mail, Message
from threading import Thread


# Internal function that runs in a separate thread
def _send_async_email(app, mail, msg):
    with app.app_context():
        mail.send(msg)


# Send an email using flask_mail
def send_email(app, subject, body, recipients):
    mail = Mail(app)

    if isinstance(recipients, str):
        recipients = [recipients]

    # Remove unneccessary indents

    msg = Message(subject, recipients=recipients, body=textwrap.dedent(body))

    # Start a new thread to send the email
    Thread(target=_send_async_email, args=(app, mail, msg)).start()
