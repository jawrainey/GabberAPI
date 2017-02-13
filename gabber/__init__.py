from flask import Flask
from flask.ext.login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_mail import Mail
import os

# Required when deploying to dokku. This would be
PROXY_PATH = os.getenv('PROXY_PATH', '/')
# Set the static path here as ...
# Set static path as it will remain the same throughout blueprints.
app = Flask(__name__, static_url_path=os.path.join(PROXY_PATH, 'static'))
bcrypt = Bcrypt(app)

login_manager = LoginManager(app)

app.debug = True
# This is where all the audio interviews will be stored -- root directory.
root = os.path.dirname(os.path.abspath(__file__))

xp = os.path.join(root, 'protected')
if not os.path.exists(xp):
    os.makedirs(xp)

dbp = os.path.join(xp, 'dati.db')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + dbp
app.config['SECRET_KEY'] = 'supersecretpasswordfromtheotherside'
app.config['UPLOAD_FOLDER'] = xp
app.config['SALT'] = 'supersecretsaltfromtheotherside'
app.config['PROXY_PATH'] = PROXY_PATH
app.config['IMG_FOLDER'] = os.path.join(root, 'static/img/')


# Gmail for simplicity of initial deployment.
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME', '')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD', '')
app.config['MAIL_DEFAULT_SENDER'] = app.config['MAIL_USERNAME']
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True

db = SQLAlchemy(app)
mail = Mail(app)

from gabber.views import main
app.register_blueprint(main, url_prefix=PROXY_PATH)
from gabber.api import api
app.register_blueprint(api, url_prefix=os.path.join(PROXY_PATH, 'api/'))
from gabber.users.views import users
app.register_blueprint(users, url_prefix=PROXY_PATH)
from gabber.users.views import users
app.register_blueprint(users, url_prefix=PROXY_PATH)

# Create the database afterwards as models meta-data required to populate it.
if not os.path.exists(dbp):
    db.create_all()
