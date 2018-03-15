# -*- coding: utf-8 -*-
"""
Membership validation Schemas
"""
from gabber.api.schemas.project import HelperSchemaValidator
from gabber.api.schemas.auth import validate_email
from gabber import ma
from marshmallow import pre_load


class AddMemberSchema(ma.Schema):
    fullname = ma.String()
    email = ma.String()

    @pre_load()
    def __validate(self, data):
        validator = HelperSchemaValidator('MEMBERSHIP')
        fullname_valid = validator.validate('fullname', 'str', data)
        email_valid = validator.validate('email', 'str', data)

        if email_valid:
            validate_email(data['email'], validator.errors)
        validator.raise_if_errors()
