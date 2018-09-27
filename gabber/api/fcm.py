# -*- coding: utf-8 -*-
"""
Actions on a users Firebase Cloud Messaging (FCM) token
"""
from .. import db
from ..models.user import User
from ..utils.helpers import abort_if_unknown_user, jsonify_request_or_abort
from ..utils.general import custom_response
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity


class TokenForUser(Resource):
    """
    Mapped to: /api/fcm/
    """
    @staticmethod
    @jwt_required
    def post():
        """
        Creates or updates the FCM token for a user (identified through JWT)
        """
        user = User.query.filter_by(email=get_jwt_identity()).first()
        abort_if_unknown_user(user)
        data = jsonify_request_or_abort()
        token = data['token']
        if token and token is not user.fcm_token:
            user.fcm_token = token
            db.session.commit()
        return custom_response(200)
