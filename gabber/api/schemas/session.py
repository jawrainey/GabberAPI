from gabber.models.projects import InterviewSession, InterviewParticipants, Connection, InterviewPrompts
from gabber.models.user import User
from gabber import ma


class RecordingTopicSchema(ma.ModelSchema):
    topic_id = ma.Int(attribute="prompt_id")
    text = ma.String(attribute='topic.text')

    class Meta:
        model = InterviewPrompts
        include_fk = True
        exclude = ['interview', 'interview_id', 'prompt_id']


class RecordingParticipantsSchema(ma.ModelSchema):
    user_id = ma.Int(attribute='user.id')
    role = ma.Function(lambda member: 'interviewer' if member.role else 'interviewee')
    age = ma.Int(attribute='user.age')
    society = ma.Int(attribute='user.society')
    m_role = ma.Int(attribute='user.role')
    gender = ma.Int(attribute='user.gender')
    custom = ma.String(attribute='user.gender_custom')

    class Meta:
        model = InterviewParticipants
        exclude = ['id', 'interview', 'consent_type', 'user']


class SessionAnnotationSchema(ma.ModelSchema):
    user_id = ma.String(attribute='annotation.user_id')
    session_id = ma.String(attribute='annotation.session_id')

    class Meta:
        model = Connection
        exclude = ['user', 'interview']


class RecordingSessionsSchema(ma.ModelSchema):
    topics = ma.Nested(RecordingTopicSchema, many=True, attribute="prompts")
    participants = ma.Nested(RecordingParticipantsSchema, many=True, attribute="participants")
    num_user_annotations = ma.Function(lambda data: len(data.connections))
    creator = ma.Method("_creator")

    @staticmethod
    def _creator(data):
        user = User.query.get(data.creator_id)
        return {'user_id': user.id, 'fullname': user.fullname}

    class Meta:
        model = InterviewSession
        include_fk = True
        exclude = ['prompts', 'creator_id', 'connections', 'consents']


class RecordingSessionSchema(RecordingSessionsSchema):
    audio_url = ma.Function(lambda s: s.generate_signed_url_for_recording())
