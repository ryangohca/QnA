from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from QnA import db, login

class DocumentUploads(db.Model):
    __tablename__ = 'documentUploads'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    userID = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    originalName = db.Column(db.String(256), nullable=False)
    databaseName = db.Column(db.String(110), nullable=False)
    percentageCompleted = db.Column(db.Integer, server_default=db.text('0'))
    pages = db.relationship('Pages', backref='documentUploads', lazy=True)
    answersToQns = db.relationship('Answers', backref='documentUploads', lazy=True)
    
class Users(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(256), nullable=False)
    documentUploads = db.relationship('DocumentUploads', backref='users', lazy=True)
    
    def set_password(self, password):
        self.password = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password, password)

class Pages(db.Model):
    __tablename__ = 'pages'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    documentID = db.Column(db.Integer, db.ForeignKey('documentUploads.id'), nullable=False)
    pageNo = db.Column(db.Integer, nullable=False)
    databaseName = db.Column(db.String(110), nullable=False)
    extractedImages = db.relationship('ExtractedImages', backref='pages', lazy=True)
    
class ExtractedImages(db.Model):
    __tablename__ = 'extractedImages'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    pageID = db.Column(db.Integer, db.ForeignKey('pages.id'), nullable=False)
    databaseName = db.Column(db.String(110), nullable=False)
    topX = db.Column(db.Integer, nullable=False)
    topY = db.Column(db.Integer, nullable=False)
    bottomX = db.Column(db.Integer, nullable=False)
    bottomY = db.Column(db.Integer, nullable=False)
    question = db.relationship('Questions', uselist=False, backref='extractedImages')
    answer = db.relationship('Answers', uselist=False, backref='image')
    
class Questions(db.Model):
    __tablename__ = 'questions'
    id = db.Column(db.Integer, db.ForeignKey('extractedImages.id'), primary_key=True, autoincrement=False)
    subject = db.Column(db.String(256), nullable=True)
    topic = db.Column(db.String(256), nullable=True)
    year = db.Column(db.Integer, nullable=True)
    paper = db.Column(db.String(256), nullable=True)
    questionNo = db.Column(db.Integer, nullable=True)
    questionPart = db.Column(db.String(5), nullable=True)
    
class Answers(db.Model):
    __tablename__ = 'answers'
    id = db.Column(db.Integer, db.ForeignKey('extractedImages.id'), primary_key=True, autoincrement=False)
    answerText = db.Column(db.String(256), nullable=True)
    questionDocumentID = db.Column(db.Integer, db.ForeignKey('documentUploads.id'), nullable=True)
    questionNo = db.Column(db.Integer, nullable=True)
    questionPart = db.Column(db.String(5), nullable=True)
  
@login.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))
  
def insert_dummy_user():
    dummy = Users(username='admin')
    dummy.set_password('admin')
    db.session.add(dummy)
    db.session.commit()
    
def refreshDb():
    db.drop_all()
    db.create_all()
    insert_dummy_user()
    
# refreshDb()