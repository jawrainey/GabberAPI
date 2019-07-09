# -*- coding: utf-8 -*-
"""
Content for all PLAYLISTS that a user has access to
"""
from .. import db
from ..models.user import User
from ..models.playlist import Playlist as PlaylistModel
from ..api.schemas.playlist import PlaylistSchema
from ..utils.general import custom_response
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity
import gabber.utils.helpers as helpers


class Playlists(Resource):
    """
    Mapped to: /api/playlists
    """
    @staticmethod
    @jwt_required
    def get():
        """
        The PLAYLISTS the JWT user has created.
        """
        user = User.query.filter_by(email=get_jwt_identity()).first()
        helpers.abort_if_unknown_user(user)
        playlists = PlaylistModel.query.filter_by(user_id=user.id, is_active=True).all()
        return custom_response(200, data=PlaylistSchema(many=True).dump(playlists))

    @jwt_required
    def post(self):
        """
        CREATE a playlist
        """
        user = User.query.filter_by(email=get_jwt_identity()).first()
        helpers.abort_if_unknown_user(user)

        data = helpers.jsonify_request_or_abort()
        helpers.abort_if_errors_in_validation(PlaylistSchema().validate(data))
        playlist = PlaylistModel(name=data['name'], description=data['description'], user_id=user.id)
        db.session.add(playlist)
        db.session.commit()

        return custom_response(201, data=PlaylistSchema().dump(playlist))
