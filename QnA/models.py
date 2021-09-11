import json

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from QnA import db, login
from QnA.clean import clean_directories

def getAllPaperTitles(currentUserID):
    allTitles = {}
    for question in Questions.query.all():
        pageID = ExtractedImages.query.get(question.id).pageID
        documentID = Pages.query.get(pageID).documentID
        userID = DocumentUploads.query.get(documentID).userID
        if userID == currentUserID:
            if documentID not in allTitles:
                allTitles[documentID] = set()
            allTitles[documentID].add((question.year, question.paper))
    for documentID in allTitles:
        allTitles[documentID] = list(allTitles[documentID])
    # Abuse json to convert tuples to lists (since Javascript don't support tuples)
    return json.loads(json.dumps(allTitles))
  
def get_all_questions(currentUserID):
    all_questions = {};
    for question in Questions.query.all():
        pageID = ExtractedImages.query.get(question.id).pageID # directed graph
        documentID = Pages.query.get(pageID).documentID
        userID = DocumentUploads.query.get(documentID).userID
        if (userID == currentUserID):
            paper = question.paper
            if (paper not in all_questions):
                all_questions[paper] = set()
            answer = Answers.query.filter_by(questionID=question.id).first()
            all_questions[paper].add((question.id, answer.id, question.questionNo, question.questionPart))
    for paper in all_questions:
        all_questions[paper] = list(all_questions[paper])
    return json.loads(json.dumps(all_questions))

def get_all_worksheet_questions(worksheetID):
    # returns a list of (questionID, questionImage, answerImage)
    allQn = []
    for wksheetQn in WorksheetsQuestions.query.filter_by(worksheetID=worksheetID).all():
        currQn = Questions.query.get(wksheetQn.questionID)
        questionImage = ExtractedImages.query.get(currQn.id).databaseName
        answerImage = None
        if currQn.answer is not None:
            answerImage = ExtractedImages.query.get(currQn.answer.id).databaseName
        allQn.append((currQn.id, questionImage, answerImage))
    allQn.sort(key=lambda qn: WorksheetsQuestions.query.filter_by(worksheetID=worksheetID, questionID=qn[0]).first().position)
    return allQn
   
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
    worksheets = db.relationship('Worksheets', backref='users', lazy=True)
    
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
    
# The last 2 models accept null values as user may be unable to give ALL the information at one shot / have insufficient info
# We try to store as much data is possible, even if majority of fields in a row are null.
# This is because preventing loss of data > preserving db form
class Questions(db.Model):
    __tablename__ = 'questions'
    id = db.Column(db.Integer, db.ForeignKey('extractedImages.id'), primary_key=True, autoincrement=False)
    subject = db.Column(db.String(256), nullable=True)
    topic = db.Column(db.String(256), nullable=True)
    year = db.Column(db.Integer, nullable=True)
    paper = db.Column(db.String(256), nullable=True)
    questionNo = db.Column(db.Integer, nullable=True)
    questionPart = db.Column(db.String(5), nullable=True)
    answer = db.relationship('Answers', uselist=False, backref='questions')
    wksheetQns = db.relationship('WorksheetsQuestions', backref='questions', lazy=True)
    
class Answers(db.Model):
    __tablename__ = 'answers'
    id = db.Column(db.Integer, db.ForeignKey('extractedImages.id'), primary_key=True, autoincrement=False)
    answerText = db.Column(db.String(256), nullable=True)
    questionDocumentID = db.Column(db.Integer, db.ForeignKey('documentUploads.id'), nullable=True)
    qnYear = db.Column(db.Integer, nullable=True)
    qnPaper = db.Column(db.String(256), nullable=True)
    questionNo = db.Column(db.Integer, nullable=True)
    questionPart = db.Column(db.String(5), nullable=True)
    # Previous 5 are to store info of a possible Question in the future 
    # Used when data given is incomplete / we are unable to find a match in Questions table
    # NOTE: Prefer `questionID` if it is defined.
    questionID = db.Column(db.Integer, db.ForeignKey('questions.id'), nullable=True)

class Worksheets(db.Model):
    __tablename__ = 'worksheets'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    owner = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(256), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    format = db.Column(db.String(256), nullable=False)
    subject = db.Column(db.String(256), nullable=True)
    wksheetQns = db.relationship('WorksheetsQuestions', backref='worksheets', lazy=True)
    
class WorksheetsQuestions(db.Model):
    __tablename__ = 'worksheetQuestions'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    worksheetID = db.Column(db.Integer, db.ForeignKey('worksheets.id'), nullable=False)
    questionID = db.Column(db.Integer, db.ForeignKey('questions.id'), nullable=False)
    position = db.Column(db.Integer, nullable=False) #Disabling unique for now
    
@login.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))
  
def __insert_dummy_user():
    dummy = Users(username='admin')
    dummy.set_password('admin')
    db.session.add(dummy)
    db.session.commit()
    
def __refreshTable(table):
    table.__table__.drop(db.engine)
    table.__table__.create(db.engine)
    
def __refreshDb():
    db.drop_all()
    clean_directories(False)
    db.create_all()
    insert_dummy_user()
    
def __update():
    # Do whatever thing that you want to do here
    __refreshTable(WorksheetsQuestions)
    pass
  
#__update()
