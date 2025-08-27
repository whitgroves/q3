'''Tests for the user endpoints of qqueue.'''

from random import choice, randint
from flask import g # globals - needed to access CSRF token
from flask.testing import FlaskClient
from tests.conftest import USER_DATA, authenticate_user

def test_index(client:FlaskClient) -> None:
    '''Tests the endpoint `/users`.'''
    
    # Future-proofing
    endpoint = '/users'
    recruit_msgs = [
        f'{len(USER_DATA)} user{"s are" if len(USER_DATA) != 1 else "is"} already on qqueue.', #pylint: disable=line-too-long
        '>Login</a> or <a href=',
        '>register</a> to see user profiles and make requests.',
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
    
    # Future-proofing
    def endpoint(user_id:int) -> str:
        return f'/users/{user_id}'
    
    # If not logged in, get a recruitment message with their username
    # We use user3 (id: 4) since they have neither requests nor orders in the system
    response = client.get(endpoint(4), follow_redirects=True)
    assert response.status_code == 200
    # TODO: check recruitment messages
    assert all(user['email'] not in response.text for user in USER_DATA)
    assert all(user['username'] not in response.text for user in USER_DATA)
    assert all(user['password'] not in response.text for user in USER_DATA)

    # Once logged in, username, tagline, and bio are visible, along with open requests and completed orders
    authenticate_user(credentials=USER_DATA[choice([0, 1, 2])], client=client)
    response = client.get(endpoint(4), follow_redirects=True)
    assert response.status_code == 200
    # TODO: check for absence of recruitment messages
    assert USER_DATA[3]['username'] in response.text
    assert USER_DATA[3]['headline'] in response.text
    assert USER_DATA[3]['bio'] in response.text

    # When logged in as that user, can see the same info + option to edit
    authenticate_user(credentials=USER_DATA[3], client=client)
    response = client.get(endpoint(4), follow_redirects=True)
    assert response.status_code == 200
    assert USER_DATA[3]['username'] in response.text
    assert USER_DATA[3]['headline'] in response.text
    assert USER_DATA[3]['bio'] in response.text
    assert 'edit' in response.text.lower()

    # Logout, then check specific users for...
    client.get('/logout')

    # Only requests completed (user0)
    response = client.get(endpoint(1), follow_redirects=True)
    assert response.status_code == 200
    assert 'completed' in response.text.lower()
    assert 'fulfilled' not in response.text.lower()

    # Only orders fulfilled (user1)
    response = client.get(endpoint(2), follow_redirects=True)
    assert response.status_code == 200
    assert 'completed' not in response.text.lower()
    assert 'fulfilled' in response.text.lower()
    
    # Both orders and requests completed (user2)
    response = client.get(endpoint(3), follow_redirects=True)
    assert response.status_code == 200
    assert 'completed' in response.text.lower()
    assert 'fulfilled' in response.text.lower()

def test_edit(client:FlaskClient) -> None:
    '''Tests the endpoint `/users/<user_id>/edit`.'''
    pass
