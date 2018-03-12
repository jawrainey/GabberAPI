# -*- coding: utf-8 -*-
"""
Membership validation Schemas
"""
from gabber.api.schemas.project import HelperSchemaValidator
from gabber.api.schemas.auth import validate_email
from gabber.users.models import User
from gabber import ma
from marshmallow import pre_load


def val_email(validator, data):
    """
    Helper method to simplify logic below
    """
    email_valid = validator.validate('email', 'str', data)

    if email_valid:
        validate_email(data['email'], validator.errors)
    validator.raise_if_errors()


class AddMemberSchema(ma.Schema):
    fullname = ma.String()
    email = ma.String()

    @pre_load()
    def __validate(self, data):
        validator = HelperSchemaValidator('MEMBERSHIP')
        fullname_valid = validator.validate('fullname', 'str', data)
        val_email(validator, data)
        validator.raise_if_errors()


class RemoveMemberSchema(ma.Schema):
    email = ma.String()

    @pre_load()
    def __validate(self, data):
        validator = HelperSchemaValidator('MEMBERSHIP')
        val_email(validator, data)
        if not validator.errors and data['email'] not in [user.email for user in User.query.all()]:
            validator.errors.append("USER_404")
        validator.raise_if_errors()
