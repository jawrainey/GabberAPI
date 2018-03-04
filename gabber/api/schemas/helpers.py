from marshmallow import ValidationError


def is_not_empty(data, message):
    if not data or len(data) <= 0:
        raise ValidationError(message)
