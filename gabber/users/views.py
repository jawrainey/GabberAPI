from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import current_user, login_user, login_required, logout_user
from gabber.users.forms import LoginForm
from gabber.users.models import User
from gabber import login_manager

users = Blueprint('users', __name__)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)


@users.route('signup/', methods=['GET', 'POST'])
def signup():
    return render_template('views/users/signup.html', form=form)
@users.route('login/', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        flash('You are already logged in')
        return redirect(url_for('main.projects'))

    form = LoginForm()

    if form.validate_on_submit():
        login_user(User.query.filter_by(username=form.email.data.lower()).first())
        flash('You can view or edit your projects')
        return redirect(url_for('main.projects'))
    return render_template('views/users/login.html', form=form)


@users.route('logout/', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))


@users.route('forgot/', methods=['GET', 'POST'])
def forgot():
    return render_template('views/users/forgot.html', form=None)
