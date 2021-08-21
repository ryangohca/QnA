from QnA import db

class DocumentUploads(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    userID = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    originalName = db.Column(db.String(256), nullable=False)
    databaseName = db.Column(db.String(110), nullable=False)
    
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(256), nullable=False)
    documentUploads = db.relationship('DocumentUploads', backref='user', lazy=True)
    
