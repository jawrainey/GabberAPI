# -*- coding: utf-8 -*-
"""
JWT configuration and authentication (registration, login and logout).
"""
from gabber import db
from gabber.users.models import User
from flask_restful import Resource, reqparse, abort
from flask_jwt_extended import create_access_token, \
    create_refresh_token, jwt_refresh_token_required, get_jwt_identity


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

        :return: a dictionary containing JWT access/refresh tokens
        """
        parser = reqparse.RequestParser()
        parser.add_argument('fullname', required=True, help="The full name of a user is required when registering.")
        parser.add_argument('email', required=True, help="An email address is required (i.e. the username).")
        parser.add_argument('password', required=True, help="A password is required to register an account.")
        args = parser.parse_args()

        if not args['fullname']:
            abort(400, message='A fullname is required to register')
        if not args['email']:
            abort(400, message='An email address is required to register')
        if not args['password']:
            abort(400, message='A password is required to register')

        # TODO: rigorously validate user input?
        email = args['email']

        if email in [user.email for user in db.session.query(User.email)]:
            abort(400, message='An account with that email exists.')

        db.session.add(User(email, args['password'], args['fullname']))
        db.session.commit()

        return create_jwt_access(email)


class UserLogin(Resource):
    """
    Logging in a user
    """
    @staticmethod
    def post():
        """
        Provide a user with JWT access/refresh tokens to use other aspects of API

        Mapped to: /api/auth/login/

        :return: a dictionary containing JWT access/refresh tokens
        """
        parser = reqparse.RequestParser()
        parser.add_argument('email', required=True, help="An email address is required (i.e. the username).")
        parser.add_argument('password', required=True, help="A password is required to register an account.")
        args = parser.parse_args()
        # TODO: rigorously validate email/password?
        email = args['email']

        known_users = [user.email for user in db.session.query(User.email)]
        if email and email in known_users:
            user = User.query.filter_by(email=email).first()
            if user and user.is_correct_password(args['password']):
                return create_jwt_access(email)
            return abort(400, message='An incorrect password was provided for that user.')
        return abort(400, message='The email you provided is not a known user.')


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
