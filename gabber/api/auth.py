# -*- coding: utf-8 -*-
"""
JWT configuration and authentication (registration, login and logout).
"""
from flask import url_for
from flask_restful import Resource
from flask_jwt_extended import create_access_token, \
    create_refresh_token, jwt_refresh_token_required, get_jwt_identity
from gabber import db, app
from gabber.api import helpers
from gabber.api.schemas.auth import AuthRegisterSchema, AuthLoginSchema, AuthRegisterWithTokenSchema, \
    ResetPasswordSchema, ForgotPasswordSchema
from gabber.projects.models import Membership
from gabber.users.models import User, ResetTokens
from gabber.utils.email import send_forgot_password, send_password_changed
from gabber.utils.general import CustomException, custom_response
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature


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
        if not reset_token or not reset_token.token:
            # The user has not requested a password reset
            raise CustomException(400, errors=['TOKEN_404'])
        elif not reset_token.is_active:
            # The user previously reset their password using this token
            raise CustomException(400, errors=['TOKEN_USED'])
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


class RegisterInvitedUser(Resource):
    """
    User accounts are created on behalf of participants in sessions to simplify onboarding.
    They receive an email with a magic-link (generated below) for account creation. This
    simplifies on-boarding and allows (1) that user to change fullname/email that was used
    when capturing the Gabber, and (2) association sessions, etc, with that user.

    Mapped to: /api/auth/register/<string:token>/
    """
    def get(self, token):
        """
        When a user completes a session an account is created on their behalf. This workflow
        allows Gabber to associate users as participants, and therefore their consent. However,
        they cannot create an account using traditional workflow, whereas this workflow (like Trello)
        returns the data they input into the mobile application, where they can edit it here. That way,
        all other instances of their participation (such as name) are updated to reflect the change.
        """
        return custom_response(201, data=self.validate_token(token))

    def put(self, token):
        """
        Registration process for non-registered users, i.e. those created through participating in sessions.
        """
        self.validate_token(token)
        data = helpers.jsonify_request_or_abort()
        helpers.abort_if_errors_in_validation(AuthRegisterWithTokenSchema().validate(data))

        user = User.query.filter_by(email=data['email']).first()
        if user.registered:
            return custom_response(400, errors=['ALREADY_REGISTERED'])
        user.fullname = data['fullname']
        user.email = data['email']
        user.registered = True

        # Better to ask for forgiveness: users can leave projects from the main page.
        for member in user.member_of.all():
            member.confirmed = True

        db.session.commit()

        return custom_response(201, data=create_jwt_access(data['email']))

    @staticmethod
    def generate_url(user_fullname, user_email, project_id, url):
        """
        Generates a time serialized URL that will last for one week (see validation below). The data attributes
        of the user registering for the first time are embedded within it (fullname, email and associated project).
        """
        properties = {'fullname': user_fullname, 'email': user_email, 'project_id': project_id}
        token = URLSafeTimedSerializer(app.config["SECRET_KEY"]).dumps(properties, app.config['SALT'])
        # Do not store tokens as (1) when the user registers we have confirmation of that, and (2) token expires.
        return url_for('api.%s' % url, token=token, _external=True)

    @staticmethod
    def validate_token(token):
        """
        Validates that the token used to register an unconfirmed user is time valid.
        TODO: this and generate_url could be abstracted to share code between the consent process and share URLs.
        """
        serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
        try:
            data = serializer.loads(token, salt=app.config['SALT'], max_age=86400 * 7)  # one week
        except SignatureExpired:
            raise CustomException(400, errors=['TOKEN_EXPIRED'])
        except BadSignature:
            raise CustomException(400, errors=['TOKEN_404'])
        return data


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
        db.session.add(User(fullname=data['fullname'], email=data['email'], password=data['password']))
        db.session.commit()
        return custom_response(201, data=create_jwt_access(data['email']))


class LoginInvitedUser(Resource):
    """
    Mapped to: /api/auth/login/<token>/
    """
    @staticmethod
    def put(token):
        """
        When a user receives an invite, they may already have a Gabber account with a different email.
        This lets a user login with another registered account and adds them as a member to the project.
        """
        data = helpers.jsonify_request_or_abort()
        helpers.abort_if_errors_in_validation(AuthLoginSchema().validate(data))
        token_data = RegisterInvitedUser.validate_token(token)
        # The email did not changed, so the membership invite remains associated with the other member.
        if data['email'] == token_data['email']:
            return custom_response(201, data=create_jwt_access(data['email']))
        # Conversely, the user tried to login with a different email, now we must update the membership invite.
        invited_user = User.query.filter_by(email=token_data['email'])
        # The membership of the invite sent, i.e. to a different email the user received.
        membership = Membership.query.filter_by(
            user_id=invited_user.first().id,
            project_id=token_data['project_id']).first()
        # Given they're logging in with a different account, we must associate the sent membership with this email.
        existing_user = User.query.filter_by(email=data['email']).first()
        membership.user_id = existing_user.id
        membership.confirmed = True
        # The user who was previously invited is removed as an invited member.
        invited_user.delete()
        db.session.commit()
        return custom_response(201, data=create_jwt_access(data['email']))

    @staticmethod
    def get(token):
        """
        Retrieves User/Project details associated with the invite token, e.g. fullname, email, project_id
        """
        return custom_response(201, data=RegisterInvitedUser.validate_token(token))


class UserLogin(Resource):
    """
    Mapped to: /api/auth/login/
    """
    @staticmethod
    def post():
        """
        Provide a user with JWT access/refresh tokens to use other aspects of API
        """
        # If token exists, then get the email from token ...
        # if the email is different

        data = helpers.jsonify_request_or_abort()
        helpers.abort_if_errors_in_validation(AuthLoginSchema().validate(data))
        return custom_response(201, data=create_jwt_access(data['email']))


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
