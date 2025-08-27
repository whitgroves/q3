'''Data models used by SQLAlchemy to build qqueue's database tables.'''

from flask_login import UserMixin
from sqlalchemy import Column, Integer, String, DateTime, Text, func, ForeignKey#, Table
from qqueue.extensions import database

CASCADE = 'all, delete-orphan' # shorthand for FK relationships

class User(UserMixin, database.Model): # pylint: disable=too-few-public-methods
    '''Defines the table fields for registered users.'''
    id = Column(Integer, primary_key=True)
    email = Column(String(64), nullable=False, unique=True)
    username = Column(String(32), nullable=False, unique=True)
    password = Column(String(128), nullable=False)
    created = Column(DateTime(timezone=True), server_default=func.now()) # pylint: disable=not-callable
    headline = Column(String(256))
    bio = Column(Text)

    def __repr__(self):
        return f'<User {self.id}: "{self.username}" ({self.email})>'
