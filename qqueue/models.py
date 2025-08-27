'''Data models used by SQLAlchemy to build qqueue's database tables.'''

from flask_login import UserMixin
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, Float, func, ForeignKey
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
    requests = database.relationship('Request', backref='user', cascade=CASCADE)
    orders = database.relationship('Order', backref='user', cascade=CASCADE)


class Request(database.Model): # pylint: disable=too-few-public-methods
    id = Column(Integer, primary_key=True)
    summary = Column(String(256), nullable=False)
    description = Column(Text)
    reward_amount = Column(Float, nullable=False)
    reward_currency = Column(String(16), nullable=False)
    due_by = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now()) # pylint: disable=not-callable
    created_by = Column(Integer, ForeignKey('user.id'), nullable=False)
    accepted_at = Column(DateTime(timezone=True))
    orders = database.relationship('Order', backref='request', cascade=CASCADE)


class Order(database.Model): # pylint: disable=too-few-public-methods
    id = Column(Integer, primary_key=True)
    request_id = Column(Integer, ForeignKey('request.id'), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now()) # pylint: disable=not-callable
    created_by = Column(Integer, ForeignKey('user.id'), nullable=False)
    completed_at = Column(DateTime(timezone=True))
    approved_at = Column(DateTime(timezone=True))
    rejected_at = Column(DateTime(timezone=True))
    comments = database.relationship('Comment', backref='order', cascade=CASCADE)


class Comment(database.Model): # pylint: disable=too-few-public-methods
    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey('order.id'), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now()) # pylint: disable=not-callable
    created_by = Column(Integer, ForeignKey('user.id'), nullable=False)
    text = Column(Text, nullable=False)
