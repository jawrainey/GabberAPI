from gabber import ma, db
# TODO: this should help simplify refactoring
from gabber.projects.models import \
    Connection as UserAnnotations, \
    Code as Tags, \
    ConnectionComments as Comments
from marshmallow import pre_load
from gabber.api.schemas.project import HelperSchemaValidator, validate_length


class UserAnnotationTagSchema(ma.ModelSchema):
    class Meta:
        model = Tags
        dateformat = "%d-%b-%Y"
        exclude = ['codebook', 'connections']


class UserAnnotationCommentSchema(ma.ModelSchema):
    creator = ma.Method("_creator")
    parent_id = ma.Function(lambda data: data.parent_id)
    annotation_id = ma.Function(lambda data: data.connection.id)
    session_id = ma.Function(lambda data: data.connection.session_id)

    @staticmethod
    def _creator(data):
        return {'user_id': data.user.id, 'fullname': data.user.fullname}

    class Meta:
        model = Comments
        dateformat = "%d-%b-%Y"
        exclude = ['user', 'connection', 'parent']

    @pre_load()
    def __validate(self, data):
        validator = HelperSchemaValidator('USER_COMMENT')
        validator.validate('content', 'str', data)
        validate_length(data.get('content'), 1024, 'content', validator)
        validator.raise_if_errors()


class UserAnnotationSchema(ma.ModelSchema):
    """
    Current issues:
        1) tags is a list and cannot be replaced or the update does not work (since it does not know
        about the tags relationship); for now I have created labels from the tags attribute.
        2) comments have replies, which is a list of FKs rather than content. Due to the relationship,
        an infinite loop occurs when serialising itself.
    """
    labels = ma.Nested(UserAnnotationTagSchema, many=True, attribute="tags")
    comments = ma.Nested(UserAnnotationCommentSchema, many=True, attribute="comments")
    creator = ma.Method("_creator")

    @staticmethod
    def _creator(data):
        return {'user_id': data.user.id, 'fullname': data.user.fullname}

    class Meta:
        model = UserAnnotations
        include_fk = True
        dateformat = "%d-%b-%Y"
        exclude = ['interview', 'user', 'user_id']

    @staticmethod
    def validate_intervals(attribute, data, validator):
        if attribute not in data:
            validator.errors.append('%s_REQUIRED' % attribute)
        elif validator.is_not_int(data[attribute]):
            validator.errors.append('%s_IS_NOT_INT' % attribute)
        elif data[attribute] < 0:
            validator.errors.append('%s_MUST_BE_POSITIVE_INT' % attribute)
        else:
            return True

    @pre_load()
    def __validate(self, data):
        validator = HelperSchemaValidator('USER_ANNOTATIONS')

        validator.validate('content', 'str', data)
        validate_length(data.get('content'), 1024, 'CONTENT', validator)
        valid_start = self.validate_intervals('start_interval', data, validator)
        valid_end = self.validate_intervals('end_interval', data, validator)

        if valid_start and valid_end:
            if data['start_interval'] > data['end_interval']:
                validator.errors.append('START_BEFORE_END')

        # TODO: tags are currently optional
        if data.get('tags'):
            if validator.is_not_list(data['tags']):
                validator.errors.append('TAGS_IS_NOT_LIST')
            else:
                for tag in data['tags']:
                    if validator.is_not_int(tag):
                        validator.errors.append('TAG_IS_NOT_INT')

        validator.raise_if_errors()
