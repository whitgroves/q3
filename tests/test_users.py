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

    # Helper for endpoint calls
    def endpoint(user_id:int) -> str:
        return f'/users/{user_id}'

    # If not logged in, get a recruitment message with their username
    # We use user3 (id: 4) since they have neither requests nor orders
    response = client.get(endpoint(4), follow_redirects=True)
    assert response.status_code == 200
    assert 'already' in response.text
    assert all(user['email'] not in response.text for user in USER_DATA)
    assert all(user['username'] not in response.text for user in USER_DATA)
    assert all(user['password'] not in response.text for user in USER_DATA)

    # Once logged in, username, tagline, and bio are visible,
    # along with open requests and completed orders
    authenticate_user(credentials=USER_DATA[choice([0, 1, 2])], client=client)
    response = client.get(endpoint(4), follow_redirects=True)
    assert response.status_code == 200
    assert 'already' not in response.text
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
    '''Tests the endpoint `/users/edit`.'''

    # Helper for endpoint calls
    endpoint = '/users/edit'
    new_data = {'email':'test-1@test.net',
                'username':'test-1',
                'password':'pass-1',
                'confirm_password':'pass-1',
                'headline':'minus one',
                'bio':'godzilla is my favorite franchise that I do not like.'}

    # Log a sample user into the service
    sample_index = randint(0, len(USER_DATA) - 1)
    credentials = USER_DATA[sample_index]
    new_data['current_password'] = credentials['password']
    authenticate_user(credentials=credentials, client=client)

    # For GET requests, user sees their own profile but no one else's
    response = client.get(endpoint, follow_redirects=True)
    assert response.status_code == 200
    assert credentials['username'] in response.text
    assert all(user['username'] not in response.text for user in USER_DATA
               if user['username'] != credentials['username'])

    # For POST requests, the current user is auto-selected for update
    new_data['csrf_token'] = g.csrf_token
    response = client.post(endpoint, data=new_data, follow_redirects=True)
    assert response.status_code == 200

    # They are then redirected to their own user page with updated profile
    assert response.request.path == f'/users/{sample_index + 1}'
    assert new_data['username'] in response.text
    assert new_data['headline'] in response.text
    assert new_data['bio'] in response.text

    # And none of the old profile data, nor anyone else's is present
    assert all(user['username'] not in response.text for user in USER_DATA)

    # Update non-password fields back to old values 1 at a time to test single edits
    credentials['headline'] = 'goddammit'
    credentials['bio'] = 'ooh you said #11'
    for field in ['email', 'username', 'headline', 'bio']:
        value = credentials[field]
        response = client.post(endpoint,
                               data={field:value,
                                     'current_password':new_data['password'],
                                     'csrf_token':g.csrf_token},
                               follow_redirects=True)
        assert response.status_code == 200
        if field != 'email':
            assert value in response.text
            assert new_data[field] not in response.text

    # If logged out, both GET and POST should redirect to the home index
    client.get('/logout')
    response = client.get(endpoint, follow_redirects=True)
    assert response.status_code == 200
    assert response.request.path == '/login'
    response = client.post(endpoint, data=new_data, follow_redirects=True)
    assert response.status_code == 200
    assert response.request.path == '/login'

    # Should be able to re-authenticate with new password
    credentials['password'] = new_data['password']
    response = authenticate_user(credentials=credentials, client=client)
    assert response.status_code == 200

    # Then update to the new data again
    new_data['csrf_token'] = g.csrf_token # refresh the token
    new_data['current_password'] = new_data['password']
    response = client.post(endpoint, data=new_data, follow_redirects=True)
    assert response.status_code == 200

    # And finally, logout and log back in with the new credentials
    client.get('/logout')
    response = authenticate_user(credentials=new_data, client=client)
    assert response.status_code == 200
