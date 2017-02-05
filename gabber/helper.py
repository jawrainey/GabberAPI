from gabber import app, mail
from flask import url_for, render_template, request
from itsdangerous import URLSafeTimedSerializer


def snowball(email):
    # Do not snowball if already in known users?
    from flask_mail import Message
    content={'title': '', 'name': '', 'main-content': '', 'sub-content' : ''}
    message = Message('Gabber with your friends: ',
                      recipients=[email],
                      sender=("Gabber", app.config['MAIL_USERNAME']),
                      html=render_template("emails/layout.html", data=content))

    message.html = render_template('views/snowball_email.html')
    mail.send(message)


def email_consent(experience, email):
    # Sends an email to a user to approve their audio experience, which
    # calls _generate_consent_url(who, what) below.
    import json
    # TODO: abstract this per project basis?
    # do this based on details of the experience, e.g. project by extension?
    content = json.load(open('gabber/templates/emails/consent.json', 'r'))
    content['button-url'] = request.url_root[:-1] + __consent_url(experience, email)

    from flask_mail import Message
    message = Message('Gabber consent: ' + experience.promptText,
                      recipients=[email],
                      sender=("Gabber", app.config['MAIL_USERNAME']),
                      html=render_template("emails/layout.html", data=content))
    mail.send(message)


def confirm_consent(token):
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    try:
        consent = serializer.loads(token, salt=app.config['SALT'])
        # Improves readability when accessing within views.
        consent = {'email': consent[0], 'audio': consent[1], 'image': consent[2]}
    except:
        return False  # URI expired or invalid token created.
    return consent


def consented(filename):
    """
    Checks if participants have provided consent for an interview to be public.

    Returns:
        bool: True if all participants provided full consent, otherwise False.
    """
    from gabber.models import Interview
    interview = Interview.query.filter(Interview.audio == filename).first()
    if interview and 'NONE' not in [c.type for c in interview.consents.all()]:
        return True
    return False


def __consent_url(interview, email):
    ts = URLSafeTimedSerializer(app.config["SECRET_KEY"])
    properties = [email, interview.audio, interview.image]
    token = ts.dumps(properties, app.config['SALT'])
    return url_for('main.display_consent', token=token)
