'''Data models used by SQLAlchemy to build qqueue's database tables.'''

from flask_login import UserMixin
from sqlalchemy import Column, Integer, String, DateTime, func #, Table
from qqueue.extensions import database

class User(UserMixin, database.Model):
    id = Column(Integer, primary_key=True)
    email = Column(String(64), nullable=False, unique=True)
    username = Column(String(32), nullable=False, unique=True)
    password = Column(String(128), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now()) # pylint: disable=not-callable

    def __repr__(self):
        return f'<User {self.id}: "{self.username}" ({self.email})>'
