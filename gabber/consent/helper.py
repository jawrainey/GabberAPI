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


def email_consent(interview, email):
    import json
    # TODO: abstract this per project basis?
    content = json.load(open('gabber/templates/emails/consent.json', 'r'))
    content['button-url'] = request.url_root[:-1] + __consent_url(interview, email)

    from flask_mail import Message
    from gabber.projects.models import ProjectPrompt
    prompt_text = ProjectPrompt.query.filter_by(
        id=interview.prompt_id).first().text_prompt
    message = Message('Gabber consent: ' + prompt_text,
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
    # TODO: for now all recordings will be made public until the following changes are made
    return True
    from gabber.projects.models import InterviewSession
    interview = InterviewSession.query.filter(InterviewSession.recording_url == filename).first()
    if interview and 0 not in [c.type.lower() for c in interview.consents.all()]:
        return True
    return False


def __consent_url(interview, email):
    ts = URLSafeTimedSerializer(app.config["SECRET_KEY"])
    properties = [email, interview.audio, interview.image]
    token = ts.dumps(properties, app.config['SALT'])
    return url_for('consent.display_consent', token=token)
