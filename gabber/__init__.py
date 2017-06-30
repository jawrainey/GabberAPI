from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_mail import Mail
from flask_migrate import Migrate
import os

# Required when deploying to dokku @OpenLab
PROXY_PATH = os.getenv('PROXY_PATH', '/')
# Share static path behind proxy across all blueprints

templates = os.path.join(os.pardir, 'frontend/templates')
static_path = os.path.join(os.pardir, 'frontend/static')
static_url_path=os.path.join(PROXY_PATH, 'static')
app = Flask(__name__, template_folder=templates, static_url_path=static_url_path, static_folder=static_path)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)

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
app.config['IMG_FOLDER'] = os.path.join(static_path, 'img/')

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME', '')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD', '')
app.config['MAIL_DEFAULT_SENDER'] = app.config['MAIL_USERNAME']
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True

db = SQLAlchemy(app)
mail = Mail(app)
migrate = Migrate(app, db)

from gabber.main.views import main
app.register_blueprint(main, url_prefix=PROXY_PATH)
from gabber.api.views import api
app.register_blueprint(api, url_prefix=os.path.join(PROXY_PATH, 'api/'))
from gabber.users.views import users
app.register_blueprint(users, url_prefix=PROXY_PATH)
from gabber.projects.views import project
app.register_blueprint(project, url_prefix=os.path.join(PROXY_PATH, 'project/'))
from gabber.consent.views import consent
app.register_blueprint(consent, url_prefix=PROXY_PATH)

# Model meta-data required to create db correctly
if not os.path.exists(dbp):
    db.create_all()

from gabber.users.models import Anonymous
login_manager.anonymous_user = Anonymous

