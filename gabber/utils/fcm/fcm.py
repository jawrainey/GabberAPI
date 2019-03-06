# -*- coding: utf-8 -*-
"""
Handles sending notifications through Firebase Cloud Messaging
"""
from pyfcm import FCMNotification
from ...models.language import SupportedLanguage

# Store these here while #Notifications is small
locales = {
    "ar": {
        "commented": {
            "title": "تعليق جديد على محادثتك",
            "body": "انقر لعرضه على gabber.audio"
        }
    },
    "en": {
        "commented": {
            "title": "New comment on your conversation",
            "body": "Tap to view on gabber.audio"
        }
    },
    "es": {
        "commented": {
            "title": "Nuevo comentario en tu conversación",
            "body": "Clic para ver en gabber.audio"
        }
    },
    "fr": {
        "commented": {
            "title": "Nouveau commentaire sur votre conversation",
            "body": "Appuyez pour afficher sur gabber.audio"
        }
    }
}


def notify_participants_user_commented(pid, sid):
    from ...models.projects import InterviewSession
    for participant in InterviewSession.query.get(sid).participants:
        if participant.user.fcm_token:
            notify_user_commented(participant.user, pid, sid)


def notify_user_commented(user, pid, sid):
    from flask import current_app as app

    content = locales[SupportedLanguage.query.get(user.lang).code]['commented']
    push_service = FCMNotification(api_key=app.config['FCM_API_KEY'])
    # NOTE: this URL is currently different from the main Gabber website
    session_url = '{0}/themes/{1}/conversations/{2}'.format(app.config['WEB_HOST'], pid, sid)

    push_service.notify_single_device(
        registration_id=user.fcm_token,
        message_title=content['title'],
        message_body=content['body'],
        data_message={"url": session_url}
    )

