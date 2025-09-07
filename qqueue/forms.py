'''Secured forms for qqueue built on WTForms + Flask-WTF.'''

from wtforms import EmailField, StringField, PasswordField, TextAreaField, FloatField, SelectField, DateField
from wtforms.validators import DataRequired, Length, NumberRange
from flask_wtf import FlaskForm
from qqueue.config import ACCEPTED_CURRENCIES

def required_max_len(max_len:int=None) -> list:
    '''Helper to build validation lists for required fields.'''
    validators = [DataRequired()]
    if max_len is not None: validators.append(Length(max=max_len))
    return validators

# register
class RegisterForm(FlaskForm):
    email = EmailField('Email', validators=required_max_len(64))
    username = StringField('Username', validators=required_max_len(32))
    password = PasswordField('Password', validators=required_max_len(128))
    confirm_password = PasswordField('Confirm Password',
                                     validators=required_max_len(128))


# login
class LoginForm(FlaskForm):
    email_or_username = StringField('Email or Username',
                                    validators=required_max_len(64))
    password = PasswordField('Password', validators=required_max_len(128))


# user
class UserForm(FlaskForm):
    username = StringField('Username', validators=[Length(max=32)])
    headline = StringField('Headline', validators=[Length(max=256)])
    bio = TextAreaField('Bio')


# user credentials
class CredentialsForm(FlaskForm):
    email = EmailField('Email', validators=[Length(max=64)])
    password = PasswordField('Password', validators=[Length(max=128)])
    confirm_password = PasswordField('Confirm Password',
                                     validators=[Length(max=128)])
    current_password = PasswordField('Current Password',
                                     validators=required_max_len(128))

# task
class TaskForm(FlaskForm):
    summary = StringField('Summary', validators=required_max_len(256))
    detail = TextAreaField('Detail', validators=[DataRequired()])
    reward_amount = FloatField('Reward Amount',
                               validators=[DataRequired(), NumberRange(min=0)])
    reward_currency = SelectField('Reward Currency',
                                  choices=ACCEPTED_CURRENCIES,
                                  validators=[DataRequired()])
    due_by = DateField('Due By', validators=[DataRequired()])


# comment
class CommentForm(FlaskForm):
    text = TextAreaField('Text', validators=[DataRequired()])
