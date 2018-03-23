from flask import jsonify
from .. import jwt


@jwt.expired_token_loader
def jwt_expired(callback):
    return custom_response(400, errors=['JWT_EXPIRED'])


@jwt.invalid_token_loader
def jwt_invalid(callback):
    return custom_response(400, errors=['JWT_INVALID'])


@jwt.unauthorized_loader
def jwt_unauthorized(callback):
    return custom_response(400, errors=['JWT_UNAUTHORIZED'])


class CustomException(Exception):
    """
    This allows us to raise this exception within the API, which then
    feeds our custom body data to the error handler below.
    """
    def __init__(self, status_code=None, data=None, errors=None):
        Exception.__init__(self)
        self.status_code = status_code or 400
        self.data = data or []
        self.errors = errors or []


def custom_response(status_code, data=None, errors=None):
    """
    Creates a custom response to return to the user. This is used throughout the API
    when creating responses for the user, and when errors are thrown (see below).
    """
    response = jsonify(
        {
            "data": data,
            "meta": {
                "success": status_code in [200, 201, 204],
                "messages": errors or []
            }
        }
    )
    response.status_code = status_code
    return response
