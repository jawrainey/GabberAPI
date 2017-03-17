from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import current_user, login_user, login_required, logout_user
from gabber.users.forms import LoginForm
from gabber.users.models import User
from gabber import login_manager

users = Blueprint('users', __name__)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)


@users.route('login/', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('users.dashboard'))

    form = LoginForm()

    if form.validate_on_submit():
        login_user(User.query.filter_by(username=form.email.data).first())
        return redirect(url_for('users.dashboard'))
    return render_template('views/users/login.html', form=form)


@users.route('logout/', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))


@users.route('dashboard/', methods=['GET'])
@login_required
def dashboard():
    if current_user.get_role() == 'admin':
        return render_template('views/users/dashboard.html', projects=current_user.projects)
    return redirect(url_for('main.projects'))
