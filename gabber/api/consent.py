# -*- coding: utf-8 -*-
"""
The consent for a Gabber session.
"""
from .. import db
from ..api.schemas.auth import UserSchema
from ..api.schemas.consent import ConsentType
from ..api.schemas.project import ProjectModelSchema
from ..api.schemas.session import RecordingSessionSchema
from ..api.auth import AuthToken
from ..models.projects import Project, InterviewSession
from ..models.user import User, SessionConsent as SessionConsentModel
from ..utils.general import custom_response
from flask import current_app as app
from flask_restful import Resource
from itsdangerous import URLSafeTimedSerializer
import gabber.utils.helpers as helpers


class SessionConsent(Resource):
    """
    Mapped to: /api/consent/<token>/
    """
    @staticmethod
    def get(token):
        """
        Returns the project, session and user associated with the session that is being consented by the user.
        """
        data = AuthToken.validate_token(token)
        user = UserSchema().dump(User.query.get(data['user_id']))
        project = ProjectModelSchema().dump(Project.query.get(data['project_id']))
        session = RecordingSessionSchema().dump(InterviewSession.query.get(data['session_id']))
        return custom_response(200, data=dict(user=user, project=project, session=session))

    @staticmethod
    def put(token):
        """
        Lets a user update their consent for a gabber session.
        """
        token_data = AuthToken.validate_token(token)
        data = helpers.jsonify_request_or_abort()
        helpers.abort_if_errors_in_validation(ConsentType().validate(data))
        consent = SessionConsentModel.query.get(token_data['consent_id'])
        consent.type = data['type']
        db.session.commit()
        return custom_response(200)

    @staticmethod
    def generate_invite_url(user_id, project_id, session_id, consent_id):
        """
        Generates an invite URL with embedded information
        """
        payload = dict(user_id=user_id, project_id=project_id, session_id=session_id, consent_id=consent_id)
        token = URLSafeTimedSerializer(app.config["SECRET_KEY"]).dumps(payload, app.config['SALT'])
        return '%s/consent/%s/' % (app.config['WEB_HOST'], token)
