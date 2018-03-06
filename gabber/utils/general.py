from flask import jsonify
from gabber import app


Consistent API responses and serialisation of some endpoints
-
- Added `CustomException`, which allows helper methods and resources to raise errors that are formatted in the same as a normal response, i.e. using the new `create_response` method.

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
            "data": data or [],
            "meta": {
                "success": status_code in [200, 201, 204],
                "errors": errors or []
            }
        }
    )
    response.status_code = status_code
    return response


@app.errorhandler(CustomException)
def handle_error(e):
    """
    Create a custom response for resource endpoints; this simplifies how data can be directly
    returned from within endpoint, and from within helper classes who can raise errors immediately.
    """
    return custom_response(e.status_code, data=e.data, errors=e.errors)