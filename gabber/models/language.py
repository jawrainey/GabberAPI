# -*- coding: utf-8 -*-
"""
Models the supported languages for the platform
"""
from .. import db


class SupportedLanguage(db.Model):
    """
    The supported languages for the platform

    id: used when associating with other models (i.e. projects)
    code: the ISO code that represents a language (it, en, de, etc.)
    iso_name: the language name in English (it => Italian)
    endonym: the native language name (it => Italiano)
    """
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(6))
    iso_name = db.Column(db.String(40))
    endonym = db.Column(db.String(1028))

    @staticmethod
    def codes():
        # We must unpack the tuple from the one column require
        return [code[0] for code in db.session.query(SupportedLanguage.code).all()]
