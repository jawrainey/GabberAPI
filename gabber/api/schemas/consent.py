# -*- coding: utf-8 -*-
"""
Consent validation Schemas
"""
from gabber.api.schemas.project import HelperSchemaValidator
from gabber import ma
from marshmallow import pre_load


class ConsentType(ma.Schema):
    type = ma.String()

    @pre_load()
    def __validate(self, data):
        validator = HelperSchemaValidator('CONSENT')

        valid_type = validator.validate('consent', 'str', data)

        if valid_type:
            if data['consent'] not in ['none', 'private', 'public']:
                validator.errors.append("INVALID_VALUE")

        validator.raise_if_errors()
