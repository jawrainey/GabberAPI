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
            self.errors.append('%s_MUST_BE_STRING' % attribute)
        elif _type == "list" and self.is_not_list(data[attribute]):
            self.errors.append('%s_MUST_BE_LIST' % attribute)
        else:
            return True

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
                    validator.errors.append('TOPIC_MUST_BE_STRING')
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
    class Meta:
        model = ProjectPrompt
        dateformat = "%d-%b-%Y"


class ProjectModelSchema(ma.ModelSchema):
    """
    Simplify and keep
    """
    # Note: these are the same to support backwards comparability with Gabber mobile applications
    # TODO: remove prompts once tests are in place within the mobile application.
    topics = ma.Nested(ProjectTopicSchema, many=True, attribute="prompts")
    prompts = ma.Nested(ProjectTopicSchema, many=True, attribute="prompts")

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
        exclude = ['codebook']