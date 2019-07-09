# -*- coding: utf-8 -*-
"""
Models playlists created from snippets of conversations
"""
from .. import db


class Playlist(db.Model):
    """
    The name and creator of a playlist.

    TODO: for simplicity this does not consider a collaborative playlist
    """
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(140))
    description = db.Column(db.String(1400))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    is_active = db.Column(db.Boolean, default=True)  # Used as a 'soft-delete'
    order = db.Column(db.JSON)

    annotations = db.relationship('PlaylistAnnotations', backref="playlist", lazy='dynamic')

    created_on = db.Column(db.DateTime, default=db.func.now())
    updated_on = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now())


class PlaylistAnnotations(db.Model):
    """
    The regions chosen by a user for a specific playlist
    """
    id = db.Column(db.Integer, primary_key=True)
    playlist_id = db.Column(db.Integer, db.ForeignKey('playlist.id'))
    annotation_id = db.Column(db.Integer, db.ForeignKey('connection.id'))
