from gabber import ma
from gabber.users.models import User
from gabber.api.schemas.project import HelperSchemaValidator
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
        errors.append("INVALID_EMAIL")


def known_users():
    return [user.email for user in User.query.all()]


def validate_password_length(is_valid, attribute, errors):
    if is_valid and len(attribute) <= 12:
        errors.append("PASSWORD_LENGTH")


def validate_password(data, validator):
    password_valid = validator.validate('password', 'str', data)
    #
    # if password_valid:
    #     validate_password_length(password_valid, data['password'], validator.errors)


class ForgotPasswordSchema(ma.Schema):
    email = ma.String()

    @pre_load()
    def __validate(self, data):
        validator = HelperSchemaValidator('AUTH')
        email_valid = validator.validate('email', 'str', data)

        if email_valid:
            validate_email(data['email'], validator.errors)
        validator.raise_if_errors()


class ResetPasswordSchema(ma.Schema):
    token = ma.String()
    password = ma.String()

    @pre_load()
    def __validate(self, data):
        validator = HelperSchemaValidator('AUTH')
        token_valid = validator.validate('token', 'str', data)
        # TODO: VALIDATE PASSWORD LENGTH: currently there is no upper/lower limit
        validate_password(data, validator)
        validator.raise_if_errors()


class AuthLoginSchema(ma.Schema):
    email = ma.String()
    password = ma.String()

    @pre_load()
    def __validate(self, data):
        validator = HelperSchemaValidator('AUTH')

        email_valid = validator.validate('email', 'str', data)

        if email_valid:
            validate_email(data['email'], validator.errors)
        if data['email'] not in known_users():
            validator.errors.append("USER_DOES_NOT_EXIST")

        validate_password(data, validator)

        if not validator.errors:
            user = User.query.filter_by(email=data['email']).first()
            if user and not user.is_correct_password(data['password']):
                validator.errors.append("INVALID_PASSWORD")

        validator.raise_if_errors()


class AuthRegisterSchema(ma.Schema):
    fullname = ma.String()
    email = ma.String()
    password = ma.String()

    @pre_load()
    def __validate(self, data):
        validator = HelperSchemaValidator('AUTH')

        fullname_valid = validator.validate('fullname', 'str', data)
        email_valid = validator.validate('email', 'str', data)

        if email_valid:
            validate_email(data['email'], validator.errors)

        validate_password(data, validator)
        validator.raise_if_errors()


class AuthRegisterWithTokenSchema(ma.Schema):
    fullname = ma.String()
    email = ma.String()
    password = ma.String()

    @pre_load()
    def __validate(self, data):
        validator = HelperSchemaValidator('AUTH')

        fullname_valid = validator.validate('fullname', 'str', data)
        email_valid = validator.validate('email', 'str', data)

        if email_valid:
            validate_email(data['email'], validator.errors)

        validate_password(data, validator)
        validator.raise_if_errors()


class UserSchema(ma.ModelSchema):
    class Meta:
        model = User
        exclude = ['connection_comments', 'connections', 'password', 'member_of']

