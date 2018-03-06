from gabber.projects.models import InterviewSession, InterviewParticipants, Connection, InterviewPrompts, ProjectPrompt
from gabber.users.models import User
from gabber import ma


class RecordingTopicSchema(ma.ModelSchema):
    text = ma.Method('_topic')
    start = ma.String(attribute="start_interval")
    end = ma.String(attribute="end_interval")

    @staticmethod
    def _topic(data):
        return ProjectPrompt.query.get(data.prompt_id).text_prompt

    class Meta:
        model = InterviewPrompts
        exclude = ['interview', 'start_interval', 'end_interval']


class RecordingParticipantsSchema(ma.ModelSchema):
    user_id = ma.Function(lambda obj: User.query.get(obj.user_id).id)
    name = ma.Function(lambda obj: User.query.get(obj.user_id).fullname)
    # NOTE/TODO: not sure how best to represent the role of a participant in a Gabber
    role = ma.Function(lambda obj: "interviewer" if obj.role else "interviewee")

    class Meta:
        model = InterviewParticipants
        exclude = ['id', 'interview', 'consent_type']


class SessionAnnotationSchema(ma.ModelSchema):
    class Meta:
        model = Connection
        dateformat = "%d-%b-%Y"


class RecordingSessionSchema(ma.ModelSchema):
    topics = ma.Nested(RecordingTopicSchema, many=True, attribute="prompts")
    participants = ma.Nested(RecordingParticipantsSchema, many=True, attribute="participants")
    user_annotations = ma.Nested(SessionAnnotationSchema, many=True, attribute="connections")
    creator = ma.Method("_creator")

    @staticmethod
    def _creator(data):
        user = User.query.get(data.creator_id)
        return {'id': user.id, 'name': user.fullname}

    class Meta:
        model = InterviewSession
        include_fk = True
        exclude = ['prompts', 'project_id', 'creator_id', 'connections']
        dateformat = "%d-%b-%Y"
