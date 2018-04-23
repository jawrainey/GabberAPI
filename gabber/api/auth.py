# -*- coding: utf-8 -*-
"""
JWT configuration and authentication (registration, login and logout).
"""
from .. import db
from ..api.schemas.auth import AuthRegisterSchema, AuthLoginSchema, \
    ResetPasswordSchema, ForgotPasswordSchema, UserSchema, UserSchemaHasAccess
from ..models.user import User, ResetTokens
from ..utils.general import CustomException, custom_response
from ..utils import helpers
from flask import current_app as app
from flask_restful import Resource
from flask_jwt_extended import create_access_token, \
    create_refresh_token, jwt_refresh_token_required, get_jwt_identity, jwt_optional
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
import gabber.utils.email as email_client


def invalidate_other_user_tokens(email):
    """
    Once a request has been made to reset the password or the password was updated,
    then all previous tokens must be made invalid so they will not work again.
    """
    user = User.query.filter_by(email=email).first()
    user_tokens = ResetTokens.query.filter_by(user_id=user.id).all()
    for token in user_tokens:
        token.is_active = False
    db.session.commit()


class UserAsMe(Resource):
    """
    Mapped to: /api/auth/me/
    """
    @jwt_optional
    def get(self):
        """
        Returns the user details, such as fullname.
        If no user is logged in then data is empty.
        """
        user = User.query.filter_by(email=get_jwt_identity()).first()
        return custom_response(200, data=UserSchemaHasAccess().dump(user) if user else None)


class ForgotPassword(Resource):
    """
    Generates a unique magic-URL for a user to let them reset their password.
    Mapped to: /api/auth/forgot/
    """
    @staticmethod
    def post():
        """
        Send a user an email if they exist with a URL where they can reset their password.
        """
        data = helpers.jsonify_request_or_abort()
        helpers.abort_if_errors_in_validation(ForgotPasswordSchema().validate(data))

        email = data['email']
        user = User.query.filter_by(email=email).first()
        token = URLSafeTimedSerializer(app.config["SECRET_KEY"]).dumps(email, app.config['SALT'])
        invalidate_other_user_tokens(email)

        db.session.add(ResetTokens(token=token, user_id=user.id))
        db.session.commit()

        url = app.config['WEB_HOST'] + '/reset/' + token
        email_client.send_forgot_password(user, url)
        return custom_response(200)


class ResetPassword(Resource):
    """
    Given a magic-URL generates from /forgot/, lets a user reset their password if the token is active.

    Mapped to: /api/auth/reset/
    """
    def post(self):
        """
        Update a password for a user if the token is valid.
        """
        data = helpers.jsonify_request_or_abort()
        helpers.abort_if_errors_in_validation(ResetPasswordSchema().validate(data))

        email = self.serialize_token_or_abort(data['token'])
        user = User.query.filter_by(email=email).first()
        reset_token = self.abort_if_invalid_token(data['token'], user.id)

        user.set_password(data['password'])
        invalidate_other_user_tokens(email)

        reset_token.is_active = False
        db.session.add(user)
        db.session.commit()

        #email_client.send_password_changed(email)
        return custom_response(200, data=create_jwt_access(email))

    @staticmethod
    def abort_if_invalid_token(token, user_id):
        reset_token = ResetTokens.query.filter_by(token=token, user_id=user_id).first()
        if not reset_token or not reset_token.token:
            # The user has not requested a password reset
            raise CustomException(400, errors=['RESET_TOKEN_404'])
        elif not reset_token.is_active:
            # The user previously reset their password using this token
            raise CustomException(400, errors=['RESET_TOKEN_USED'])
        return reset_token

    def serialize_token_or_abort(self, token):
        serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
        try:
            email = serializer.loads(token, salt=app.config['SALT'], max_age=86400)  # one day expire time
        except SignatureExpired:
            email = serializer.loads(token, salt=app.config['SALT'])
            user = User.query.filter_by(email=email).first()
            # The token for this user has already been used.
            if user:
                reset_token = self.abort_if_invalid_token(token, user.id)
                reset_token.is_active = False
                db.session.commit()
            # The token expired and tried to be used again, so we must expire it.
            raise CustomException(400, errors=['RESET_TOKEN_EXPIRED'])
        except BadSignature:
            # All other potential errors, such as SECRET/SALTs not being set.
            raise CustomException(400, errors=['RESET_TOKEN_404'])
        return email


class TokenRefresh(Resource):
    """
    Refresh token endpoint. This will generate a new access token from
    the refresh token, but will mark that access token as non-fresh,
    as we do not actually verify a password in this endpoint.
    """
    @jwt_refresh_token_required
    def post(self):
        """
        Generates an access token given a refresh token

        Mapped to: /api/auth/token/refresh/

        :param: JWT refresh token
        :return: JWT Access token if a valid refresh token was provided
        """
        return {'access_token': create_access_token(identity=get_jwt_identity())}


class AuthToken:
    def __init__(self, **kwargs):
        self.token = URLSafeTimedSerializer(app.config["SECRET_KEY"]).dumps(kwargs, app.config['SALT'])

    @staticmethod
    def validate_token(token):
        """
        Validates that the token used to register an unconfirmed user is time valid.
        """
        serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
        try:
            data = serializer.loads(token, salt=app.config['SALT'], max_age=86400 * 7)  # one week
        except SignatureExpired:
            raise CustomException(400, errors=['AUTH_TOKEN_EXPIRED'])
        except BadSignature:
            raise CustomException(400, errors=['AUTH_TOKEN_404'])
        return data


class VerifyRegistration(Resource):
    """
    Mapped to: /api/auth/verify/<token>/
    """
    @staticmethod
    def post(token):
        """
        ??
        """
        token = AuthToken.validate_token(token)
        user = User.query.get(token['user_id'])
        # Rather than storing tokens, check if the user has been verified before
        if user.verified:
            return custom_response(400, errors=['ALREADY_VERIFIED'])
        user.verified = True
        db.session.commit()
        return custom_response(200, data=create_jwt_access(user.email))


class UserRegistration(Resource):
    """
    Mapped to: /api/auth/register/
    """
    @staticmethod
    def post():
        """
        Register a NEW user to Gabber and return JWT tokens
        """
        data = helpers.jsonify_request_or_abort()
        helpers.abort_if_errors_in_validation(AuthRegisterSchema().validate(data))
        user = User(fullname=data['fullname'], email=data['email'], password=data['password'], registered=True)

        known_user = User.query.filter_by(email=data['email']).first()
        if known_user:
            email_client.send_register_notification(known_user)
            return custom_response(200)
        else:
            db.session.add(user)
            db.session.commit()
            email_client.send_email_verification(user, AuthToken(user_id=user.id).token)

        return custom_response(201)


class UserLogin(Resource):
    """
    Mapped to: /api/auth/login/
    """
    @staticmethod
    def post():
        """
        Provide a user with JWT access/refresh tokens to use other aspects of API
        """

        data = helpers.jsonify_request_or_abort()
        helpers.abort_if_errors_in_validation(AuthLoginSchema().validate(data))
        return custom_response(200, data=create_jwt_access(data['email']))


def create_jwt_access(username):
    """
    Creates JWT access for a given user. Abstracted to a method to share between registration/login.
    :param username: the user to create access for
    :return: a dictionary containing JWT access/refresh tokens
    """
    return {
        'user': UserSchemaHasAccess().dump(User.query.filter_by(email=username).first()),
        'tokens': {
            'access': create_access_token(identity=username),
            'refresh': create_refresh_token(identity=username)
        }
    }
