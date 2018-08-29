# -*- coding: utf-8 -*-
import json
import os
import requests
from flask import render_template, current_app as app
from ..models.language import SupportedLanguage
from ..models.projects import InterviewSession


class MailClient:
    def __init__(self, lang_id):
        lang = SupportedLanguage.query.get(lang_id)
        current = os.path.realpath(os.path.dirname(__file__))
        data = os.path.join(current, 'email/locales', '{0}.json'.format(lang.code if lang else 'en'))

        self.content = json.load(open(data))

        self.brand = app.config['BRAND']
        self.homepage = app.config['WEB_HOST']
        self.contact = app.config['CONTACT_EMAIL']
        self.mailbox = app.config['MAILBOX']
        self.apikey = app.config['MAIL_API_KEY']
        self.sender_name = app.config['MAIL_SENDER_NAME']
        self.sender_email = app.config['MAIL_SENDER_EMAIL']

    def forgot(self, user, url):
        content = self.content['forgot']
        content['subject'] = content['subject'].format(self.brand)
        content['name'] = user.fullname
        content['body'] = content['body'].format(self.brand)
        content['button_url'] = url

        self.send_email(user.email, content)

    def verify(self, user, url):
        content = self.content['verify']
        content['subject'] = content['subject'].format(self.brand)
        content['name'] = user.fullname
        content['body'] = content['body'].format(self.brand)
        content['button_url'] = url

        self.send_email(user.email, content)

    def consent(self, participant, names, project_title, session_id, consent_type):
        from ..models.user import User
        from ..api.consent import SessionConsent

        user = User.query.filter_by(email=participant['Email']).first()

        content = self.content['consent']
        content['subject'] = content['subject'].format(self.brand)
        content['name'] = user.fullname
        content['body'] = content['body'].format(self.brand, names, project_title, consent_type)
        content['button_url'] = SessionConsent.consent_url(session_id, user.id)

        self.send_email(user.email, content)

    def invite_registered(self, user, admin_name, project):
        num_sessions = len(InterviewSession.query.filter_by(project_id=project.id).all())
        content = self.content['invite_registered']
        content['subject'] = content['subject'].format(admin_name, self.brand)
        content['name'] = user.fullname
        content['body'] = content['body'].format(project.title, admin_name, num_sessions)
        content['button_url'] = '{0}/projects/{1}/sessions/'.format(self.homepage, project.id)

        self.send_email(user.email, content)

    def invite_unregistered(self, user, admin_name, project):
        from ..api.membership import ProjectInviteVerification

        num_sessions = len(InterviewSession.query.filter_by(project_id=project.id).all())
        content = self.content['invite_unregistered']
        content['subject'] = content['subject'].format(admin_name, self.brand)
        content['name'] = user.fullname
        content['body'] = content['body'].format(project.title, admin_name, num_sessions)
        content['button_url'] = ProjectInviteVerification.generate_invite_url(user.id, project.id)

        self.send_email(user.email, content)

    def build_html(self, content):
        content = self.__add_shared(content)
        content['bottom'] = content['bottom'].replace('Android', '<a href="{0}/android/">Android</a>'.format(self.homepage))
        content['bottom'] = content['bottom'].replace('iOS', '<a href="{0}/ios/">iOS</a>'.format(self.homepage))
        return render_template('action.html', **content)

    def build_plaintext(self, content):
        content = self.__add_shared(content)
        content['bottom'] = content['bottom'].replace('Android', 'Android ({0}/android/)'.format(self.homepage))
        content['bottom'] = content['bottom'].replace('iOS', 'iOS ({0}/ios)'.format(self.homepage))
        return u'Hi {name},\n\n{body}\n\n{button_label} ({button_url})' \
               u'\n\n{footer}\n{brand}\n\n{bottom}'.format(**self.__add_shared(content))

    def send_email(self, recipient, content):
        sender = '{0} <{1}>'.format(self.sender_name, self.sender_email)

        requests.post(
            'https://api.eu.mailgun.net/v3/{0}/messages'.format(self.mailbox),
            auth=('api', self.apikey),
            data={
                'h:sender': sender,
                'from': sender,
                'to': recipient,
                'subject': content['subject'],
                'text': self.build_plaintext(content),
                'html': self.build_html(content)
            }
        )

    def __add_shared(self, content):
        content['footer'] = content['footer'].format(self.contact)
        content['brand'] = self.brand
        content['brand_url'] = self.homepage
        content['bottom'] = self.content['misc']['footer'].format(self.brand)
        return content
