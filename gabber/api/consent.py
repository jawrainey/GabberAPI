# -*- coding: utf-8 -*-
"""
The consent for a Gabber session.
"""
from flask_restful import Resource
from gabber import app, db
from gabber.api.schemas.auth import UserSchema
from gabber.api.schemas.consent import ConsentType
from gabber.api.schemas.project import ProjectModelSchema
from gabber.api.schemas.session import RecordingSessionSchema
from gabber.api.auth import AuthToken
from gabber.projects.models import Project, InterviewSession
from gabber.utils.general import custom_response
from gabber.users.models import User, SessionConsent as SessionConsentModel
from itsdangerous import URLSafeTimedSerializer
import gabber.api.helpers as helpers


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
