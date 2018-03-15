# -*- coding: utf-8 -*-
"""
All emails send through sendgrid on behalf of Gabber through user-actions.
"""
import os
import sendgrid
from sendgrid.helpers.mail import Email, Content, Mail


def send_email(receiver, subject, content, sender="noreply@gabber.audio"):
    _sendgrid = sendgrid.SendGridAPIClient(apikey=os.environ.get('SENDGRID_API_KEY', 'secret'))
    mail = Mail(
      from_email=Email(email=sender, name="Gabber"),
      subject=subject,
      content=Content("text/plain", content),
      to_email=Email(receiver)
    )
    _sendgrid.client.mail.send.post(request_body=mail.get())


def welcome_after_account_creation(email):
    send_email(receiver=email, subject="Welcome to Gabber", content="You can create an account using this magic URL")


def send_welcome_after_registration(email):
    send_email(receiver=email, subject="Welcome to Gabber", content="Welcome")


def request_consent(participants, project):
    from gabber.users.models import User
    # Email each client to request individual consent on the recorded session.
    for participant in participants:
        user = User.query.filter_by(email=participant['Email']).first()
        subject = "Share your Gabber session by providing consent"
        content = "Thanks for taking part in a Gabber on the project %s." % project.title
        if not user.registered:
            content = "You can create an account using this magic URL <url>"
        send_email(receiver=user.email, subject=subject, content=content)


def send_forgot_password(email, url):
    send_email(receiver=email, subject="Gabber password reset", content=url)


def send_password_changed(email):
    send_email(receiver=email, subject="Gabber password successfully updated", content="Password successfully updated")


def send_project_member_joined(user, project):
    send_email(receiver=user.email, subject="Welcome to %s on Gabber" % project.title, content="Sorry that you left")


def send_project_member_left(user, project):
    send_email(receiver=user.email, subject="Gabber: sorry you left %s" % project.title, content="Sorry that you left")


def send_project_member_invite_registered_user(admin, user, project):
    """
    The user is registered and known to the system

    :param admin: The User model object for the admin sending the email.
    :param user: The User model object for the user to email.
    :param project: The User model object for the user to email.
    """
    # TODO: temporary content; will change once templates on sendgrid are used.
    content = "Hi %s, Let's listen and annotate! " \
              "%s invites you to join the project: %s. " \
              "Login to view the project: %s" \
              % (user.fullname, admin.fullname, project.title, 'https://gabber.audio/login/')
    subject = '%s invited you to join the project "%s" on Gabber' % (admin.fullname, project.title)
    send_email(receiver=user.email, subject=subject, content=content)


def send_project_member_invite_unregistered_user(admin, user, project):
    """
    The user exists (i.e. participated in a session) or was created above before sending the email
    """
    from gabber.api.auth import RegisterInvitedUser
    token_register_url = RegisterInvitedUser.generate_url(user.fullname, user.email, project.id, 'register')
    token_login_url = RegisterInvitedUser.generate_url(user.fullname, user.email, project.id, 'login')

    send_email(
        receiver=user.email,
        subject='%s invited you to join the project "%s" on Gabber' % (admin.fullname, project.title),
        content="Let's listen and annotate! %s invites you to join the project: %s "
                "HOWEVER, if you already have an account with us, then login: %s" %
                (admin.fullname, token_register_url, token_login_url),
    )


def send_project_member_removal(admin, user, project):
    """
    Once a user has been removed from a project they're notified
    (1) when (time), (2) where (project) and (3) who (admin) performed the action.
    """
    send_email(
        receiver=user.email,
        subject="%s removed you from %s on Gabber" % (admin.fullname, project.title),
        content="There are %s other projects that you can annotate and get involved with."
    )
