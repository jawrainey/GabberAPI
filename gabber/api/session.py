# -*- coding: utf-8 -*-
"""
REST Actions for a Gabber session, e.g. the recording between participants
"""
from ..api.schemas.session import RecordingSessionSchema
from ..models.projects import InterviewSession, Project
from ..models.user import User
from ..utils.general import custom_response
from flask_restful import Resource
from flask_jwt_extended import jwt_optional, get_jwt_identity
import gabber.utils.helpers as helpers
from datetime import datetime, timedelta


class ProjectSession(Resource):
    """
    Mapped to: /api/projects/<int:pid>/sessions/<string:sid>/
    """
    @jwt_optional
    def get(self, pid, sid):
        """
        An interview session for a given project; viewing depends in consent and project visibility.
        """
        helpers.abort_on_unknown_project_id(pid)
        project = Project.query.get(pid)

        session = InterviewSession.query.get(sid)
        session.prompts.sort(key=lambda x: x.start_interval, reverse=False)

        helpers.abort_if_unknown_session(session)
        helpers.abort_if_session_not_in_project(session, pid)

        jwt_user = get_jwt_identity()
        user = User.query.filter_by(email=jwt_user).first()

        if jwt_user or not project.is_public:
            helpers.abort_if_not_a_member_and_private(user, project)

        # In the first 24 hours of capturing a conversation only participants of the conversation can review it
        if datetime.now() < (session.created_on + timedelta(hours=24)):
            if user and session.user_is_participant(user):
                return custom_response(200, data=RecordingSessionSchema().dump(session))
            else:
                return custom_response(400, errors=['general.EMBARGO'])

        # If the user is known and is an administrator or creator, then they can view the session regardless.
        if user and (user.role_for_project(pid) in ['administrator', 'researcher'] or project.creator == user.id or session.user_is_participant(user)):
            return custom_response(200, data=RecordingSessionSchema().dump(session))
        else:
            _session = RecordingSessionSchema().dump(session) if session.consented(project.is_public) else None
            return custom_response(200 if _session else 404, _session)
