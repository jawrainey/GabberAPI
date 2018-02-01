from gabber.users.models import User
from flask import url_for, Markup
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField
from wtforms.validators import DataRequired, Length, Email, ValidationError


class SignupForm(FlaskForm):
    name = StringField('Name', [DataRequired(), Length(min=4, max=20)])

    email = StringField('Email: ', [DataRequired(
        message='An email address must be provided.'),
        Email(),
        Length(min=6, max=90)])

    password = PasswordField('Password', [DataRequired(
        message='A password must be provided.'),
        Length(min=6, max=40)])

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            login = "<a href=" + url_for('users.login') + ">login</a>"
            recover = "<a href=" + url_for('users.forgot') + ">recover</a>"
            output = Markup("This email is already registered. Want to " + login + ' or ' + recover + ' your password?')
            raise ValidationError(output)


class LoginForm(FlaskForm):
    email = StringField('Email: ', [DataRequired(
        message='An email address must be provided.'),
        Email(),
        Length(min=3, max=90)])
    password = PasswordField('Password', [DataRequired(
        message='A password must be provided.'),
        Length(min=4, max=40)])

    def validate(self):
        if not FlaskForm.validate(self):
            return False

        user = User.query.filter_by(email=self.email.data.lower()).first()

        if not user:
            self.email.errors.append('Unknown email provided.')

        if user and not user.is_correct_password(self.password.data):
            self.password.errors.append('Invalid password provided.')

        if self.email.errors or self.password.errors:
            return False
        return True
