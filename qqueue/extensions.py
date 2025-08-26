'''Separate file for flask extensions to avoid circular references.'''

from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

database = SQLAlchemy()
login = LoginManager()
