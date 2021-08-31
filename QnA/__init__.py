from flask import Flask
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_session import Session
from werkzeug.middleware.proxy_fix import ProxyFix

app = Flask(__name__)
app.config['SECRET_KEY'] = "chuucandoitificandoit"
app.config['EXTRACTED'] = 'static/extracted'
app.config['UPLOAD'] = 'static/upload'
app.config['PAGES'] = 'static/pages'

Bootstrap(app)

app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///app.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False # Optimisation
app.config['SQLALCHEMY_ECHO'] = False # See all sql statements that are being run

db = SQLAlchemy(app)

app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = False

sess = Session()
sess.init_app(app)
''' 
Session object stores:
{
  edit: {
      curPageNum: current page number in editor
      curDoc: document object of current file
      curAnnotations: {
        pageID: []
      }
  }
  tag: {
      documentID
      croppedImages
      pageNum
  }
}

'''

app.wsgi_app = ProxyFix(app.wsgi_app)


from QnA import views, models
from QnA import clean