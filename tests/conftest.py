'''Fixtures for automated testing of qqueue.'''

from secrets import token_hex
from datetime import date, timedelta
from pytest import fixture
from flask import Flask, Response, g
from flask.testing import FlaskClient
from werkzeug.security import generate_password_hash
from qqueue import create_app
from qqueue.models import User, Task, Comment
from qqueue.config import TestConfig
from qqueue.extensions import database

# initialized outside of the app fixture so the other test modules can access.
# it's not "best practice" to do this, but it makes writing tests much easier.
USER_DATA = [{'email':f'user{i}@test.net',
              'username':f'user{i}',
              'password':f'pass{i}',
              'address':f'0x{token_hex(20)}'} for i in range(4)]

# There are some specific scenarios being checked on user pages, so we make
# a batch of similar tasks, then modify a couple of them for those tests
TASK_DATA = [{'summary':f'Setup {i} laptops',
              'detail':f'Install Windows {10+i} and link it to Azure AD.',
              'reward_amount':50.0*i,
              'reward_currency':f'USD{i}',
              'due_by':date.today()+timedelta(days=i), # nearest dates first
              'requested_by':1}  # user0 (only tasks requested)
              for i in range(2, 13)]

TASK_DATA[0]['accepted_by'] = 3  # user2 (task completed + approved)
TASK_DATA[0]['accepted_at'] = date.today()-timedelta(2)
TASK_DATA[0]['completed_at'] = date.today()-timedelta(1)
TASK_DATA[0]['approved_at'] = date.today()

TASK_DATA[1]['requested_by'] = 3 # user2 (task completed + approved)
TASK_DATA[1]['accepted_by'] = 2  # user1 (only tasks accepted)
TASK_DATA[1]['accepted_at'] = date.today()-timedelta(1)
TASK_DATA[1]['completed_at'] = date.today()
TASK_DATA[1]['approved_at'] = date.today()

# task 2 (id:3) is accepted but not completed or approved
TASK_DATA[2]['accepted_by'] = 2  # user1
TASK_DATA[2]['accepted_at'] = date.today()

# task 3 (id:4) is accepted and completed but not approved
TASK_DATA[3]['accepted_by'] = 2  # user1
TASK_DATA[3]['accepted_at'] = date.today()-timedelta(1)
TASK_DATA[3]['completed_at'] = date.today()

# user3 (id:4) needs neither, but they do need a tagline and bio
USER_DATA[3]['headline'] = '3rd rock'
USER_DATA[3]['bio'] = 'Most definitely not an extraterrestrial'

# Each task will have at least 1 comment by the requester, plus another
# for each stage it has moved through (accepted, completed, approved)
COMMENT_DATA = []
for i, task in enumerate(TASK_DATA):
    task_id = i + 1
    COMMENT_DATA.append({
        'task_id': task_id,
        'created_by': task['requested_by'],
        'text': f'Requesting assistance for task{task_id}.',
    })
    if 'accepted_at' in task:
        COMMENT_DATA.append({
            'task_id': task_id,
            'created_by': task['accepted_by'],
            'text': f'I will complete task{task_id}',
        })
    if 'completed_at' in task:
        COMMENT_DATA.append({
            'task_id': task_id,
            'created_by': task['accepted_by'],
            'text': f'I have completed task{task_id}',
        })
    if 'approved_at' in task:
        COMMENT_DATA.append({
            'task_id': task_id,
            'created_by': task['requested_by'],
            'text': f'I approve the work on task{task_id}',
        })

@fixture()
def application() -> Flask: # pyright: ignore[reportInvalidTypeForm]
    '''Creates an instance of the qqueue app seeded with test data.'''
    app = create_app(TestConfig)

    # since some users have custom fields, we populate the db with an unpacked
    # dict; the side effect is passwords are unhashed, so we copy the dict and
    # hash them separately, allowing for properly stored passwords but also
    # authentication by the test client.
    hashed_user_data = [user.copy() for user in USER_DATA]
    for user in hashed_user_data:
        user['password'] = generate_password_hash(user['password'])

    with app.app_context(): # setup test records
        test_users = [User(**user) for user in hashed_user_data]
        test_tasks = [Task(**task) for task in TASK_DATA]
        test_comments = [Comment(**comment) for comment in COMMENT_DATA]
        database.session.add_all(test_users)
        database.session.add_all(test_tasks)
        database.session.add_all(test_comments)
        database.session.commit()

        # yielded in app context so downstream fixtures/tests have access to it
        # https://testdriven.io/blog/flask-contexts/#testing-example
        yield app

@fixture()
def client(application:Flask) -> FlaskClient: # fixtures, pylint: disable=redefined-outer-name
    '''Returns an automated client for simulating user requests.'''
    return application.test_client()

# Helpers

def authenticate_user(credentials:dict, client:FlaskClient) -> Response: # pylint: disable=redefined-outer-name
    '''
    Generates a CSRF token then logs the user into the test client to allow
    testing of authenticated endpoints.

    Included as a helper function and not a fixture so logins can be done on
    an ad-hoc basis, rather than for a predefined set every time.

    For a detailed explaination, see:
        https://gist.github.com/singingwolfboy/2fca1de64950d5dfed72?permalink_comment_id=4556252#gistcomment-4556252
    '''
    client.get('/auth/login') # generates token
    login_data = {'csrf_token': g.csrf_token,
                  'email_or_username': credentials['email'],
                  'password': credentials['password']}
    return client.post('/auth/login', data=login_data, follow_redirects=True)

def assert_redirect(response:Response, redirect='/auth/login') -> None:
    '''
    Asserts `response` was a redirect (302) to `redirect` (default `/login`).

    Included as a helper function since this case has come up across tests.
    '''
    assert response.status_code == 302
    assert response.location[:len(redirect)] == redirect
