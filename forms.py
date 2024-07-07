# forms.py
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, EmailField, validators,FileField,DateField
from wtforms.validators import DataRequired, Email, Length, EqualTo,Optional



 
class ProfileForm(FlaskForm):
  profile_picture = FileField('Profile Picture', validators=[DataRequired()])
  submit = SubmitField('Upload')

# Define a form for user Post
class PostForm(FlaskForm):
  title = StringField('Title', validators=[DataRequired(), Length(min=3, max=50)])  
  content = TextAreaField('Content', validators=[DataRequired()])  
  tag = TextAreaField('Tag', validators=[DataRequired()])
  submit = SubmitField('Post')

# Define a form for user login
class LoginForm(FlaskForm):
    email = StringField('Email', validators=[validators.InputRequired()])
    password = PasswordField('Password', validators=[validators.InputRequired()])
    submit = SubmitField('Login')

# Define a form for user signup
class SignupForm(FlaskForm):
    username = StringField('Username', validators=[validators.InputRequired()])
    email = EmailField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[validators.InputRequired(), validators.EqualTo('confirm_password', message='Passwords must match')])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')

#confirm mail form
class commailForm(FlaskForm):
    email = EmailField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Request Reset Link')

#reset form
class resetpwForm(FlaskForm):
    npass = PasswordField('Password', validators=[validators.InputRequired()])
    cpass = PasswordField('Confirm Password', validators=[DataRequired()])
    submit = SubmitField('Confirm')

#search form
class SearchForm(FlaskForm):
    search = StringField('Search ', validators=[DataRequired()])
    submit = SubmitField('Search')

#comment form
class CommentForm(FlaskForm):
    content = TextAreaField('Comment', validators=[DataRequired()])
    submit = SubmitField('Submit')

class DateFilterForm(FlaskForm):
    created_date = DateField('Created Date')
    submit = SubmitField('Filter')

# define a form for profile upload
class PictureUpdate(FlaskForm):
    profile_picture = FileField('Profile Picture', validators=[validators.InputRequired()])
    submit = SubmitField('Update')
