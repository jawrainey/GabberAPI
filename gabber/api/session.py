# -*- coding: utf-8 -*-
"""
REST Actions for a Gabber session, e.g. the recording between participants
"""
from flask_restful import Resource
from flask_jwt_extended import jwt_optional, get_jwt_identity
from gabber.projects.models import InterviewSession, Project
from gabber.users.models import User
import gabber.api.helpers as helpers
from gabber.api.schemas.session import RecordingSessionSchema
from gabber.utils.general import custom_response


class ProjectSession(Resource):
    """
    Mapped to: /api/projects/<int:pid>/sessions/<string:sid>/
    """
    @jwt_optional
    def get(self, pid, sid):
        """
        An interview session for a given project
        if the user is a member of the project or if it is public

        :param pid: The project to associate with the session
        :param sid: The ID (as UUID) of the interview session to view
        :return: A serialized interview session
        """
        user = User.query.filter_by(email=get_jwt_identity()).first()
        helpers.abort_if_unknown_user(user)

        helpers.abort_on_unknown_project_id(pid)
        project = Project.query.get(pid)

        session = InterviewSession.query.get(sid)
        helpers.abort_if_unknown_session(session)
        helpers.abort_if_session_not_in_project(session, pid)

        if project.is_public:
            return custom_response(200, data=RecordingSessionSchema().dump(session))
        helpers.abort_if_not_a_member_and_private(user, project)
        return custom_response(200, data=RecordingSessionSchema().dump(session))
