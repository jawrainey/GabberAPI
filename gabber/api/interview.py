# -*- coding: utf-8 -*-
"""
REST Actions for an InterviewSession
"""
from gabber import db
from flask_restful import Resource, reqparse
from gabber.projects.models import InterviewSession, InterviewParticipants, InterviewPrompts
import json
from uuid import uuid4


class InterviewSessions(Resource):
    """
    REST Actions for an InterviewSession
    """
    def get(self, sid):
        """
        An interview for a given session

        Mapped to: /api/interview/<int:session_id>

        :param sid: The ID of a interview, which is the session ID
        :return: a dictionary of meta-data associated with a given project
        """
        # TODO: validation: is the SID valid?
        return InterviewSession.query.get(sid).json(), 200

    def post(self):
        """
        Creates a new interview session

        Mapped to: '/api/interview/'

        :return: True if session was stored correctly, otherwise False
        """
        from werkzeug.datastructures import FileStorage
        parser = reqparse.RequestParser()
        parser.add_argument('recording', location='files', type=FileStorage, required=True,
                            help="An audio recording is required, ideally encoded as MP4.")

        parser.add_argument('projectID', required=True,
                            help="A project ID for the interview is required, i.e. what's it about?")
        parser.add_argument('creatorID', required=True,
                            help="A creator ID for the interview is required, i.e. who created it?")
        parser.add_argument('participants', required=True,
                            help="A dictionary of participants in the interview is required, i.e. who took part?")
        parser.add_argument('prompts', required=True,
                            help="A dictionary of prompts that were selected during the interview is required")

        interview_session_id = uuid4().hex

        # TODO: we need to validate arguments, i.e. does that project/creator exist?
        args = parser.parse_args()
        # TODO: what if an error occurs in there? ABORT CAPTAIN
        self.__upload_interview_recording(args['recording'], interview_session_id, args['projectID'])

        interview_session = InterviewSession(
            # TODO: we send the UUID generated on the client, so why not use it?
            id=interview_session_id,
            creator_id=args['creatorID'],
            project_id=args['projectID']
        )

        interview_session.participants.extend(self.__add_participants(args['participants'], interview_session_id))
        interview_session.prompts.extend(self.__add_structural_prompts(args['prompts'], interview_session_id))

        db.session.add(interview_session)
        db.session.commit()

        # TODO: what if something went wrong along the way?
        return '', 201

    def __upload_interview_recording(self, recording, interview_id, project_id):
        """
        Upload the given interview file to S3

        :param recording:
        :return: A URL for the location of the file uploaded
        """
        from gabber.utils import amazon
        amazon.upload(recording, str(project_id) + "/" + str(interview_id))

    def __add_participants(self, participants, session_id):
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

        for p in json.loads(participants):
            known_user = User.query.filter_by(email=p['Email']).first()
            # e.g. someone interviewed a person who is not a Gabber user
            if not known_user:
                known_user = User(fullname=p['Name'], email=p['Email'], password="hi")
                # TODO: should they be made a member of the project once participated?
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
        prompts = json.loads(prompts)
        return [
            InterviewPrompts(
                prompt_id=p['PromptID'],
                interview_id=session_id,
                start_interval=p['Start'],
                end_interval=p['End']
            )
            for p in prompts
        ]
