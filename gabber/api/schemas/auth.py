from ... import ma
from ...models.user import User
from ...models.language import SupportedLanguage
from ...api.schemas.project import HelperSchemaValidator
from marshmallow import pre_load, validate, ValidationError


def validate_email(email, errors):
    try:
        # This is required as a ValidationError would be raised if required=True
        # is set on a field, which annoyingly, returns a dictionary of errors where
        # the key is the field name. This is not suitable as we will return custom
        # error codes from the API instead. We use the same validator that fields uses,
        # but catch, suppress and log the error to our custom error list. Neat.
        validate.Email().__call__(email)
    except ValidationError:
        errors.append("EMAIL_INVALID")


def known_users():
    return [user.email.lower() for user in User.query.all()]


def validate_password_length(is_valid, attribute, errors):
    if is_valid and len(attribute) <= 12:
        errors.append("PASSWORD_LENGTH")


def validate_password(data, validator):
    password_valid = validator.validate('password', 'str', data)


class ForgotPasswordSchema(ma.Schema):
    email = ma.String()

    @pre_load()
    def __validate(self, data):
        validator = HelperSchemaValidator('auth')
        email_valid = validator.validate('email', 'str', data)

        if email_valid:
            validate_email(data['email'], validator.errors)
        validator.raise_if_errors()


class ResetPasswordSchema(ma.Schema):
    token = ma.String()
    password = ma.String()

    @pre_load()
    def __validate(self, data):
        validator = HelperSchemaValidator('auth')
        token_valid = validator.validate('token', 'str', data)
        # TODO: VALIDATE PASSWORD LENGTH: currently there is no upper/lower limit
        validate_password(data, validator)
        validator.raise_if_errors()


class AuthLoginSchema(ma.Schema):
    email = ma.String()
    password = ma.String()

    @pre_load()
    def __validate(self, data):
        validator = HelperSchemaValidator('auth')

        email_valid = validator.validate('email', 'str', data)

        if email_valid:
            validate_email(data['email'].lower(), validator.errors)

        if not validator.errors and data['email'].lower() not in known_users():
            validator.errors.append("USER_404")

        validate_password(data, validator)

        if not validator.errors:
            user = User.query.filter_by(email=data['email'].lower()).first()
            if user and not user.is_correct_password(data['password']):
                validator.errors.append("INVALID_PASSWORD")
            if not user.verified:
                validator.errors.append("UNVERIFIED_USER")
        validator.raise_if_errors()


class AuthRegisterSchema(ma.Schema):
    fullname = ma.String()
    email = ma.String()
    password = ma.String()
    lang = ma.Int()

    @pre_load()
    def __validate(self, data):
        validator = HelperSchemaValidator('auth')

        fullname_valid = validator.validate('fullname', 'str', data)
        email_valid = validator.validate('email', 'str', data)
        lang_valid = validator.validate('lang', 'int', data)

        if lang_valid:
            is_lang = SupportedLanguage.query.get(data['lang'])
            if not is_lang:
                validator.errors.append("INVALID_PREFERRED_LANGUAGE")

        if email_valid:
            validate_email(data['email'].lower(), validator.errors)

        validate_password(data, validator)
        validator.raise_if_errors()


class UserSchemaHasAccess(ma.ModelSchema):
    class Meta:
        model = User
        include_fk = True
        exclude = ['connection_comments', 'connections', 'password', 'member_of']

    @pre_load()
    def __validate(self, data):
        validator = HelperSchemaValidator('auth')

        if data.get('lang', None) and not SupportedLanguage.query.get(data['lang']):
            validator.errors.append("INVALID_PREFERRED_LANGUAGE")

        validator.raise_if_errors()
