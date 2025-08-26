'''Data models used by SQLAlchemy to build qqueue's database tables.'''

from flask_login import UserMixin
from sqlalchemy import Column, Integer, String, DateTime, Text, func, ForeignKey#, Table
from qqueue.extensions import database

CASCADE = 'all, delete-orphan' # shorthand for FK relationships

class User(UserMixin, database.Model):
    id = Column(Integer, primary_key=True)
    email = Column(String(64), nullable=False, unique=True)
    username = Column(String(32), nullable=False, unique=True)
    password = Column(String(128), nullable=False)
    created = Column(DateTime(timezone=True), server_default=func.now()) # pylint: disable=not-callable
    headline = Column(String(256))
    bio = Column(Text)
    tasks = database.relationship('Task', backref='user', cascade=CASCADE)
    comments = database.relationship('Comment', backref='user', cascade=CASCADE)

    def __repr__(self):
        return f'<User {self.id}: "{self.username}" ({self.email})>'


class Task(database.Model):
    id = Column(Integer, primary_key=True)
    title = Column(String(128), nullable=False)
    description = Column(Text)
    created = Column(DateTime(timezone=True), server_default=func.now()) # pylint: disable=not-callable
    started = Column(DateTime(timezone=True))
    due = Column(DateTime(timezone=True), nullable=False)
    completed = Column(DateTime(timezone=True))
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    comments = database.relationship('Comment', backref='task', cascade=CASCADE)

    def __repr__(self):
        return f'<Task {self.id}: "{self.title}" (user id: {self.user_id})>'
    

class Comment(database.Model):
    id = Column(Integer, primary_key=True)
    text = Column(Text, nullable=False)
    created = Column(DateTime(timezone=True), server_default=func.now()) # pylint: disable=not-callable
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    task_id = Column(Integer, ForeignKey('task.id'), nullable=False)

    def __repr__(self):
        return f'<Comment {self.id}: (user id: {self.user_id}; task id: {self.task_id})>' # pylint: disable=line-too-long
