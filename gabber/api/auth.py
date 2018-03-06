# -*- coding: utf-8 -*-
"""
JWT configuration and authentication (registration, login and logout).
"""
from flask import request
from gabber import db
from gabber.api import helpers
from gabber.api.schemas.auth import AuthRegisterSchema, AuthLoginSchema
from gabber.utils.general import custom_response
from gabber.users.models import User
from flask_restful import Resource
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
