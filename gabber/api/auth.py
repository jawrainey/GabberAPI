# -*- coding: utf-8 -*-
"""
JWT configuration and authentication (registration, login and logout).
"""
from flask import request, url_for
from gabber import db, app
from gabber.api import helpers
from gabber.api.schemas.auth import AuthRegisterSchema, AuthLoginSchema, ResetPasswordSchema, ForgotPasswordSchema
from gabber.utils.general import custom_response
from gabber.users.models import User, ResetTokens
from flask_restful import Resource
from flask_jwt_extended import create_access_token, \
    create_refresh_token, jwt_refresh_token_required, get_jwt_identity
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from gabber.utils.email import send_forgot_password, send_password_changed
from gabber.utils.general import CustomException


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
        helpers.abort_if_unknown_user(user)

        token = URLSafeTimedSerializer(app.config["SECRET_KEY"]).dumps(email, app.config['SALT'])
        invalidate_other_user_tokens(email)

        db.session.add(ResetTokens(token=token, user_id=user.id))
        db.session.commit()

        url = url_for('api.reset', token=token, _external=True)
        send_forgot_password(email, url)
        return custom_response(200, data={'reset_url': url})


class ResetPassword(Resource):
    """
    Given a magic-URL generates from /forgot/, lets a user reset their password if the token is active.

    Mapped to: /api/auth/reset/<string:token>/
    """
    def get(self, token):
        """
        This validates the token and returns meta-data about the user, which can
        be used to populate a form to improve or simplify the user experience.
        """
        email = self.serialize_token_or_abort(token)
        user = User.query.filter_by(email=email).first()
        self.abort_if_invalid_token(token, user.id)
        return custom_response(201, data={'email': email})

    def post(self, token):
        """
        Update a password for a user if the token is valid.
        """
        json_data = helpers.jsonify_request_or_abort()
        helpers.abort_if_errors_in_validation(ResetPasswordSchema().validate(json_data))

        email = self.serialize_token_or_abort(token)
        user = User.query.filter_by(email=email).first()
        reset_token = self.abort_if_invalid_token(token, user.id)

        user.set_password(json_data['password'])
        invalidate_other_user_tokens(email)

        reset_token.is_active = False
        db.session.add(user)
        db.session.commit()

        send_password_changed(email)
        return custom_response(201, data=create_jwt_access(email))

    @staticmethod
    def abort_if_invalid_token(token, user_id):
        reset_token = ResetTokens.query.filter_by(token=token, user_id=user_id).first()
        if not reset_token:
            raise CustomException(400, errors=['NOT_RESET'])
        elif not reset_token.token:
            # The user has not requested a password reset
            raise CustomException(400, errors=['TOKEN_404'])
        elif not reset_token.is_active:
            # The user previously reset their password using this token
            raise CustomException(400, errors=['TOKEN_USED'])
        return reset_token

    def serialize_token_or_abort(self, token):
        serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
        try:
            email = serializer.loads(token, salt=app.config['SALT'], max_age=100000)
        except SignatureExpired:
            email = serializer.loads(token, salt=app.config['SALT'])
            user = User.query.filter_by(email=email).first()
            # The token for this user has already been used.
            if user:
                reset_token = self.abort_if_invalid_token(token, user.id)
                reset_token.is_active = False
                db.session.commit()
            # The token expired and tried to be used again, so we must expire it.
            raise CustomException(400, errors=['TOKEN_EXPIRED'])
        except BadSignature:
            # All other potential errors, such as SECRET/SALTs not being set.
            raise CustomException(400, errors=['TOKEN_404'])
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


class UserRegistration(Resource):
    """
    Register a user to Gabber and return JWT tokens
    """
    @staticmethod
    def post():
        """
        Who would like to register and do they exist?

        Mapped to: /api/auth/register/
        """
        # TODO: could wrap the following until data to reduce bloat throughout?
        json_data = request.get_json(force=True, silent=True)
        helpers.abort_if_invalid_json(json_data)

        schema = AuthRegisterSchema()
        helpers.abort_if_errors_in_validation(schema.validate(json_data))

        data = schema.dump(json_data)

        db.session.add(User(data['email'], data['password'], data['fullname']))
        db.session.commit()

        return custom_response(201, data=create_jwt_access(data['email']))


class UserLogin(Resource):
    """
    Logging in a user
    """
    @staticmethod
    def post():
        """
        Provide a user with JWT access/refresh tokens to use other aspects of API

        Mapped to: /api/auth/login/
        """
        json_data = request.get_json(force=True, silent=True)
        helpers.abort_if_invalid_json(json_data)
        schema = AuthLoginSchema()
        helpers.abort_if_errors_in_validation(schema.validate(json_data))
        return custom_response(201, data=create_jwt_access(schema.dump(json_data)['email']))


def create_jwt_access(username):
    """
    Creates JWT access for a given user. Abstracted to a method to share between registration/login.
    :param username: the user to create access for
    :return: a dictionary containing JWT access/refresh tokens
    """
    return {
        'access_token': create_access_token(identity=username),
        'refresh_token': create_refresh_token(identity=username)
    }
