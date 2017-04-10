from gabber.users.models import User
from flask_wtf import FlaskForm
from wtforms import TextField, PasswordField
from wtforms.validators import DataRequired, Length, Email


class LoginForm(FlaskForm):
    email = TextField('Email: ', [DataRequired(
        message='An email address must be provided.'),
        Email(),
        Length(min=3, max=90)])
    password = PasswordField('Password', [DataRequired(
        message='A password must provided.'),
        Length(min=4, max=40)])

    def validate(self):
        if not FlaskForm.validate(self):
            return False

        user = User.query.filter_by(username=self.email.data).first()

        if not user:
            self.email.errors.append('Unknown username provided.')

        if user and not user.is_correct_password(self.password.data):
            self.password.errors.append('Invalid password provided.')

        if self.email.errors or self.password.errors:
            return False
        return True
