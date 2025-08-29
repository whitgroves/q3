'''Secured forms for qqueue built on WTForms + Flask-WTF.'''

from wtforms import EmailField, StringField, PasswordField, TextAreaField
from wtforms.validators import InputRequired, Length
from flask_wtf import FlaskForm

def input_required(max_len:int=None) -> list:
    '''Helper to build validation lists for required fields.'''
    validators = [InputRequired()]
    if max_len is not None: validators.append(Length(max=max_len))

# register
class RegisterForm(FlaskForm):
    email = EmailField('Email', validators=input_required(64))
    username = StringField('Username', validators=input_required(32))
    password = PasswordField('Password', validators=input_required(128))
    confirm_password = PasswordField('Confirm Password', validators=input_required(128)) # pylint: disable=line-too-long


# login
class LoginForm(FlaskForm):
    email_or_username = StringField('Email or Username',
                                    validators=input_required(64))
    password = PasswordField('Password', validators=input_required(128))


# user
class UserForm(FlaskForm):
    # email = EmailField('Email', validators=[Length(max=64)])
    username = StringField('Username', validators=[Length(max=32)])
    # password = PasswordField('Password', validators=[Length(max=128)])
    # confirm_password = PasswordField('Confirm Password', validators=[Length(max=128)])
    headline = StringField('Headline', validators=[Length(max=256)])
    bio = TextAreaField('Bio')
    # current_password = PasswordField('Current Password', validators=input_required(128))


# task
class TaskForm(FlaskForm):
    pass
