import string
import datetime

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, HiddenField, SelectField, IntegerField
from wtforms.validators import ValidationError, InputRequired, EqualTo, Length, NumberRange, Optional
from flask_login import current_user

from QnA.models import Users, DocumentUploads, Pages, ExtractedImages, Answers, Questions, getAllPaperTitles, get_all_questions, Worksheets


def userExists(form, field):
    username = field.data.strip()
    return len(Users.query.filter_by(username=username).all()) != 0
  
def getAllUploadDocuments(userID):
    allDocs = DocumentUploads.query.filter_by(userID=userID).all()
    selectChoices = []
    for doc in allDocs:
        selectChoices.append((doc.id, doc.originalName))
    return selectChoices
  
class LoginForm(FlaskForm):
    username = StringField('Username', id="login-username", validators=[InputRequired()])
    password = PasswordField('Password', id="login-password", validators=[InputRequired()])
    remember_me = BooleanField('Remember Me', id="login-remember_me")
    
    formName = HiddenField(default="login", id="login-formName")
    
    def validate_username(form, field):
        if not userExists(form, field):
            raise ValidationError("Username does not exist in server.")
        return True
            
    def validate_password(form, field):
        user = Users.query.filter_by(username=form.username.data.strip()).first()
        if user is None:
            # validate_password still runs even if username does not exist.
            # We just suppress this validation
            return False
        if not user.check_password(field.data):
            raise ValidationError("Password is incorrect.")
        return True
            
class SignupForm(FlaskForm):
    username = StringField('Username', id="signup-username", validators=[InputRequired()])
    password = PasswordField('Password', id="signup-password", validators=[InputRequired(), Length(6, 24, "Password must be between 6 to 24 characters long.")])
    confirm = PasswordField('Confirm Password', id="signup-confirm", validators=[InputRequired(), EqualTo("password", "Passwords do not match!")])
    remember_me = BooleanField('Remember Me', id="signup-remember_me")
    
    formName = HiddenField(default='signup', id="signup-formName")
    
    def validate_username(form, field):
        if userExists(form, field):
            raise ValidationError("Username already exists in server.")
        return True
            
    def validate_password(form, field):
        validated = True
        
        password = field.data
        if not any(char in string.digits for char in password):
            form.password.errors.append("Password must have at least 1 number.")
            validated = False
            
        if not any(char in set(string.punctuation) for char in password):
            form.password.errors.append("Password must have at least 1 punctuation.")
            validated = False

        if not any(char in string.ascii_uppercase for char in password):
            form.password.errors.append("Password must have at least 1 uppercase character.")
            validated = False
            
        if not any(char in string.ascii_lowercase for char in password):
            form.password.errors.append("Password must have at least 1 lowercase character.")
            validated = False 
        
        if form.username.data.lower() in password.lower():
            form.password.errors.append("Password must not contain username.")
            validated = False
            
        return validated
            
class TagForm(FlaskForm):
    imageType = SelectField('Type*:', id="tag-imageType", choices=[('question', 'Question Statement'), ('answer', 'Answer')], default='question', validators=[InputRequired()])
    subject = StringField('Subject:', id="tag-subject")
    topic = StringField('Topic:', id="tag-topic")
    year = IntegerField('Year:', id='tag-year', validators=[Optional(), NumberRange(min=1950, max=datetime.datetime.now().year, message='Invalid year: please enter a year between %(min)s and %(max)s.')])
    paper = StringField('Paper Title (please be as specific as possible):', id='tag-paper')
    questionNo = IntegerField('Question Number:', id="tag-qnNo", validators=[Optional(), NumberRange(min=1, message='Question Number must be positive!')])
    questionPart = StringField('Part:', id="tag-qnPart")
    questionDocument = SelectField('Question From:', id="tag-questionDoc", coerce=int, choices=[], default="")
    paperSelect = SelectField('Choose paper:', id="tag-paperSelect", coerce=str, choices=[('none', 'Select a paper...')], default="none") #This field will be populated with Javascript
    answer = StringField('Answer (leave blank if not in text):', id="tag-qnAns")
    
    def __init__(self, *args, **kwargs):
        if 'currImageID' not in kwargs:
            raise TypeError('TagForm() missing 1 required keyword-only argument: `currImageID`.')
        super().__init__(*args, **kwargs)
        self.questionDocument.choices = getAllUploadDocuments(current_user.id)
        pageID = ExtractedImages.query.get(kwargs['currImageID']).pageID
        documentID = Pages.query.get(pageID).documentID
        self.questionDocument.default = documentID
        self.currImageID = kwargs['currImageID']
        allPaperTitles = getAllPaperTitles(current_user.id)
        for choices in allPaperTitles.values():
            self.paperSelect.choices.extend([(str(year) + "^%$" + paper, '') for year, paper in choices])
        
    def validate_questionPart(form, field):
        # Firstly, reject any forms with a question part but no question number.
        if field.data is None and form.questionNo.data is not None:
            raise ValidationError("All question part must follow a valid question number.")
        # If questionType is answer, we just need to check whether the corresponding qn already has an answer.
        # However, we prioritise entry of data into database first, so if any of (year, paper, questionNo)
        # is missing, we just validate the form and throw whatever data inside.
        # In the case of answers, the answer would just be stored but inaccessible to users if it is not linked
        # to a qn.
        if form.imageType.data == "answer":
            if form.paperSelect.data == "none" or form.questionNo.data is None:
                return True
            year, paper = form.paperSelect.data.split('^%$')
            if year == "noyear":
                year = None
            else:
                year = int(year)
            for question in Questions.query.filter_by(year=year, paper=paper, questionNo=form.questionNo.data, questionPart=form.questionPart.data).all():
                pageID = ExtractedImages.query.get(question.id).pageID
                documentID = Pages.query.get(pageID).documentID
                userID = DocumentUploads.query.get(documentID).userID
                if userID == current_user.id:
                    if question.answer is not None:
                        raise ValidationError('This question already has a corresponding answer. Did you mistype something?')
        # If questionType is question, we just need to check whether the following condition is True:
        #   There should be no 2 questions with the same (year, paper, questionNo, questionPart) for the same user.
        # Similarly, if data is not available for checking, we just throw data into database if possible.
        # The only exception is when year is not specified but paper and questionNo is satisfied. We would prompt
        # user to enter a valid year if there are potential clashes.
        elif form.imageType.data == "question":
            if form.paper.data is None or form.questionNo.data is None:
                return True
            year = form.year.data
            for question in Questions.query.filter_by(year=year, paper=form.paper.data, questionNo=form.questionNo.data, questionPart=form.questionPart.data).all():
                pageID = ExtractedImages.query.get(question.id).pageID
                documentID = Pages.query.get(pageID).documentID
                userID = DocumentUploads.query.get(documentID).userID
                if userID == current_user.id and form.currImageID != question.id: # Belongs to this user AND not trying to update the form.
                    raise ValidationError("This question already exists in server. Did you mistype `questionNo`?")
            return True
          
class WorksheetForm(FlaskForm):
    title = StringField('Worksheet Title', id="create-title", validators=[InputRequired()])
    year = IntegerField('Year of Publishing: ', id="create-year", validators=[InputRequired(), NumberRange(min=1950, max=datetime.datetime.now().year+10, message='Invalid year: please enter a year between %(min)s and %(max)s.')]) 
    # 2022 worksheet can be made in 2021
    subject = StringField('Worksheet Subject', id="create-subject", validators=[InputRequired()])
    format = SelectField('Export Format: ', id="create-format", choices=[('pdf', 'PDF'), ('docx', 'Word Document')])
    
    def validate_title(form, field):
        title = field.data
        if (len(Worksheets.query.filter_by(title=title).all())):
            raise ValidationError(f"A worksheet with title {title} already exists! Please choose another name!")
        
class AddQuestionForm(FlaskForm):
    # This is not the form we submit, this form fills up 'AddQuestionSubmitForm', which is then submitted
    document = SelectField("Document Name", id="select-document", coerce=str, choices=[], validators=[InputRequired()])  
    paper = SelectField("Paper", id="select-paper", choices=[], validators=[InputRequired()])
    question = SelectField("Question", id="select-question", choices=[], validators=[InputRequired()])
    bulk_options = SelectField("Add all from", id="select-bulk", choices=[('individual', 'No'), ('doc', 'Document'), ('paper', 'Paper')], validators=[InputRequired()])
    def __init__(self):
        super().__init__()
        for doc in DocumentUploads.query.filter_by(userID=current_user.id):
            self.document.choices.append((doc.id, doc.originalName))
            
class AddQuestionSubmitForm(FlaskForm):
    worksheet = HiddenField(default='', id="worksheetID")
    questions = HiddenField(default='', id="questions")
    
    def validate_worksheet(form, field):
        try:
            wksheetID = int(field.data)
        except ValueError:
            raise ValidationError("Internal Error: Invalid worksheetID.")
        if Worksheets.query.get(wksheetID) is None:
            raise ValidationError("Internal Error: Invalid worksheetID.")
        return True
      
    def validate_questions(form, field):
        if field.data == "":
            return True
        if field.data[-1] != ',':
            raise ValidationError("Internal Error: questions field is tampered with.")
        
        questionIDs = field.data[:-1].split(',')
        for qnID in questionIDs:
            try:
                qnID = int(qnID)
            except ValueError:
                raise ValidationError("Internal Error: One of the questionIDs is not an integer.")
            if Questions.query.get(qnID) is None:
                raise ValidationError("Internal Error: One of the questionIDs is not defined in database.")
        
    