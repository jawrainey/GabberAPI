from gabber import db
from flask_restful import Resource, reqparse
from flask_jwt_extended import jwt_required, get_jwt_identity
from gabber.projects.models import InterviewSession, InterviewParticipants, InterviewPrompts, Project
from gabber.users.models import User
from uuid import uuid4
import gabber.api.helpers as helpers
from marshmallow import ValidationError
from gabber.api.schemas.create_session import ParticipantScheme, RecordingAnnotationSchema
from gabber.api.schemas.helpers import is_not_empty
import json


class ProjectSessions(Resource):
    """
    Mapped to: /api/project/<int:id>/sessions/
    """
    @jwt_required
    def get(self, pid):
        """
        VIEW all the Gabber sessions for a given project

        :param pid: the project id
        :return: A list of serialized sessions if sessions exist, otherwise an empty list
        """
        user = User.query.filter_by(email=get_jwt_identity()).first()
        helpers.abort_if_unknown_user(user)
        project = Project.query.get(pid)
        helpers.abort_if_unknown_project(project)
        helpers.abort_if_not_a_member_and_private(user, project)
        interview_sessions = InterviewSession.query.filter_by(project_id=pid).all()
        return [i.serialize() for i in interview_sessions]

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

        # The request is a multi-form request from the mobile device, and hence data needs
        # to be validated through RequestParser and converted to JSON before serializing.

        from werkzeug.datastructures import FileStorage
        parser = reqparse.RequestParser()
        parser.add_argument('recording', location='files', type=FileStorage, required=True,
                            help="An audio recording is required, ideally encoded as MP4.")
        parser.add_argument('creatorEmail', required=False,
                            help="The creator (i.e. email) of the interviewer is required, i.e. who created it? "
                                 "If this is not provided, then the user authenticated with the upload is used.")
        parser.add_argument('participants', required=True,
                            help="A dictionary of participants in the interview is required, i.e. who took part?")
        parser.add_argument('prompts', required=True,
                            help="A dictionary of prompts that were selected during the interview is required")

        args = parser.parse_args()

        try:
            _prompts = json.loads(args['prompts'])
            is_not_empty(_prompts, message="The list of prompts should not be empty")
            prompts = RecordingAnnotationSchema(many=True).load(_prompts)
        except ValueError:
            return {'errors': ['The content for the prompts argument is invalid JSON.']}, 404
        except ValidationError as err:
            return {"errors": err.messages}, 400

        try:
            _participants = json.loads(args['participants'])
            is_not_empty(_participants, message="The PARTICIPANTS list does not contain any attributes")
            participants = ParticipantScheme(many=True).load(_participants)
        except ValueError:
            return {'errors': ['The content for the participants argument is invalid JSON.']}, 404
        except ValidationError as err:
            return {"errors": err.messages}, 400

        interview_session_id = uuid4().hex

        # Note: if an invalid email is provided (or one not known to the db) then creator is None
        creator = User.query.filter_by(email=args['creatorEmail']).first()
        creator_id = creator.id if creator else user.id

        interview_session = InterviewSession(id=interview_session_id, creator_id=creator_id, project_id=pid)

        # TODO: what if an error occurs during uploading to S3?
        self.__upload_interview_recording(args['recording'], interview_session_id, pid)
        interview_session.participants.extend(self.__add_participants(participants, interview_session_id))
        interview_session.prompts.extend(self.__add_structural_prompts(prompts, interview_session_id))

        db.session.add(interview_session)
        db.session.commit()
        return interview_session.serialize(), 201

    @staticmethod
    def __upload_interview_recording(recording, session_id, project_id):
        """
        Upload the session recording (audio file) to Amazon S3.
        The session and project IDs are used to categorize storage.

        :param recording: the audio file to upload
        :param session_id: the ID of the session associated with the recording
        :param project_id: the project associated with the session
        """
        from gabber.utils import amazon
        amazon.upload(recording, str(project_id) + "/" + str(session_id))

    @staticmethod
    def __add_participants(participants, session_id):
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
        from gabber.users.models import User
        _participants_to_add = []

        for p in participants:
            known_user = User.query.filter_by(email=p['Email']).first()
            # e.g. someone interviewed a person who is not a Gabber user
            if not known_user:
                known_user = User(fullname=p['Name'], email=p['Email'], password=uuid4().hex)
                # TODO: should they be made a member of the project once participated? -> YES
                db.session.add(known_user)
                db.session.commit()
                # TODO: if the new user was created, send a welcome email with a password reset.
            # TODO: ask the user to verify that they were involved in this Gabber and to provide consent.
            new_participant = InterviewParticipants(
                user_id=known_user.id,
                interview_id=session_id,
                role=p['Role'])
            _participants_to_add.append(new_participant)
        return _participants_to_add

    def __add_structural_prompts(self, prompts, session_id):
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
