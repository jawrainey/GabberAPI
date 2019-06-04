# -*- coding: utf-8 -*-
"""
Handles sending notifications through Firebase Cloud Messaging
"""
from pyfcm import FCMNotification
from ...models.language import SupportedLanguage
from ...models.projects import InterviewSession

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
    },
    "it": {
        "commented": {
            "title": "Nuovo commento nella tua conversazione",
            "body": "Tocca per visualizzare su gabber.audio"
        }
    },
    "ru": {
        "commented": {
            "title": "Новый комментарий к вашему разговору",
            "body": "Нажмите, чтобы посмотреть на gabber.audio"
        }
    }
}


def notify_participants_user_commented(pid, sid):
    for participant in InterviewSession.query.get(sid).participants:
        if participant.user.fcm_token:
            notify_user_commented(participant.user, pid, sid)


def notify_user_commented(user, pid, sid):
    from flask import current_app as app

    content = locales[SupportedLanguage.query.get(user.lang).code]['commented']
    push_service = FCMNotification(api_key=app.config['FCM_API_KEY'])

    push_service.notify_single_device(
        registration_id=user.fcm_token,
        message_title=content['title'],
        message_body=content['body'],
        data_message={"url": InterviewSession.session_url(pid, sid)}
    )

