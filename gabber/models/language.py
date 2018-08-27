# -*- coding: utf-8 -*-
"""
Models the supported languages for the platform
"""
from .. import db


class SupportedLanguage(db.Model):
    """
    The supported languages for the platform

    id: used when assoicating with other models (i.e. projects)
    code: the ISO code that represents a language (it, en, de, etc.)
    iso_name: the language name in English (it => Italian)
    endonum: the native language name (it => Italiano)
    """
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(6))
    iso_name = db.Column(db.String(40))
    endonym = db.Column(db.String(1028))
