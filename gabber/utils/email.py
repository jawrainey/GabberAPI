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


def send_welcome_after_registration(email):
    pass


def send_welcome_and_consent_after_session(participants):
    pass


def send_forgot_password(email, url):
    send_email(receiver=email, subject="Gabber password reset", content=url)


def send_password_changed(email):
    send_email(receiver=email, subject="Your Gabber password was updated", content="Password successfully updated")


def send_project_member_invite(email):
    pass


def send_project_member_removal(email):
    pass
