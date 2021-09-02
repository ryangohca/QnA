import string

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, HiddenField
from wtforms.validators import ValidationError, DataRequired, EqualTo, Length

from QnA.models import Users

def userExists(form, field):
    username = field.data.strip()
    return len(Users.query.filter_by(username=username).all()) != 0
  
class LoginForm(FlaskForm):
    username = StringField('Username', id="login-username", validators=[DataRequired()])
    password = PasswordField('Password', id="login-password", validators=[DataRequired()])
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
    username = StringField('Username', id="signup-username", validators=[DataRequired()])
    password = PasswordField('Password', id="signup-password", validators=[DataRequired(), Length(6, 24, "Password must be between 6 to 24 characters long.")])
    confirm = PasswordField('Confirm Password', id="signup-confirm", validators=[EqualTo("password", "Passwords do not match!")])
    remember_me = BooleanField('Remember Me', id="signup-remember_me")
    
    formName = HiddenField(default='signup', id="signup-formName")
    
    def validate_username(form, field):
        if userExists(form, field):
            raise ValidationError("Username already exists in server.")
        return True
            
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
        
        if form.username.data.lower() in password.lower():
            form.password.errors.append("Password must not contain username.")
            validated = False
            
        return validated
            
        