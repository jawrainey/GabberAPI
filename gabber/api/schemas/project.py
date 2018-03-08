from gabber import ma
from slugify import slugify
from marshmallow import pre_load, ValidationError
from gabber.projects.models import Project, ProjectPrompt, Roles, Membership
from gabber.users.models import User


class ValidationErrorWithCustomErrorFormat(ValidationError):
    """
    Overriding ValidationError (used as default Schema validator) such that
    a list of custom error messages are returned rather than auto generated.

    This means that the default error message dict can be overridden as below.
    """
    def normalized_messages(self, no_field_name=None):
        return self.messages


class HelperSchemaValidator:
    """
    Contains general validation shared across schema: required, is empty, and type validation.
    """
    def __init__(self, name):
        """
        Initializes the errors messages

        :param name: the name of the schema using this helper, which is prepended to each error code.
        """
        self.caller = name
        self.errors = []

    def validate(self, attribute, _type, data):
        if attribute not in data:
            self.errors.append('%s_REQUIRED' % attribute)
        elif not data[attribute]:
            self.errors.append('%s_IS_EMPTY' % attribute)
        elif _type == "str" and self.is_not_str(data[attribute]):
            self.errors.append('%s_IS_NOT_STRING' % attribute)
        elif _type == "list" and self.is_not_list(data[attribute]):
            self.errors.append('%s_IS_NOT_LIST' % attribute)
        elif _type == "int" and self.is_not_int(data[attribute]):
            self.errors.append('%s_IS_NOT_INT' % attribute)
        else:
            return True

    @staticmethod
    def is_not_int(data):
        return not isinstance(data, int)

    @staticmethod
    def is_not_list(data):
        return not isinstance(data, list)

    @staticmethod
    def is_not_str(data):
        # Test against basestring as unicode is not supported in Python 2.7,
        # whereas basestring is the super-class of both unicode and str.
        return not isinstance(data, basestring)

    def raise_if_errors(self):
        if self.errors:
            errors = [('%s_%s' % (self.caller, error)).upper() for error in self.errors]
            raise ValidationErrorWithCustomErrorFormat(errors)


class ProjectPostSchema(ma.Schema):
    title = ma.String()
    description = ma.String()
    privacy = ma.String()
    topics = ma.List(ma.String())

    @pre_load()
    def __validate(self, data):
        validator = HelperSchemaValidator('PROJECTS')

        title_valid = validator.validate('title', 'str', data)
        if title_valid and Project.query.filter_by(slug=slugify(data['title'])).first():
            validator.errors.append("TITLE_EXISTS")

        validator.validate('description', 'str', data)

        privacy_valid = validator.validate('privacy', 'str', data)
        if privacy_valid and data['privacy'] not in ['private', 'public']:
            validator.errors.append('PRIVACY_INVALID')

        topics_valid = validator.validate('topics', 'list', data)

        if topics_valid:
            for topic in data['topics']:
                if validator.is_not_str(topic):
                    validator.errors.append('TOPIC_IS_NOT_STRING')
                if not topic:
                    validator.errors.append('TOPIC_IS_EMPTY')

        validator.raise_if_errors()


class ProjectMember(ma.ModelSchema):
    id = ma.Function(lambda member: User.query.get(member.user_id).id)
    name = ma.Function(lambda member: User.query.get(member.user_id).fullname)
    role = ma.Function(lambda member: Roles.query.get(member.role_id).name)

    class Meta:
        model = Membership
        dateformat = "%d-%b-%Y"
        exclude = ['project']


class ProjectTopicSchema(ma.ModelSchema):
    """
    No validation is done here as it's all done in ProjectModelSchema before serialization
    """
    text = ma.String(attribute="text_prompt")

    class Meta:
        model = ProjectPrompt
        include_fk = True
        dateformat = "%d-%b-%Y"
        exclude = ['text_prompt', 'image_path', 'project', 'is_active', 'creator']


class ProjectModelSchema(ma.ModelSchema):
    topics = ma.Nested(ProjectTopicSchema, many=True, attribute="prompts")
    members = ma.Nested(ProjectMember, many=True, attribute="members")
    creator = ma.Method("_creator")

    @staticmethod
    def _creator(data):
        user = User.query.get(data.creator)
        return {'id': user.id, 'name': user.fullname}

    class Meta:
        model = Project
        # We include FKs so that to gain access to Topics, Creator and Members
        include_fk = True
        dateformat = "%d-%b-%Y"
        # TODO: remove other attributes as necessary, i.e. isConsentEnabled and isProjectPublic?
        exclude = ['codebook', 'prompts']

    @pre_load()
    def __validate(self, data):
        validator = HelperSchemaValidator('PROJECTS')

        pid_valid = validator.validate('id', 'int', data)

        if pid_valid and data['id'] not in [p.id for p in Project.query.with_deleted().all()]:
            validator.errors.append("ID_404")
            pid_valid = False

        # This must be a known user, and must be a member of this project
        creator_valid = validator.validate('creator', 'int', data)
        # The property exists...
        if creator_valid:
            user = User.query.get(data['creator'])
            if user and pid_valid:
                if data['creator'] != Project.query.get(data['id']).creator:
                    validator.errors.append("UNAUTHORIZED")
            else:
                validator.errors.append("USER_404")

        title_valid = validator.validate('title', 'str', data)
        title_as_slug = slugify(data['title'])

        if pid_valid and title_valid:
            # The title is different from the previous one, hence it changed.
            if Project.query.get(data['id']).slug != title_as_slug:
                # The slug does not exist, so it is a unique new title
                if Project.query.with_deleted().filter_by(slug=title_as_slug).first():
                    validator.errors.append("TITLE_EXISTS")
                else:
                    # Note: this is not passed up and is always calculated in the backend
                    data['slug'] = title_as_slug

        validator.validate('description', 'str', data)

        privacy_valid = validator.validate('privacy', 'str', data)
        if privacy_valid and data['privacy'] not in ['private', 'public']:
            validator.errors.append('PRIVACY_INVALID')

        topics_valid = validator.validate('topics', 'list', data)

        if topics_valid:
            for item in data['topics']:
                if not isinstance(item, dict):
                    validator.errors.append('TOPICS_IS_NOT_DICT')
                else:
                    if 'is_active' not in item:
                        validator.errors.append('TOPICS_IS_ACTIVE_KEY_404')
                    else:
                        if not isinstance(item.get('is_active'), int):
                            validator.errors.append('TOPICS_IS_ACTIVE_MUST_BE_INT')
                        elif item['is_active'] not in [0, 1]:
                            validator.errors.append('TOPICS_IS_ACTIVE_MUST_BE_0_OR_1')

                    if item.get('id') and (item['id'] not in [i.id for i in Project.query.get(data['id']).prompts.all()]):
                        validator.errors.append('TOPICS_ID_NOT_PROJECT')

                    # We do not check for ID as if it does not exist then a topic will be created
                    if not item.get('text_prompt'):
                        validator.errors.append('TOPICS_TEXT_KEY_404')
                    else:
                        if not isinstance(item['text_prompt'], basestring):
                            validator.errors.append('TOPICS_TEXT_IS_NOT_STRING')

                # TODO: Rather than the user passing the creator to each topic, it is passed as a parent
                # and we manually add it here as the relationship between these schemas is void.
                if not validator.errors:
                    item['creator'] = data['creator']
                    item['project_id'] = data['id']

        validator.raise_if_errors()
