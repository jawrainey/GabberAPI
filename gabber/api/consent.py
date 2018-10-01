# -*- coding: utf-8 -*-
"""
The consent for a Gabber session.
"""
from .. import db
from ..api.schemas.auth import UserSchemaHasAccess
from ..api.schemas.consent import ConsentType
from ..api.schemas.project import ProjectModelSchema
from ..api.schemas.session import RecordingSessionSchema
from ..api.auth import AuthToken
from ..models.projects import Project, InterviewSession
from ..models.user import User, SessionConsent as SessionConsentModel
from ..utils.general import CustomException, custom_response
from flask import current_app as app
from flask_restful import Resource
from itsdangerous import URLSafeSerializer, SignatureExpired, BadSignature
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
        consent_id = SessionConsent.validate_token(token)
        consent = SessionConsentModel.query.get(consent_id)
        _session = InterviewSession.query.get(consent.session_id)
        session = RecordingSessionSchema().dump(_session)
        project = ProjectModelSchema().dump(Project.query.get(_session.project_id))
        user = UserSchemaHasAccess().dump(User.query.get(consent.participant_id))
        return custom_response(200, data=dict(user=user, project=project, session=session, consent=consent.type))

    @staticmethod
    def put(token):
        """
        Lets a user update their consent for a gabber session.
        """
        consent_id = SessionConsent.validate_token(token)
        data = helpers.jsonify_request_or_abort()
        helpers.abort_if_errors_in_validation(ConsentType().validate(data))
        consent = SessionConsentModel.query.get(consent_id)
        consent.type = data['consent']
        db.session.commit()
        return custom_response(200)

    @staticmethod
    def generate_invite_token(consent_id):
        """
        Generates an invite URL with embedded information
        """
        return URLSafeSerializer(app.config["SECRET_KEY"]).dumps(consent_id, app.config['SALT'])

    @staticmethod
    def validate_token(token):
        """
        Validates that the token used exists
        """
        try:
            serializer = URLSafeSerializer(app.config['SECRET_KEY'])
            return serializer.loads(token, salt=app.config['SALT'])
        except Exception:
            raise CustomException(400, errors=['general.UNKNOWN_TOKEN'])

    @staticmethod
    def consent_url(session_id, user_id):
        """
        Generates an invite URL with embedded information
        """
        consent = SessionConsentModel.query.filter_by(session_id=session_id, participant_id=user_id).first()
        return '{}/consent/{}/'.format(app.config['WEB_HOST'], consent.token)
