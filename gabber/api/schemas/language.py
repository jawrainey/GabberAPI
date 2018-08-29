from gabber.models.language import SupportedLanguage
from gabber import ma


class SupportedLanguageSchema(ma.ModelSchema):
    class Meta:
        model = SupportedLanguage
