'''Tests for the user endpoints of qqueue.'''

from random import choice, randint
from flask import g # globals - needed to access CSRF token
from flask.testing import FlaskClient
from tests.conftest import USER_DATA, authenticate_user

def test_index(client:FlaskClient) -> None:
    '''Tests the endpoint `/users`.'''

    # Future-proofing
    endpoint = '/users/'
    recruit_text = [
        f'{len(USER_DATA)} user{"s are" if len(USER_DATA) != 1 else "is"} already on qqueue.', #pylint: disable=line-too-long
        '>Login</a> or <a href=',
        '>register</a> to see user profiles and make requests.',
    ]

    # Can't see any user data when not logged in, but prompted to join
    response = client.get(endpoint)
    assert response.status_code == 200
    assert all(text in response.text for text in recruit_text)
    assert all(user['email'] not in response.text for user in USER_DATA)
    assert all(user['username'] not in response.text for user in USER_DATA)
    assert all(user['password'] not in response.text for user in USER_DATA)

    # Only usernames are visible, not other user data nor the recruting prompt
    authenticate_user(credentials=choice(USER_DATA), client=client)
    response = client.get(endpoint)
    assert response.status_code == 200
    assert all(text not in response.text for text in recruit_text)
    assert all(user['username'] in response.text for user in USER_DATA)
    assert all(user['email'] not in response.text for user in USER_DATA)
    assert all(user['password'] not in response.text for user in USER_DATA)
    assert 'None' not in response.text

def test_get_user(client:FlaskClient) -> None: # pylint: disable=too-many-statements
    '''Tests the endpoint `/users/<user_id>`.'''

    # Future-proofing
    recruit_text = {
        'requests': 'This user is already making requests on qqueue.',
        'orders': 'This user is already fulfilling orders on qqueue.',
        'both': 'This user is already making requests and fulfilling orders on qqueue.', # pylint: disable=line-too-long
        'neither': 'This user is already registered for qqueue.',
    }
    task_link_text = ['Open Requests', 'Completed Orders']
    def endpoint(user_id:int) -> str:
        return f'/users/{user_id}'

    # If not logged in, get a recruitment message with their username
    # We use user3 (id: 4) since they have neither requests nor orders
    response = client.get(endpoint(4))
    assert response.status_code == 200
    assert recruit_text['requests'] not in response.text
    assert recruit_text['orders'] not in response.text
    assert recruit_text['both'] not in response.text
    assert recruit_text['neither'] in response.text
    assert all(user['email'] not in response.text for user in USER_DATA)
    assert all(user['username'] not in response.text for user in USER_DATA)
    assert all(user['password'] not in response.text for user in USER_DATA)
    assert all(text not in response.text for text in task_link_text)

    # Once logged in, username, tagline, and bio are visible for that user
    # and not any others.
    authenticate_user(credentials=USER_DATA[choice([0, 1, 2])], client=client)
    response = client.get(endpoint(4))
    assert response.status_code == 200
    assert recruit_text['requests'] not in response.text
    assert recruit_text['orders'] not in response.text
    assert recruit_text['both'] not in response.text
    assert recruit_text['neither'] not in response.text
    assert USER_DATA[3]['username'] in response.text
    assert USER_DATA[3]['headline'] in response.text
    assert USER_DATA[3]['bio'] in response.text
    assert all(text in response.text for text in task_link_text)
    assert all(user['username'] not in response.text
               for i, user in enumerate(USER_DATA) if i != 3)
    assert 'None' not in response.text

    # When logged in as that user, can see the same info + option to edit
    authenticate_user(credentials=USER_DATA[3], client=client)
    response = client.get(endpoint(4))
    assert response.status_code == 200
    assert USER_DATA[3]['username'] in response.text
    assert USER_DATA[3]['headline'] in response.text
    assert USER_DATA[3]['bio'] in response.text
    assert 'Edit Profile' in response.text
    assert all(text in response.text for text in task_link_text)
    assert all(user['username'] not in response.text
               for i, user in enumerate(USER_DATA) if i != 3)
    assert 'None' not in response.text

    # Logout, then check recruitment messages for...
    client.get('/logout')

    # Only requests completed (user0)
    response = client.get(endpoint(1))
    assert response.status_code == 200
    assert recruit_text['requests'] in response.text
    assert recruit_text['orders'] not in response.text
    assert recruit_text['both'] not in response.text
    assert recruit_text['neither'] not in response.text

    # Only orders fulfilled (user1)
    response = client.get(endpoint(2))
    assert response.status_code == 200
    assert recruit_text['requests'] not in response.text
    assert recruit_text['orders'] in response.text
    assert recruit_text['both'] not in response.text
    assert recruit_text['neither'] not in response.text

    # Both orders and requests completed (user2)
    response = client.get(endpoint(3))
    assert response.status_code == 200
    assert recruit_text['requests'] not in response.text
    assert recruit_text['orders'] not in response.text
    assert recruit_text['both'] in response.text
    assert recruit_text['neither'] not in response.text

def test_edit_user(client:FlaskClient) -> None:
    '''Tests the endpoint `/users/edit`.'''

    # Future-proofing
    endpoint = '/users/edit'
    new_data = {
        # 'email':'test-1@test.net',
                'username':'test-1',
                # 'password':'pass-1',
                # 'confirm_password':'pass-1',
                'headline':'minus one',
                'bio':'godzilla is my favorite franchise that I do not like.'}

    # Log a sample user into the service
    sample_index = randint(0, len(USER_DATA) - 1)
    credentials = USER_DATA[sample_index]
    # new_data['current_password'] = credentials['password']
    authenticate_user(credentials=credentials, client=client)

    # For GET requests, user sees their own profile but no one else's
    response = client.get(endpoint)
    assert response.status_code == 200
    assert credentials['username'] in response.text
    assert all(user['username'] not in response.text for user in USER_DATA
               if user['username'] != credentials['username'])
    assert 'None' not in response.text

    # For POST requests, the current user is auto-selected for update
    new_data['csrf_token'] = g.csrf_token
    response = client.post(endpoint, data=new_data, follow_redirects=True)
    assert response.status_code == 200

    # They are then redirected to their own user page with updated profile
    assert response.request.path == f'/users/{sample_index + 1}'
    assert new_data['username'] in response.text
    assert new_data['headline'] in response.text
    assert new_data['bio'] in response.text
    assert 'None' not in response.text

    # And none of the old profile data, nor anyone else's is present
    assert all(user['username'] not in response.text for user in USER_DATA)

    # Update fields back to old values 1 at a time to test single edits
    credentials['headline'] = 'goddammit'
    credentials['bio'] = 'ooh you said #11'
    for field in ['username', 'headline', 'bio']:
        value = credentials[field]
        response = client.post(endpoint,
                               data={field:value,
                                    #  'current_password':new_data['password'],
                                     'csrf_token':g.csrf_token},
                               follow_redirects=True)
        assert response.status_code == 200

    # If logged out, both GET and POST should redirect to login
    redirect = '/login'
    client.get('/logout')
    response = client.get(endpoint)
    assert response.status_code == 302
    assert response.location[:len(redirect)] == redirect
    response = client.post(endpoint, data=new_data)
    assert response.status_code == 302
    assert response.location[:len(redirect)] == redirect

    # # Should be able to re-authenticate with new password
    # credentials['password'] = new_data['password']
    # response = authenticate_user(credentials=credentials, client=client)
    # assert response.status_code == 200

    # # Then update to the new data again
    # new_data['csrf_token'] = g.csrf_token # refresh the token
    # new_data['current_password'] = new_data['password']
    # response = client.post(endpoint, data=new_data, follow_redirects=True)
    # assert response.status_code == 200

    # # And finally, logout and log back in with the new credentials
    # client.get('/logout')
    # response = authenticate_user(credentials=new_data, client=client)
    # assert response.status_code == 200
