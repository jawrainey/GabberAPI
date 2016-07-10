from gabber import app
from flask import url_for
from itsdangerous import URLSafeTimedSerializer


def email_consent(email, experience):
    # TODO: this will be invoked in upload()
    # Sends an email to a user to approve their audio experience, which
    # calls _generate_consent_url(who, what) below.
    return 0


def generate_consent_url(experience):
    ts = URLSafeTimedSerializer(app.config["SECRET_KEY"])
    properties = [experience.intervieweeName, experience.experience,
                  experience.authorImage]
    token = ts.dumps(properties, app.config['SALT'])
    return url_for('consent', token=token)


def confirm_consent(token, exp=3600):
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    try:
        consent = serializer.loads(token, salt=app.config['SALT'], max_age=exp)
    except:
        return False  # URI expired or invalid token created.
    return consent
