# -*- coding: utf-8 -*-
"""
Consent validation Schemas
"""
from ...api.schemas.project import HelperSchemaValidator
from ... import ma
from marshmallow import pre_load


class ConsentType(ma.Schema):
    type = ma.String()

    @pre_load()
    def __validate(self, data):
        validator = HelperSchemaValidator('consent')

        valid_type = validator.validate('consent', 'str', data)

        if valid_type:
            if data['consent'] not in ['private', 'members', 'public']:
                validator.errors.append("INVALID_VALUE")

        validator.raise_if_errors()
