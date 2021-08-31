from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField

from wtforms.validators import InputRequired, ValidationError, DataRequired, EqualTo

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')
    
class SignupForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm = PasswordField('Confirm Password', validators=[
        EqualTo("password", "Passwords do not match!")
    ])
    submit = SubmitField('Sign Up')