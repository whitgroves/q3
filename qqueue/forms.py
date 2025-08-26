'''Secured forms for qqueue built on WTForms + Flask-WTF.'''

from wtforms import EmailField, StringField, PasswordField
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
    confirm_password = PasswordField('Confirm Password', validators=input_required(128))


# login
class LoginForm(FlaskForm):
    email_or_username = StringField('Email or Username',
                                    validators=input_required(64))
    password = PasswordField('Password', validators=input_required(128))
