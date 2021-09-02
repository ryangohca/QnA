import string

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField
from wtforms.validators import ValidationError, DataRequired, EqualTo, Length

from QnA.models import Users

def userExists(form, field):
    username = field.data
    return len(Users.query.filter_by(username=username).all()) != 0
  
class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    
    def validate_username(form, field):
        if not userExists(form, field):
            raise ValidationError("Username does not exist in server.")
            
    def validate_password(form, field):
        user = Users.query.filter_by(username=form.username.data).first()
        if not user.check_password(field.data):
            raise ValidationError("Password is incorrect.")
            
class SignupForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired(), Length(6, -1, "Password must be at least 6 characters long.")])
    confirm = PasswordField('Confirm Password', validators=[
        EqualTo("password", "Passwords do not match!")
    ])
    
    def validate_username(form, field):
        if userExists(form, field):
            raise ValidationError("Username already exists in server.")
            
    def validate_password(form, field):
        validated = True
        
        password = field.data
        if not any(char in set(string.punctuation + string.digits) for char in password):
            form.password.errors.append("Password must have at least 1 special character (punctuation or number).")
            validated = False
            
        if not any(char in string.ascii_uppercase for char in password):
            form.password.errors.append("Password must have at least 1 uppercase character.")
            validated = False
            
        if not any(char in string.ascii_lowercase for char in password):
            form.password.errors.append("Password must have at least 1 lowercase character.")
            validated = False 
        
        if form.username.data in password:
            form.password.errors.append("Password must not contain username.")
            validated = False
            
        return validated
            
        