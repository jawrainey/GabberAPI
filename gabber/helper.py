from gabber import app, mail
from flask import url_for, render_template, request
from itsdangerous import URLSafeTimedSerializer


def snowball(email):
    # Do not snowball if already in known users?
    from flask_mail import Message
    message = Message('Gabber with your friends', recipients=[email])
    message.html = render_template('snowball_email.html')
    mail.send(message)


def email_consent(experience, email):
    # Sends an email to a user to approve their audio experience, which
    # calls _generate_consent_url(who, what) below.
    import json
    content = json.load(open('gabber/templates/emails/consent.json', 'r'))
    content['button-url'] = request.url_root[:-1] + __consent_url(experience, email)

    from flask_mail import Message
    message = Message('Consent for your Gabber -- ' + experience.promptText,
                      recipients=[email],
                      sender=("Gabber", app.config['MAIL_USERNAME']),
                      html=render_template("emails/layout.html", data=content))
    mail.send(message)


def commissioned_projects():
    """
    The JSON configured through the commissioning of a project.
    """
    # TODO: this would be stored in database and updated in design process.
    import json
    with open("conf/prompts.json", 'r') as projects:
        return json.load(projects)


def theme_by_prompt(prompt_text):
    """
    Obtains the theme of a project based on a child element (prompt text).

    Args:
        prompt_text (str): the element to search for in the JSON of projects.

    Note: As a prompt-text is associated with each Gabber uploaded, we use this,
    rather than create/send another variable as a look-up for the parent theme.
    """
    for pj in commissioned_projects():
        if (len([p for p in pj['prompts'] if prompt_text == p['prompt']]) > 0):
            return pj['theme']


def confirm_consent(token):
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    try:
        consent = serializer.loads(token, salt=app.config['SALT'])
    except:
        return False  # URI expired or invalid token created.
    return consent


def consented(filename):
    from gabber.models import Experience
    if Experience.query.filter(
        (Experience.experience == filename) &
        ((Experience.consentInterviewer == "ALL") |
         (Experience.consentInterviewer == "AUD")) &
        ((Experience.consentInterviewee == "ALL") |
         (Experience.consentInterviewee == "AUD"))).all():
        return True
    return False


def __consent_url(experience, email):
    ts = URLSafeTimedSerializer(app.config["SECRET_KEY"])
    properties = [email, experience.experience, experience.authorImage]
    token = ts.dumps(properties, app.config['SALT'])
    return url_for('main.display_consent', token=token)
