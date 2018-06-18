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
        validator = HelperSchemaValidator('membership')
        fullname_valid = validator.validate('fullname', 'str', data)
        email_valid = validator.validate('email', 'str', data)
        role_valid = validator.validate('role', 'str', data)
        if role_valid and data['role'] not in ['participant', 'researcher', 'administrator']:
            validator.errors.append("INVALID_ROLE")

        if email_valid:
            validate_email(data['email'], validator.errors)
        validator.raise_if_errors()


class ProjectInviteWithToken(ma.Schema):
    fullname = ma.String()
    password = ma.String()

    @pre_load()
    def __validate(self, data):
        validator = HelperSchemaValidator('membership')
        fullname_valid = validator.validate('fullname', 'str', data)
        validator.raise_if_errors()
