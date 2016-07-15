from gabber import app, mail
from flask import url_for, render_template, request
from itsdangerous import URLSafeTimedSerializer


def register_response(fullname, email):
    from flask_mail import Message
    message = Message('Gabber registration', recipients=[email])
    message.html = render_template('reg_email.html', data={'name': fullname})
    mail.send(message)


def email_consent(experience):
    # TODO: this will be invoked in upload()
    # Sends an email to a user to approve their audio experience, which
    # calls _generate_consent_url(who, what) below.
    from flask_mail import Message
    message = Message('Gabber: consent to share your experience with the world',
                      recipients=[experience.intervieweeEmail])
    content = {'name': experience.intervieweeName,
               'uri': request.url_root[:-1] + __consent_url(experience)}
    message.html = render_template('email.html', data=content)
    mail.send(message)


def confirm_consent(token, exp=3600):
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    try:
        consent = serializer.loads(token, salt=app.config['SALT'], max_age=exp)
    except:
        return False  # URI expired or invalid token created.
    return consent


def __consent_url(experience):
    ts = URLSafeTimedSerializer(app.config["SECRET_KEY"])
    properties = [experience.intervieweeName, experience.experience,
                  experience.authorImage]
    token = ts.dumps(properties, app.config['SALT'])
    return url_for('main.display_consent', token=token)
