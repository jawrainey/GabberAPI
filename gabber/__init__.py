from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.bcrypt import Bcrypt

app = Flask(__name__)
bcrypt = Bcrypt(app)
app.debug = True

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + 'dati.db'
app.config['SECRET_KEY'] = 'supersecretpasswordfromtheotherside'

db = SQLAlchemy(app)

from gabber import views, models, api
