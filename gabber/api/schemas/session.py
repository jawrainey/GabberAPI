from ...models.projects import Project, InterviewSession, InterviewParticipants, Connection, InterviewPrompts, TopicLanguage
from ...models.user import User
from ...models.language import SupportedLanguage
from ... import ma


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
    num_user_annotations = ma.Function(lambda data: len([i.comments for i in data.connections]) + len(data.connections))
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


class Recommendation(ma.ModelSchema):
    participants = ma.Function(lambda data: len(data.participants))
    comments = ma.Function(lambda data: len([i.comments for i in data.connections]) + len(data.connections))
    pid = ma.String(attribute="project_id")
    image = ma.Method("_project_image_from_amazon")
    content = ma.Method("_project_title")
    societies = ma.Method("_socs")
    lang = ma.Function(lambda d: SupportedLanguage.query.get(d.lang_id).endonym)

    @staticmethod
    def _socs(data):
        return [User.query.get(p.user_id).society for p in data.participants]

    @staticmethod
    def _project_title(data):
        project = Project.query.get(data.project_id)
        return [{'title': p.title, 'lang': SupportedLanguage.query.get(p.lang_id).code} for p in project.content.all()]

    @staticmethod
    def _project_image_from_amazon(data):
        from ...utils import amazon
        project = Project.query.get(data.project_id)
        return amazon.static_file_by_name(project.image)

    class Meta:
        model = InterviewSession
        include_fk = True
        exclude = ['prompts', 'creator_id', 'connections', 'consents', 'created_on', 'lang_id']
