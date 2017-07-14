# -*- coding: utf-8 -*-
"""
Used to log incoming requests to the server to support
filtering and analysis of user interactions.
"""
from gabber import db
from flask import request


class LogRequest(db.Model):
    """
    Stores meta-data from requests coming to our server. This allows queries
    to be written to determine usage patterns instead of regex on log files.
    """
    __tablename__ = 'logged_requests'

    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=db.func.now())

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
    db.session.remove()
    # Only log none-private information
    form = dict(request.form)
    form.pop('password', None)
    # Cover all methods for sending data in the request as JSON string for future parsing.
    data = {'data': request.data, 'form': form, 'json': request.get_json(silent=True), 'files': dict(request.files)}
    request_to_log = LogRequest(method=request.method, ip=request.remote_addr, path=request.full_path,
                                agent=request.user_agent.string, data=str(data))
    db.session.add(request_to_log)
    db.session.commit()
