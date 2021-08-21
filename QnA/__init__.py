from flask import Flask
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['EXTRACTED'] = 'extracted'
app.config['UPLOAD'] = 'upload'
app.config['PAGES'] = 'pages'

Bootstrap(app)

app.secretkey = "chuucandoitificandoit"
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///app.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False # Optimisation
app.config['SQLALCHEMY_ECHO'] = True # See all sql statements that are being run
db = SQLAlchemy(app)

from QnA import views, models