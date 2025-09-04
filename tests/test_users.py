'''Tests for the user endpoints of qqueue.'''

from random import choice, randint
from flask import g # globals - needed to access CSRF token
from flask.testing import FlaskClient
from tests.conftest import USER_DATA, TASK_DATA, authenticate_user, assert_redirect

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
    def endpoint(user_id:int) -> str:
        return f'/users/{user_id}'
    sample_id = 4 # We use user3 (id: 4) since they lack requests and orders

    # If not logged in, get a recruitment message with their username
    response = client.get(endpoint(sample_id))
    assert response.status_code == 200
    assert recruit_text['requests'] not in response.text
    assert recruit_text['orders'] not in response.text
    assert recruit_text['both'] not in response.text
    assert recruit_text['neither'] in response.text
    assert all(user['email'] not in response.text for user in USER_DATA)
    assert all(user['username'] not in response.text
               for i, user in enumerate(USER_DATA) if i != sample_id-1)
    assert all(user['password'] not in response.text for user in USER_DATA)

    # Once logged in, see only that user's profile info + open requests
    sample_user = USER_DATA[choice([0, 1, 2])]
    authenticate_user(credentials=sample_user, client=client)
    response = client.get(endpoint(sample_id))
    assert response.status_code == 200
    assert recruit_text['requests'] not in response.text
    assert recruit_text['orders'] not in response.text
    assert recruit_text['both'] not in response.text
    assert recruit_text['neither'] not in response.text
    assert USER_DATA[sample_id-1]['username'] in response.text
    assert USER_DATA[sample_id-1]['headline'] in response.text
    assert USER_DATA[sample_id-1]['bio'] in response.text
    assert 'None' not in response.text
    for i, user in enumerate(USER_DATA):
        if i != sample_id-1 and user['username'] != sample_user['username']:
            assert user['username'] not in response.text

    # When logged in as that user, can see the same info + option to edit
    authenticate_user(credentials=USER_DATA[3], client=client)
    response = client.get(endpoint(sample_id))
    assert response.status_code == 200
    assert USER_DATA[sample_id-1]['username'] in response.text
    assert USER_DATA[sample_id-1]['headline'] in response.text
    assert USER_DATA[sample_id-1]['bio'] in response.text
    assert 'Edit Profile' in response.text
    assert all(user['username'] not in response.text
               for i, user in enumerate(USER_DATA) if i != sample_id-1)
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

    # Login as user2 to cover task visibliity cases
    test_user_id = 3
    test_user = USER_DATA[test_user_id-1]
    authenticate_user(credentials=test_user, client=client)

    # When logged in, should see the open requests on users with them plus
    # any request that they've accepted
    sample_id = 1
    response = client.get(endpoint(sample_id))
    assert response.status_code == 200
    for task in TASK_DATA:
        # open requests for sample_id
        if 'accepted_at' not in task and task['requested_by'] == sample_id:
            assert task['summary'] in response.text
            continue
        # requests from logged in user accepted by this user
        if 'completed_at' not in task and task['requested_by'] == test_user_id\
                and task['accepted_by'] == sample_id:
            assert task['summary'] in response.text
            continue
        assert task['summary'] not in response.text

    # And their own profile should show both requests and all accepted tasks
    response = client.get(endpoint(test_user_id))
    assert response.status_code == 200
    for task in TASK_DATA:
        # open requests by the user themselves
        if 'accepted_at' not in task and task['requested_by'] == test_user_id:
            assert task['summary'] in response.text
            continue
        # requests from other users accepted by the logged in user
        if 'completed_at' not in task and\
          (('accepted_at' in task and task['accepted_by'] == test_user_id)\
             or task['requested_by'] == test_user_id):
            assert task['summary'] in response.text
            continue
        assert task['summary'] not in response.text

def test_edit_user(client:FlaskClient) -> None:
    '''Tests the endpoint `/users/edit`.'''

    # Future-proofing
    endpoint = '/users/edit'
    new_data = {
        'username':'test-1',
        'headline':'minus one',
        'bio':'godzilla is my favorite franchise that I do not like.'
    }

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
    # And the old profile data is not present
    assert response.request.path == f'/users/{sample_index + 1}'
    assert new_data['username'] in response.text
    assert new_data['headline'] in response.text
    assert new_data['bio'] in response.text
    assert 'None' not in response.text
    assert credentials['username'] not in response.text

    # Update fields back to old values 1 at a time to test single edits
    credentials['headline'] = 'goddammit'
    credentials['bio'] = 'ooh you said #11'
    for field in ['username', 'headline', 'bio']:
        value = credentials[field]
        response = client.post(endpoint,
                               data={field:value, 'csrf_token':g.csrf_token},
                               follow_redirects=True)
        assert response.status_code == 200

    # If logged out, both GET and POST should redirect to login
    client.get('/logout')
    assert_redirect(client.get(endpoint))
    assert_redirect(client.post(endpoint, data=new_data))

def test_edit_credentials(client:FlaskClient) -> None:
    '''Tests the endpoint `/users/edit/credentials`.'''

    # Future-proofing
    endpoint = '/users/edit/credentials'
    new_login = {
        'email': 'user-1@test.net',
        'password': 'pass-1',
    }
    final_login = {
        'email':'user-2@test.net',
        'password':'pass-2',
        'current_password': new_login['password']
    }
    new_login['confirm_password'] = new_login['password']
    final_login['confirm_password'] = final_login['password']

    # Log a sample user into the service
    sample_index = randint(0, len(USER_DATA)-1)
    old_login = USER_DATA[sample_index]
    new_login['current_password'] = old_login['password']
    authenticate_user(credentials=old_login, client=client)

    # For GET requests, see the form pre-populated with their email,
    # but NOT the password
    response = client.get(endpoint)
    assert response.status_code == 200
    assert old_login['email'] in response.text
    assert old_login['password'] not in response.text

    # For POST requests, will fail and redirect to form if...

    # ...New passwords don't match
    invalid_login = new_login.copy()
    invalid_login['password'] = 'pass-2'
    response = client.post(endpoint,
                           data={'csrf_token':g.csrf_token, **invalid_login},
                           follow_redirects=True)
    assert response.status_code == 400
    assert response.request.path == endpoint

    # ...Old password is incorrect
    invalid_login = new_login.copy()
    invalid_login['current_password'] = 'pass-2'
    response = client.post(endpoint,
                           data={'csrf_token':g.csrf_token, **invalid_login},
                           follow_redirects=True)
    assert response.status_code == 400
    assert response.request.path == endpoint

    # ...CSRF token is missing
    response = client.post(endpoint, data=new_login, follow_redirects=True)
    assert response.status_code == 400
    assert response.request.path == endpoint

    # Otherwise, will pass if all fields are present and redirect to the
    # user's profile page
    redirect = f'/users/{sample_index + 1}'
    response = client.post(endpoint,
                           data={'csrf_token':g.csrf_token, **new_login},
                           follow_redirects=True)
    assert response.status_code == 200
    assert response.request.path == redirect

    # Or just an email update
    just_email = final_login.copy()
    del just_email['password']
    del just_email['confirm_password']
    response = client.post(endpoint,
                           data={'csrf_token':g.csrf_token, **just_email},
                           follow_redirects=True)
    assert response.status_code == 200
    assert response.request.path == redirect

    # Or just a password update
    just_password = final_login.copy()
    del just_password['email']
    response = client.post(endpoint,
                           data={'csrf_token':g.csrf_token, **just_password},
                           follow_redirects=True)
    assert response.status_code == 200
    assert response.request.path == redirect

    # If logged out, both GET and POST should redirect to login
    client.get('/logout')
    assert_redirect(client.get(endpoint))
    assert_redirect(client.post(endpoint, data={'csrf_token':g.csrf_token,
                                                **final_login}))

    # Logging in with the old credentials shouldn't work
    response = authenticate_user(credentials=old_login, client=client)
    assert response.status_code == 400

    # But logging in with the old username should be fine
    response = authenticate_user(credentials=final_login, client=client)
    assert response.status_code == 200
