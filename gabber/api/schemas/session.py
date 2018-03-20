from gabber.projects.models import InterviewSession, InterviewParticipants, Connection, InterviewPrompts
from gabber import ma


class RecordingTopicSchema(ma.ModelSchema):
    topic_id = ma.Int(attribute="prompt_id")
    text = ma.String(attribute='topic.text_prompt')

    class Meta:
        model = InterviewPrompts
        include_fk = True
        exclude = ['interview', 'interview_id', 'prompt_id']


class RecordingParticipantsSchema(ma.ModelSchema):
    user_id = ma.String(attribute='user.id')
    fullname = ma.String(attribute='user.fullname')
    role = ma.String(attribute='role_type')

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

    class Meta:
        model = InterviewSession
        include_fk = True
        exclude = ['prompts', 'creator_id', 'connections']


class RecordingSessionSchema(RecordingSessionsSchema):
    audio_url = ma.Function(lambda s: s.generate_signed_url_for_recording())
