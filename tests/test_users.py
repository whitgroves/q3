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
    client.get('/auth/logout')

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
    client.get('/auth/logout')
    assert_redirect(client.get(endpoint))
    assert_redirect(client.post(endpoint, data=new_data))
