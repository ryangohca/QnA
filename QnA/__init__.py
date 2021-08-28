from flask import Flask
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_session import Session

app = Flask(__name__)
app.config['EXTRACTED'] = 'static/extracted'
app.config['UPLOAD'] = 'static/upload'
app.config['PAGES'] = 'static/pages'

Bootstrap(app)

app.secret_key = "chuucandoitificandoit"
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///app.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False # Optimisation
app.config['SQLALCHEMY_ECHO'] = True # See all sql statements that are being run
db = SQLAlchemy(app)

app.config["SESSION_TYPE"] = "sqlachemy"
app.config["SESSION_SQLACHEMY"] = db

session = Session(app)

from QnA import views, models