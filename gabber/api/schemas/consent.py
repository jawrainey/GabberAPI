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
        # TODO: consent must be in the list ...
        valid_type = validator.validate('type', 'str', data)

        if valid_type:
            if data['type'] not in ['none', 'private', 'public']:
                validator.errors.append("INVALID_TYPE_VALUE")

        validator.raise_if_errors()
