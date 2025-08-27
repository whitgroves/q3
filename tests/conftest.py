'''Fixtures for automated testing of qqueue.'''

from random import randint
from datetime import date
from pytest import fixture
from flask import Flask
from flask.testing import FlaskClient
from werkzeug.security import generate_password_hash
from qqueue import create_app
from qqueue.models import User, Task
from qqueue.config import TestConfig
from qqueue.extensions import database

# initialized outside of the app fixture so the other test modules can access.
# it's not "best practice" to do this, but it makes writing tests much easier.
user_data = [{'email':f'user{i}@test.net',
              'username':f'user{i}',
              'password':f'test{i}'} for i in range(2)]
task_data = [{'title':f'Order {i}',
              'description':f'Deliver {i} sprockets to the client.',
              'due':date(2025, 9, i+1)} for i in range(30)]

@fixture()
def application() -> Flask: # pyright: ignore[reportInvalidTypeForm]
    '''Creates an instance of the qqueue app seeded with test data.'''
    app = create_app(TestConfig)

    with app.app_context(): # setup test records
        test_users = [User(email=u['email'],
                           username=u['username'],
                           password=generate_password_hash(u['password']))
                            for u in user_data]
        test_tasks = [Task(title=t['title'],
                           description=t['description'],
                           due=t['due'],
                           user=test_users[randint(0, len(user_data)-1)])
                            for t in task_data]
        database.session.add_all(test_users)
        database.session.add_all(test_tasks)
        database.session.commit()

        # yielded in app context so downstream fixtures/tests have access to it
        # https://testdriven.io/blog/flask-contexts/#testing-example
        yield app

@fixture()
def client(application:Flask) -> FlaskClient: # fixtures, pylint: disable=redefined-outer-name
    '''Returns an automated client for simulating user requests.'''
    return application.test_client()
