'''Fixtures for automated testing of qqueue.'''

from pytest import fixture
from flask import Flask, Response, g
from flask.testing import FlaskClient
from werkzeug.security import generate_password_hash
from qqueue import create_app
from qqueue.models import User
from qqueue.config import TestConfig
from qqueue.extensions import database

# initialized outside of the app fixture so the other test modules can access.
# it's not "best practice" to do this, but it makes writing tests much easier.
USER_DATA = [{'email':f'user{i}@test.net',
               'username':f'user{i}',
               'password':f'test{i}'} for i in range(2)]

@fixture()
def application() -> Flask: # pyright: ignore[reportInvalidTypeForm]
    '''Creates an instance of the qqueue app seeded with test data.'''
    app = create_app(TestConfig)

    with app.app_context(): # setup test records
        test_users = [User(email=user['email'],
                           username=user['username'],
                           password=generate_password_hash(user['password']))
                           for user in USER_DATA]
        database.session.add_all(test_users)
        database.session.commit()

        # yielded in app context so downstream fixtures/tests have access to it
        # https://testdriven.io/blog/flask-contexts/#testing-example
        yield app

@fixture()
def client(application:Flask) -> FlaskClient: # fixtures, pylint: disable=redefined-outer-name
    '''Returns an automated client for simulating user requests.'''
    return application.test_client()

def authenticate_user(credentials:dict, client:FlaskClient) -> Response: # pylint: disable=redefined-outer-name
    '''
    Generates a CSRF token then logs the user into the test client to allow
    testing of authenticated endpoints.

    Included as a helper function and not a fixture so logins can be done on
    an ad-hoc basis, rather than for a predefined set every time.

    For a detailed explaination, see:
        https://gist.github.com/singingwolfboy/2fca1de64950d5dfed72?permalink_comment_id=4556252#gistcomment-4556252
    '''
    client.get('/login') # generates token
    login_data = {'csrf_token': g.csrf_token,
                  'email_or_username': credentials['email'],
                  'password': credentials['password']}
    return client.post('/login', data=login_data, follow_redirects=True)
