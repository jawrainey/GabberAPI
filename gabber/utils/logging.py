# -*- coding: utf-8 -*-
"""
Used to log incoming requests for analysis of user interactions.
"""
from gabber import db
from flask import request
from flask_login import current_user


class LogRequest(db.Model):
    """
    Stores meta-data from requests coming to our server. This allows queries
    to be written to determine usage patterns instead of regex on log files.
    """
    __tablename__ = 'logged_requests'

    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=db.func.now())

    uid = db.Column(db.Integer)
    sid = db.Column(db.String(768))
    method = db.Column(db.String(192))
    ip = db.Column(db.String(192))
    path = db.Column(db.String(192))
    agent = db.Column(db.String(192))
    data = db.Column(db.String(19200))

# Should be a normalised database; it's only used for lookup.
EVENTS = {
    0: {'type': 'audio-play', 'description': ""},
    1: {'type': 'audio-pause', 'description': ""},
    2: {'type': 'audio-seek', 'description': ""},
    3: {'type': 'audio-region-clicked', 'description': ""},
    4: {'type': 'audio-region-dbclicked', 'description': ""},
    5: {'type': 'click-create-connection', 'description': ""},
    6: {'type': 'click-show-replies-comment', 'description': ""},
    7: {'type': 'click-show-replies-connection', 'description': ""},
    8: {'type': 'click-write-comment-on-comment', 'description': ""},
    9: {'type': 'click-write-comment-on-connection', 'description': ""},
    10: {'type': 'click-save-comment', 'description': ""},
    11: {'type': 'click-save-connection', 'description': ""},
    12: {'type': 'click-close-reply-to-comment', 'description': ""},
    13: {'type': 'click-close-reply-to-connection', 'description': ""},
    14: {'type': 'click-close-new-connection', 'description': ""},
    15: {'type': 'click-create-connection', 'description': ""}
}


class AudioEvent(db.Model):
    """
    Stores the events twigged by user interactions with audio interviews.
    For now, this is a small collection (see: EVENTS above) for interaction validation.
    """
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=db.func.now())

    uid = db.Column(db.Integer)  # Could be FK
    sid = db.Column(db.String(768))
    type = db.Column(db.Integer)  # Should be associated with an events table.
    path = db.Column(db.String(192))
    data = db.Column(db.String(19200))


def log_audio_interview_events(event_type, content, uri_path):
    """
    Logs an event from the /interview/ page based on interactions with the audio.

    :param event_type: An ID of the event type from events table
    :param content: The associated content that uniquely identifies the event.
    :param uri_path: The URL where this request was sent from; is unique for each interview.
    """
    request_to_log = AudioEvent(uid=current_user.id, type=int(event_type),
                                sid=request.cookies.get('session', ''),
                                path=uri_path, data=str(content))
    db.session.add(request_to_log)
    db.session.commit()


def log_request():
    """
    Middleware: logs each incoming request to the database.
    """
    # Ensures objects modified in the session are not committed after the request unintentionally.
    # We must capture this prior to removing/expunging session data.
    uid = current_user.id
    db.session.expunge_all()

    # Only log none-private information
    form = dict(request.form)
    form.pop('password', None)

    # What if we are behind a proxy? see: https://goo.gl/XNs4GU
    if request.headers.getlist("X-Forwarded-For"):
        ip = request.headers.getlist("X-Forwarded-For")[0]
    else:
        ip = request.remote_addr

    # Cover all methods for sending data in the request as JSON string for future parsing.
    data = {'data': request.data, 'form': form, 'json': request.get_json(silent=True), 'files': dict(request.files)}
    request_to_log = LogRequest(uid=uid, sid=request.cookies.get('session', ''), method=request.method, ip=ip,
                                path=request.full_path, agent=request.user_agent.string, data=str(data))
    db.session.add(request_to_log)
    db.session.commit()
