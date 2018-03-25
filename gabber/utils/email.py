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


def send_email_message(receiver, data):
    mail = __construct_email(receiver, data['subject'])
    mail.personalizations[0].add_substitution(Substitution("{{name}}", data['name']))
    mail.personalizations[0].add_substitution(Substitution("{{main}}", data['body']))
    mail.template_id = "2e018c30-0b95-4abe-a8d0-ba9148ac5dd3"
    __send_email(mail)


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
        top_body='Please verify your account',
        button_url=(app.config['WEB_HOST'] + '/verify/' + token + '/'),
        button_label='Verify Email',
        bottom_body=''))


def send_welcome_after_registration(user):
    data = dict(subject="Welcome to Gabber, what's next?", name=user.fullname)
    data['body'] = 'Thanks for registering ... TODO: content/images to describe Gabber process.'
    send_email_message(user.email, data)


def request_consent(participants, project, session):
    # Note: having to create a consent model here as this is called after participants are created
    from gabber.models.user import User, SessionConsent as SessionConsentModel
    from gabber.api.consent import SessionConsent

    content = 'Thanks for Gabbering on the <b>%s</b>.' \
              'Click the button to review and consent to your recording being used, and shared within the project.' \
              'You can now review the content and provide consent.' % project.title

    # Email each client to request individual consent on the recorded session.
    for participant in participants:
        user = User.query.filter_by(email=participant['Email']).first()
        # Create a default consent as participants will receive an email afterwards
        # to update their consent. Likewise, this ensures all queries manipulate all data.
        consent = SessionConsentModel.create_default_consent(session.id, user.id)
        send_email_action(user.email, dict(
            subject='Provide Consent to your Gabber recording',
            name=user.fullname,
            top_body=content,
            button_url=SessionConsent.generate_invite_url(user.id, project.id, session.id, consent.id),
            button_label='Provide Consent',
            bottom_body=''))


def send_forgot_password(user, url):
    data = dict()
    data['subject'] = "Gabber password reset"
    data['name'] = user.fullname
    data['top_body'] = "You recently requested to reset your password for your Gabber account. " \
                       "Click the button below to reset your it:"
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
    url = app.config['WEB_HOST'] + '/projects/' + project.id + '/'
    subject = '%s invited you to join the project "%s" on Gabber' % (admin.fullname, project.title)
    content = "Hi %s, Let's listen and annotate! " \
              "%s invites you to join the project: %s. " \
              "Login to view the project: %s" \
              % (user.fullname, admin.fullname, project.title, url)

    send_email_action(user.email, dict(subject=subject, body=content))


def send_project_member_invite_unregistered_user(admin, user, project):
    """
    The user exists (i.e. participated in a session) or was created above before sending the email
    """
    from gabber.api.membership import ProjectInviteVerification

    data = dict()
    data['subject'] = '%s invited you to join the project %s on Gabber' % (admin.fullname, project.title)
    data['name'] = user.fullname
    data['top_body'] = '%s invites you to join the project <b>%s</b>.</br>' \
                       'Register by clicking the button below and the account you create will be part of the project ' \
                       'where you can begin listening to and annotating Gabbers.' \
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
    data['subject'] = "%s removed you from %s on Gabber" % (admin.fullname, project.title),
    data['name'] = user.fullname
    data['body'] = "There are %s other projects that you can annotate and get involved with."
    send_email_message(user.email, data)

