from QnA import db
from werkzeug.security import generate_password_hash, check_password_hash

class DocumentUploads(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    userID = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    originalName = db.Column(db.String(256), nullable=False)
    databaseName = db.Column(db.String(110), nullable=False)
    pages = db.relationship('Pages', backref='document', lazy=True)
    
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(256), nullable=False)
    documentUploads = db.relationship('DocumentUploads', backref='user', lazy=True)
    
    def set_password(self, password):
        self.password = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password, password)
    
class Pages(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    documentID = db.Column(db.Integer, db.ForeignKey('document.id'), nullable=False)
    pageNo = db.Column(db.Integer, nullable=False)
    databaseName = db.Column(db.String(110), nullable=False)
    extractedImages = db.relationship('ExtractedImages', backref='pages', lazy=True)
    
class ExtractedImages(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    pageID = db.Column(db.Integer, db.ForeignKey('pages.id'), nullable=False)
    databaseName = db.Column(db.String(110), nullable=False)
    topX = db.Column(db.Integer, nullable=False)
    topY = db.Column(db.Integer, nullable=False)
    bottomX = db.Column(db.Integer, nullable=False)
    bottomY = db.Column(db.Integer, nullable=False)
    question = db.relationship('Questions', uselist=False, backref='image')
    answer = db.relationship('Answers', uselist=False, backref='image')
    

    
