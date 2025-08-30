'''Data models used by SQLAlchemy to build qqueue's database tables.'''

from flask_login import UserMixin
from sqlalchemy import Column, Integer, String, Date, DateTime, Text, Float, func, ForeignKey
from qqueue.extensions import database

CASCADE = 'all, delete-orphan' # shorthand for FK relationships

class User(UserMixin, database.Model): # pylint: disable=too-few-public-methods
    '''Defines the table fields for registered users.'''
    id = Column(Integer, primary_key=True)
    email = Column(String(64), nullable=False, unique=True)
    username = Column(String(32), nullable=False, unique=True)
    password = Column(String(128), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now()) # pylint: disable=not-callable
    headline = Column(String(256))
    bio = Column(Text)
    requests = database.relationship('Task',
                                     primaryjoin='User.id == Task.requested_by',
                                     backref='requester',
                                     cascade=CASCADE)
    orders = database.relationship('Task',
                                   primaryjoin='User.id == Task.accepted_by',
                                   backref='provider',
                                   cascade=CASCADE)
    
    def __str__(self):
        return self.username


class Task(database.Model): # pylint: disable=too-few-public-methods
    '''Defines the table fields for tasks.'''
    id = Column(Integer, primary_key=True)
    summary = Column(String(256), nullable=False)
    detail = Column(Text, nullable=False)
    reward_amount = Column(Float, nullable=False)
    reward_currency = Column(String(16), nullable=False)
    due_by = Column(Date(), nullable=False)
    requested_at = Column(DateTime(timezone=True), server_default=func.now()) # pylint: disable=not-callable
    requested_by = Column(Integer, ForeignKey('user.id'), nullable=False)
    accepted_at = Column(DateTime(timezone=True))
    accepted_by = Column(Integer, ForeignKey('user.id'))
    completed_at = Column(DateTime(timezone=True))
    approved_at = Column(DateTime(timezone=True))
    rejected_at = Column(DateTime(timezone=True))
    comments = database.relationship('Comment', backref='task', cascade=CASCADE)


class Comment(database.Model): # pylint: disable=too-few-public-methods
    id = Column(Integer, primary_key=True)
    task_id = Column(Integer, ForeignKey('task.id'), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now()) # pylint: disable=not-callable
    created_by = Column(Integer, ForeignKey('user.id'), nullable=False)
    text = Column(Text, nullable=False)
