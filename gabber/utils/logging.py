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
