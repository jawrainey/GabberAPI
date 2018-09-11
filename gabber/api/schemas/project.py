from ... import ma
from ...models.projects import Project, ProjectLanguage, \
    TopicLanguage, Membership, Codebook, Code as Tags, Organisation
from ...models.language import SupportedLanguage
from ...models.user import User
from marshmallow import pre_load, ValidationError
from slugify import slugify


class ValidationErrorWithCustomErrorFormat(ValidationError):
    """
    Overriding ValidationError (used as default Schema validator) such that
    a list of custom error messages are returned rather than auto generated.

    This means that the default error message dict can be overridden as below.
    """
    def normalized_messages(self, no_field_name=None):
        return self.messages


def validate_length(item, length, attribute, validator):
    if item and len(item) >= length:
        validator.errors.append('%s_LENGTH_TOO_LONG' % attribute)


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
            self.errors.append('%s_KEY_REQUIRED' % attribute.upper())
        elif not data[attribute]:
            self.errors.append('%s_IS_EMPTY' % attribute.upper())
        elif _type == "str" and self.is_not_str(data[attribute]):
            self.errors.append('%s_IS_NOT_STRING' % attribute.upper())
        elif _type == "list" and self.is_not_list(data[attribute]):
            self.errors.append('%s_IS_NOT_LIST' % attribute.upper())
        elif _type == "int" and self.is_not_int(data[attribute]):
            self.errors.append('%s_IS_NOT_INT' % attribute.upper())
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
            errors = [('{}.{}'.format(self.caller, error)) for error in self.errors]
            raise ValidationErrorWithCustomErrorFormat(errors)


class TagsSchema(ma.ModelSchema):
    class Meta:
        model = Tags
        exclude = ['codebook', 'connections']


class CodebookSchema(ma.ModelSchema):
    tags = ma.Nested(TagsSchema, many=True, attribute="tags")

    class Meta:
        model = Codebook
        exclude = ['project']


class ProjectPostSchema(ma.Schema):
    image = ma.String()
    title = ma.String()
    description = ma.String()
    privacy = ma.String()
    topics = ma.List(ma.String())

    @pre_load()
    def __validate(self, data):
        validator = HelperSchemaValidator('projects')

        if not data.get('image', None):
            data['image'] = 'default'

        validator.validate('image', 'str', data)

        privacy_valid = validator.validate('privacy', 'str', data)
        if privacy_valid and data['privacy'] not in ['private', 'public']:
            validator.errors.append('PRIVACY_INVALID')

        supported_langs = [i.code for i in SupportedLanguage.query.all()]

        for language, content in data['content'].items():
            if language not in supported_langs:
                validator.errors.append("UNSUPPORTED_LANGUAGE")

            title_valid = validator.validate('title', 'str', content)
            if title_valid and ProjectLanguage.query.filter_by(slug=slugify(content['title'])).first():
                validator.errors.append("TITLE_EXISTS")

            validator.validate('description', 'str', content)

            validate_length(content.get('title'), 64, 'TITLE', validator)
            validate_length(content.get('description'), 768, 'DESCRIPTION', validator)

            topics_valid = validator.validate('topics', 'list', content)

            if topics_valid:
                for topic in content['topics']:
                    if validator.is_not_str(topic.get('text')):
                        validator.errors.append('TOPIC_IS_NOT_STRING')
                    if not topic:
                        validator.errors.append('TOPIC_IS_EMPTY')
                    if topic:
                        validate_length(topic.get('text'), 260, 'TOPIC', validator)

        validator.raise_if_errors()


class ProjectMember(ma.ModelSchema):
    id = ma.Int(attribute='id')
    project_id = ma.String(attribute='project.id')
    role = ma.String(attribute='role.name')
    user_id = ma.Int(attribute='user_id')
    fullname = ma.Function(lambda d: d.user.fullname if d.role.name == 'staff' else None)

    class Meta:
        model = Membership
        exclude = ['project', 'user']


class ProjectMemberWithAccess(ProjectMember):
    fullname = ma.String(attribute='user.fullname')
    email = ma.String(attribute='user.email')


class ProjectLanguageSchema(ma.ModelSchema):

    class Meta:
        model = ProjectLanguage
        include_fk = True
        exclude = ['content', 'project_id']


class TopicLanguageSchema(ma.ModelSchema):

    class Meta:
        model = TopicLanguage
        include_fk = True


class ProjectModelSchema(ma.ModelSchema):
    image = ma.Method("_from_amazon")
    content = ma.Method("_content_by_language")
    codebook = ma.Function(lambda o: CodebookSchema().dump(o.codebook.first()) if o.codebook.first() else None)
    members = ma.Method("_members")
    creator = ma.Method("_creator")
    organisation = ma.Method("_organisation")
    organisation_id = ma.Function(lambda d: d.organisation)
    creator_id = ma.Function(lambda d: d.creator)
    privacy = ma.Function(lambda obj: "public" if obj.is_public else "private")

    def __init__(self, **kwargs):
        """
        When Schema is created, it can optionally take a user_id, which is used
        to provide fullname/email for members of projects where the user is an admin/creator.
        """
        # Remove this as parent ModelSchema does not expect this argument
        self.user_id = kwargs.pop('user_id', None)
        # Need to initialise parent manually
        ma.ModelSchema.__init__(self,  **kwargs)

    @staticmethod
    def _content_by_language(data):
        """
        Groups content by language to simplify lookup by clients.

        Returns dict:
            {
                "en": {
                    title: "",
                    topics: {}
                },
                "it": {
                    ...
                }
            }
        """
        projects = ProjectLanguageSchema(many=True).dump(data.content)
        topics = TopicLanguageSchema(many=True).dump(data.topics)

        grouped_content = {}
        for project in projects:
            lang = SupportedLanguage.query.get(project['lang_id']).code
            grouped_content[lang] = project
            grouped_content[lang]['topics'] = [t for t in topics if t['lang_id'] == project['lang_id']]

        return grouped_content

    @staticmethod
    def _from_amazon(data):
        from ...utils import amazon
        return amazon.static_file_by_name(data.image)

    def _members(self, data):
        """
        Show the name/email of member of a project if the user making the request (well, to serialize the object)
        is an admin on the project or they are the creator of a project.
        """
        if self.user_id:
            is_creator = data.creator == self.user_id
            users_role = User.query.get(self.user_id).role_for_project(data.id)
            if users_role in ['administrator', 'researcher'] or is_creator:
                return ProjectMemberWithAccess(many=True).dump(data.members)
        # We must show the names if they are a researcher
        return [ProjectMemberWithAccess().dump(member)
                if member.role.name == 'researcher'
                else ProjectMember().dump(member)
                for member in data.members]

    @staticmethod
    def _creator(data):
        user = User.query.get(data.creator)
        return {'user_id': user.id, 'fullname': user.fullname}

    @staticmethod
    def _organisation(data):
        org = Organisation.query.get(data.organisation)
        return {'id': org.id, 'name': org.name, 'description': org.description}

    class Meta:
        model = Project
        # We include FKs to gain access to Topics, Creator and Members
        include_fk = True
        exclude = ['prompts']

    @pre_load
    def __validate(self, data):
        # Note: currently, all content comes up at once for all languages.
        validator = HelperSchemaValidator('projects')

        pid_valid = validator.validate('id', 'int', data)

        if pid_valid and data['id'] not in [p.id for p in Project.query.with_deleted().all()]:
            validator.errors.append("ID_404")
            pid_valid = False

        # This must be a known user, and must be a member of this project
        creator_valid = validator.validate('creator', 'int', data)
        privacy_valid = validator.validate('privacy', 'str', data)

        if privacy_valid and data['privacy'] not in ['private', 'public']:
            validator.errors.append('PRIVACY_INVALID')
        else:
            # TODO: because the name is different, it does not update the model.
            data['is_public'] = data['privacy'] == 'public'

        supported_langs = [i.code for i in SupportedLanguage.query.all()]
        for language, content in data['content'].items():
            if language not in supported_langs:
                validator.errors.append("UNSUPPORTED_LANGUAGE")

            title_valid = validator.validate('title', 'str', content)
            title_as_slug = slugify(content['title'])
            validator.validate('description', 'str', content)

            if 'image' not in content and content.get('image', None):
                validator.errors.append('image_KEY_REQUIRED')
            if 'image' in content and len(content['image']) > 0 and not isinstance(content['image'], basestring):
                validator.errors.append('image_IS_NOT_STRING')

            validate_length(content.get('title'), 64, 'TITLE', validator)
            validate_length(content.get('description'), 768, 'DESCRIPTION', validator)

            if pid_valid and title_valid:
                # The title is different from the previous one, hence it changed.
                if ProjectLanguage.query.get(content['id']).slug != title_as_slug:
                    # The slug does not exist, so it is a unique new title
                    if ProjectLanguage.query.filter_by(slug=title_as_slug).first():
                        validator.errors.append("TITLE_EXISTS")
                    else:
                        # Note: this is not passed up and is always calculated in the backend
                        content['slug'] = title_as_slug

            topics_valid = validator.validate('topics', 'list', content)

            if topics_valid:
                for item in content['topics']:
                    if not isinstance(item, dict):
                        validator.errors.append('TOPICS_IS_NOT_DICT')
                    else:
                        if item.get('id'):
                            if 'is_active' not in item:
                                validator.errors.append('TOPICS_IS_ACTIVE_KEY_404')
                            else:
                                if not isinstance(item.get('is_active'), int):
                                    validator.errors.append('TOPICS_IS_ACTIVE_MUST_BE_INT')
                                elif item['is_active'] not in [0, 1]:
                                    validator.errors.append('TOPICS_IS_ACTIVE_MUST_BE_0_OR_1')

                            # Note: the ID will not appear as we implemented a primary join for only active sessions ...
                            all_project_topics = [i.id for i in TopicLanguage.query.filter_by(project_id=item['project_id']).all()]
                            if item.get('id') and (item['id'] not in all_project_topics):
                                validator.errors.append('TOPICS_ID_NOT_PROJECT')

                        # We do not check for ID as if it does not exist then a topic will be created
                        if not item.get('text'):
                            validator.errors.append('TOPICS_TEXT_KEY_404')
                        else:
                            if not isinstance(item['text'], basestring):
                                validator.errors.append('TOPICS_TEXT_IS_NOT_STRING')
                            else:
                                validate_length(content.get('text'), 260, 'TOPIC', validator)

        validator.raise_if_errors()
