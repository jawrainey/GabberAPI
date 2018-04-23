# -*- coding: utf-8 -*-
"""
Viewing all Gabber sessions and creating a new one
"""
from .. import db
from ..api.schemas.create_session import ParticipantScheme, RecordingAnnotationSchema
from ..api.schemas.session import RecordingSessionsSchema
from ..api.schemas.helpers import is_not_empty
from ..models.projects import InterviewSession, InterviewParticipants, InterviewPrompts, Project
from ..models.user import User
from ..utils.general import custom_response
from marshmallow import ValidationError
from flask_restful import Resource, reqparse, abort
from flask_jwt_extended import jwt_required, get_jwt_identity, jwt_optional
from uuid import uuid4
import gabber.utils.email as email_client
import gabber.utils.helpers as helpers
import json


class ProjectSessions(Resource):
    """
    Mapped to: /api/projects/<int:id>/sessions/
    """
    @jwt_optional
    def get(self, pid):
        """
        VIEW all the Gabber sessions for a given project

        :param pid: the project id
        :return: A list of serialized sessions if sessions exist, otherwise an empty list
        """
        project = Project.query.get(pid)
        helpers.abort_if_unknown_project(project)

        if project.is_public:
            sessions = InterviewSession.all_consented_sessions_by_project(project)
            return custom_response(200, data=RecordingSessionsSchema(many=True).dump(sessions))

        current_user = get_jwt_identity()
        user = User.query.filter_by(email=current_user).first()
        helpers.abort_if_unknown_user(user)
        helpers.abort_if_not_a_member_and_private(user, project)

        if current_user:
            is_creator_or_admin = user.role_for_project(pid) == 'admin' or project.creator == user.id
            sessions = InterviewSession.all_consented_sessions_by_project(project, is_creator_or_admin)
            return custom_response(200, data=RecordingSessionsSchema(many=True).dump(sessions))

    @jwt_required
    def post(self, pid):
        """
        CREATES a new session: only members of projects can upload to private projects.
        Anyone can upload to public projects as long as they are logged in via JWT;

        :param pid: the project to CREATE a new session for
        :return: the session serialized
        """
        user = User.query.filter_by(email=get_jwt_identity()).first()
        helpers.abort_if_unknown_user(user)
        project = Project.query.get(pid)
        helpers.abort_if_unknown_project(project)
        helpers.abort_if_not_a_member_and_private(user, project)

        # NOTE The request is a multi-form request from the mobile device, and hence data needs
        # to be validated through RequestParser and converted to JSON before serializing.

        from werkzeug.datastructures import FileStorage
        parser = reqparse.RequestParser()
        parser.add_argument('recording', location='files', type=FileStorage, required=True,
                            help="An audio recording is required, ideally encoded as MP4.")
        parser.add_argument('participants', required=True,
                            help="A dictionary of participants in the interview is required, i.e. who took part?")
        parser.add_argument('prompts', required=True,
                            help="A dictionary of prompts that were selected during the interview is required")

        args = parser.parse_args()

        prompts = self.validate_and_serialize(args['prompts'], 'prompts', RecordingAnnotationSchema(many=True))
        participants = self.validate_and_serialize(args['participants'], 'participants', ParticipantScheme(many=True))

        interview_session_id = uuid4().hex
        interview_session = InterviewSession(id=interview_session_id, creator_id=user.id, project_id=pid)
        self.__upload_interview_recording(args['recording'], interview_session_id, pid)
        interview_session.prompts.extend(self.__add_structural_prompts(prompts, interview_session_id))
        interview_session.participants.extend(self.__add_participants(participants, interview_session_id, project.id))

        db.session.add(interview_session)
        db.session.commit()
        email_client.request_consent(participants, interview_session)
        return {}, 201

    @staticmethod
    def validate_and_serialize(data, message, scheme):
        try:
            json_data = json.loads(data)
            # Checking for empty lists is required due to bug in marshmallow
            is_not_empty(json_data, message="The %s list should not be empty" % message)
            return scheme.load(json_data)
        except ValueError:
            abort(400, message={'errors': ['The content for the %s argument is invalid JSON.' % message]})
        except ValidationError as err:
            abort(400, message={'errors': err.messages})

    @staticmethod
    def __upload_interview_recording(recording, session_id, project_id):
        """
        Upload the session recording (audio file) to Amazon S3.
        The session and project IDs are used to categorize storage.

        :param recording: the audio file to upload
        :param session_id: the ID of the session associated with the recording
        :param project_id: the project associated with the session
        """
        from ..utils import amazon
        try:
            amazon.upload(recording, project_id, session_id)
        except Exception:
            abort(500, message={'errors': 'There was an issue uploading your session.'})

    @staticmethod
    def __add_participants(participants, session_id, project_id):
        """
        Each interview has a set of participants (>1), who each have a role (interviewer or interviewee).
        The problem is that these participants may be known to the system, having been interviewed by
        other users elsewhere. We want to determine this to link known users with the interview.
        If they are new, hence unknown, a user account is created (that represents a participant) for them,
        and an email sent to ask them to get involved in Gabber as a system.

        :param participants: Dictionary of those involved (User.id) in an interview (Interview.id); metadata
        about each participant (mapping to a User model, i.e. their name and email) should also be provided.
        :return: A list of InterviewParticipants that were used in a specific interview session.
        """
        from ..models.user import User
        from ..models.projects import Membership
        _participants_to_add = []

        for p in participants:
            known_user = User.query.filter_by(email=p['Email']).first()
            # e.g. someone interviewed a person who is not a Gabber user
            if not known_user:
                known_user = User.create_unregistered_user(p['Name'], p['Email'])
            # By default, participants involved in a Gabber become members
            if not known_user.is_project_member(project_id):
                Membership.join_project(known_user.id, project_id)
            participant = InterviewParticipants(known_user.id, session_id, p['Role'])
            _participants_to_add.append(participant)
        return _participants_to_add

    @staticmethod
    def __add_structural_prompts(prompts, session_id):
        """
        The prompts that were selected during an interview to structure the conversation
        :param prompts: The prompts, including the ID (what was discussed), and Start/End of the region annotated.
        :return: A list of InterviewPrompts that were used in a specific interview session.
        """
        return [
            InterviewPrompts(
                prompt_id=p['PromptID'],
                interview_id=session_id,
                start_interval=p['Start'],
                end_interval=p['End']
            )
            for p in prompts
        ]
