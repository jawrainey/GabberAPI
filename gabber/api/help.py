# -*- coding: utf-8 -*-
"""
Helper methods of the API that are useful to the applications, e.g. supported language, version, etc.
"""
from ..api.schemas.language import SupportedLanguageSchema
from ..models.language import SupportedLanguage
from ..utils.general import custom_response
from flask_restful import Resource


class SupportedLanguages(Resource):
    """
    Mapped to: /api/help/languages/
    """
    @staticmethod
    def get():
        """
        Provides details of a user (fullname & email) and the project (ID) they were invited to.
        """
        supported_languages = SupportedLanguage.query.order_by(SupportedLanguage.code).all()
        return custom_response(200, data=SupportedLanguageSchema(many=True).dump(supported_languages))
