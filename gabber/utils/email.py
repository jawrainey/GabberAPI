# -*- coding: utf-8 -*-
"""
All emails send through sendgrid on behalf of Gabber through user-actions.
"""
import os
import sendgrid
from sendgrid.helpers.mail import Email, Content, Mail, Substitution
from flask import current_app as app

SEND_GRID = sendgrid.SendGridAPIClient(apikey=os.environ.get('SENDGRID_API_KEY', ''))


def __construct_email(receiver, subject):
    return Mail(
        from_email=Email(email="noreply@gabber.audio", name="Gabber"),
        to_email=Email(receiver),
        subject=subject,
        content=Content("text/html", "."))


def __send_email(mail):
    try:
        SEND_GRID.client.mail.send.post(request_body=mail.get())
    except Exception as e:
        print("TODO: log details of error %s" % e)


def send_email_action(receiver, data):
    mail = __construct_email(receiver, data['subject'])
    mail.personalizations[0].add_substitution(Substitution("{{name}}", data['name']))
    mail.personalizations[0].add_substitution(Substitution("{{top_body}}", data['top_body']))
    mail.personalizations[0].add_substitution(Substitution("{{button_url}}", data['button_url']))
    mail.personalizations[0].add_substitution(Substitution("{{button_label}}", data['button_label']))
    mail.personalizations[0].add_substitution(Substitution("{{bottom_body}}", data['bottom_body']))
    mail.template_id = "63ccd557-7e50-4447-9c38-c52646b6fe8a"
    __send_email(mail)


def send_email_verification(user, token):
    send_email_action(user.email, dict(
        subject='Verify your Gabber account',
        name=user.fullname,
        top_body='Welcome to Gabber! Please verify your email address by tapping on the button below.',
        button_url=(app.config['WEB_HOST'] + '/verify/' + token + '/'),
        button_label='Verify Email',
        bottom_body=''))


def send_register_notification(user):
    send_email_action(user.email, dict(
        subject='Attempt to register with your email',
        name=user.fullname,
        top_body='Someone has tried to access your email account. If this was you and you have forgot your password,'
                 'then reset it using the button below.',
        button_url=(app.config['WEB_HOST'] + '/forgot/'),
        button_label='Reset Password',
        bottom_body='If you did not make this request, then disregard this email.'))


def format_names(participants):
    # TODO: this is related to a bug in the mobile apps
    participants = [p.replace(' (You)', '') for p in participants]

    if len(participants) == 1:
        participant = participants[0]
        return participant.decode('UTF-8') if isinstance(participant, str) else participant
    if len(participants) == 2:
        return u' and '.join(participants)
    if len(participants) > 2:
        return u'{} and {}'.format(u', '.join(participants[0:-1]), participants[-1])


def request_consent(participants, session):
    # Note: having to create a consent model here as this is called after participants are created
    from ..models.user import User, SessionConsent as SessionConsentModel
    from ..models.projects import Project
    from ..api.consent import SessionConsent

    names = map(unicode, [p['Name'].decode('UTF-8') if isinstance(p, str) else p["Name"] for p in participants])
    names = format_names(names)

    # Consent is the same initially (i.e. what was agreed in the app),so anyone for the session is fine.
    session_consent = SessionConsentModel.query.filter_by(session_id=session.id).first()
    project = Project.query.get(session.project_id)

    content = u'You recently participated in a Gabber conversation with <b>{0}</b> for the <b>{1}</b> project ' \
              u'where you agreed for <b>{2}</b> to have access to your conversation.<br><br>' \
              u'Your conversation will undergo a 24-hour embargo where only conversation participants can listen. ' \
              u'This gives you time to review your consent before the agreed-upon consent prior to the conversation ' \
              u'begins to be used. ' \
              u'After this time, the consent that you have agreed prior to recording (i.e. {2}) will be used. ' \
              u'If you would like other people to view, listen and tag your recording, ' \
              u'then your consent must be either public or members.'.format(names, project.title, session_consent.type)

    # Email each client to request individual consent on the recorded session.
    for participant in participants:
        user = User.query.filter_by(email=participant['Email']).first()
        # Create a default consent as participants will receive an email afterwards
        # to update their consent. Likewise, this ensures all queries manipulate all data.
        send_email_action(user.email, dict(
            subject='[URGENT]: Review consent for your Gabber conversation',
            name=user.fullname,
            top_body=content,
            button_url=SessionConsent.consent_url(session.id, user.id),
            button_label='Review Consent',
            bottom_body='You can use the link above at any time to review and update your consent for this conversation.'))


def send_forgot_password(user, url):
    data = dict()
    data['subject'] = "Gabber password reset"
    data['name'] = user.fullname
    data['top_body'] = "You requested to reset your password for your Gabber account. " \
                       "Click the link below and you'll be redirected to a secure site where you can set a new password."
    data['button_url'] = url
    data['button_label'] = "Reset your password"
    data['bottom_body'] = "If you did not request a password reset, " \
                          "then please ignore this email or contact us and let us know. " \
                          "This password reset is only valid for the next 30 minutes."
    send_email_action(user.email, data)


def send_project_member_invite_registered_user(admin, user, project):
    """
    The user is registered and known to the system

    :param admin: The User model object for the admin sending the email.
    :param user: The User model object for the user to email.
    :param project: The User model object for the user to email.
    """
    data = dict(name=user.fullname, button_label='View Project', bottom_body='')
    data['subject'] = '%s invited you to join the project "%s" on Gabber' % (admin.fullname, project.title)
    data['top_body'] = "Hi %s,<br> %s invites you to join the project: %s. " \
                       "Login to view the project:" % (user.fullname, admin.fullname, project.title)
    data['button_url'] = '{}/projects/'.format(app.config['WEB_HOST'])

    send_email_action(user.email, data)


def send_project_member_invite_unregistered_user(admin, user, project):
    """
    The user exists (i.e. participated in a session) or was created above before sending the email
    """
    from ..api.membership import ProjectInviteVerification

    data = dict()
    data['subject'] = '%s invited you to join the project %s on Gabber' % (admin.fullname, project.title)
    data['name'] = user.fullname
    data['top_body'] = '%s invites you to join the project <b>%s</b>.</br>' \
                       'Register by clicking the button below and you will become a project member ' \
                       'where you can begin listening to Gabber conversations.' \
                       '' % (admin.fullname, project.title)
    data['button_url'] = ProjectInviteVerification.generate_invite_url(user.id, project.id)
    data['button_label'] = 'Join the project'
    data['bottom_body'] = ''
    send_email_action(user.email, data)


def send_project_member_removal(admin, user, project):
    """
    Once a user has been removed from a project they're notified
    (1) when (time), (2) where (project) and (3) who (admin) performed the action.
    """
    data = dict()
    data['subject'] = "%s removed you from %s on Gabber" % (admin.fullname, project.title)
    data['name'] = user.fullname
    data['top_body'] = "You have been removed from %s by %s, however, " \
                       "there are other projects that you can contribute " \
                       "to and get involved with." % (admin.fullname, project.title)
    data['button_url'] = '{}/projects/'.format(app.config['WEB_HOST'])
    data['button_label'] = 'View other projects'
    data['bottom_body'] = ''
    send_email_action(user.email, data)

