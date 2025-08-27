'''Tests for the user endpoints of qqueue.'''

from random import choice
from flask import g # globals - needed to access CSRF token
from flask.testing import FlaskClient
from tests.conftest import USER_DATA, authenticate_user

def test_index(client:FlaskClient) -> None:
    '''Tests the endpoint `/users`.'''
    
    # Future-proofing
    endpoint = '/users'
    recruit_msgs = [
        f'{len(USER_DATA)} users are already on qqueue.',
        'Register</a> an account to see their profiles and make requests.'
    ]

    # Can't see any user data when not logged in, but prompted to join
    response = client.get(endpoint, follow_redirects=True)
    assert response.status_code == 200
    assert all(msg in response.text for msg in recruit_msgs)
    assert all(user['email'] not in response.text for user in USER_DATA)
    assert all(user['username'] not in response.text for user in USER_DATA)
    assert all(user['password'] not in response.text for user in USER_DATA)

    # Only usernames are visible, not other user data nor the recruting prompt
    authenticate_user(credentials=choice(USER_DATA), client=client)
    response = client.get(endpoint, follow_redirects=True)
    assert response.status_code == 200
    assert all(msg not in response.text for msg in recruit_msgs)
    assert all(user['username'] in response.text for user in USER_DATA)
    assert all(user['email'] not in response.text for user in USER_DATA)
    assert all(user['password'] not in response.text for user in USER_DATA)

def test_user(client:FlaskClient) -> None:
    '''Tests the endpoint `/users/<user_id>`.'''
    pass

def test_edit(client:FlaskClient) -> None:
    '''Tests the endpoint `/users/<user_id>/edit`.'''
    pass
