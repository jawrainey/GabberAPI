from gabber.projects.models import InterviewSession, InterviewParticipants, Connection, InterviewPrompts, ProjectPrompt
from gabber.users.models import User
from gabber import ma


class RecordingTopicSchema(ma.ModelSchema):
    topic_id = ma.String(attribute="prompt_id")
    text = ma.Method('_topic')
    start = ma.String(attribute="start_interval")
    end = ma.String(attribute="end_interval")

    @staticmethod
    def _topic(data):
        return ProjectPrompt.query.get(data.prompt_id).text_prompt

    class Meta:
        model = InterviewPrompts
        include_fk = True
        exclude = ['interview', 'start_interval', 'end_interval', 'interview_id', 'prompt_id', 'id']


class RecordingParticipantsSchema(ma.ModelSchema):
    user_id = ma.Function(lambda obj: User.query.get(obj.user_id).id)
    fullname = ma.Function(lambda obj: User.query.get(obj.user_id).fullname)
    # NOTE/TODO: not sure how best to represent the role of a participant in a Gabber
    role = ma.Function(lambda obj: "interviewer" if obj.role else "interviewee")

    class Meta:
        model = InterviewParticipants
        exclude = ['id', 'interview', 'consent_type']


class SessionAnnotationSchema(ma.ModelSchema):
    user_id = ma.Function(lambda annotation: annotation.user_id)
    session_id = ma.Function(lambda annotation: annotation.session_id)

    class Meta:
        model = Connection
        exclude = ['user', 'interview']
        dateformat = "%d-%b-%Y"


class RecordingSessionSchema(ma.ModelSchema):
    topics = ma.Nested(RecordingTopicSchema, many=True, attribute="prompts")
    participants = ma.Nested(RecordingParticipantsSchema, many=True, attribute="participants")
    user_annotations = ma.Nested(SessionAnnotationSchema, many=True, attribute="connections")
    audio_url = ma.Function(lambda s: s.generate_signed_url_for_recording())
    creator = ma.Method("_creator")

    @staticmethod
    def _creator(data):
        # TODO: method is the same as ProjectSchema
        user = User.query.get(data.creator_id)
        return {'user_id': user.id, 'fullname': user.fullname}

    class Meta:
        model = InterviewSession
        include_fk = True
        exclude = ['prompts', 'creator_id', 'connections']
        dateformat = "%d-%b-%Y"
