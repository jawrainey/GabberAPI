from gabber import ma
from marshmallow import ValidationError, validates_schema
from gabber.projects.models import ProjectPrompt


def is_known_topic(data):
    if data not in [i.id for i in ProjectPrompt.query.all()]:
        raise ValidationError("The topic with the ID (%i) does not exist" % data)


def required_message(attribute, parent):
    return "The %s for the %s is required." % (attribute, parent)


class RecordingAnnotationSchema(ma.Schema):
    Start = ma.Int(
        required=True,
        error_messages={'required': required_message('Start interval', 'region')}
    )
    End = ma.Int(
        required=True,
        error_messages={'required': required_message('End interval', 'region')}
    )
    PromptID = ma.Int(
        required=True,
        error_messages={'required': required_message('Topic ID known to Gabber', 'region')},
        validate=is_known_topic
    )

    @validates_schema
    def validate_region_range(self, data):
        if data['Start'] > data['End']:
            raise ValidationError('The start interval is greater than the end for topic (%s).' % data['PromptID'])

    class Meta:
        index_errors = False


class ParticipantScheme(ma.Schema):
    Name = ma.Str(
        required=True,
        error_messages={'required': required_message('Name of a participant', 'session')}
    )
    # TODO: for now this is a string as although we validate the participants email on the device,
    # some emails (such as w@w.w) are invalid, which means the session would not be uploaded.
    # Instead, we accept invalid emails for now, then we can determine (by asking the creator)
    # to verify these if they are invalid.
    Email = ma.Str(
        required=True,
        error_messages={'required': required_message('Email of a participant', 'session')}
    )
    Role = ma.Boolean(
        required=True,
        error_messages={'required': required_message('Role of a participant', 'session')}
    )

    class Meta:
        index_errors = False
