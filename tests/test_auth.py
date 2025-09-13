"""Test for the auth routes of qqueue."""

from random import randint
from secrets import token_hex
from flask import g #globals
from flask.testing import FlaskClient
from tests.conftest import USER_DATA, authenticate_user, assert_redirect

def test_register(client:FlaskClient) -> None:
    '''Tests the `/register` endpoint of the app.'''

    # Future-proofing
    endpoint = '/auth/register'

    # Manually create CSRF token since user cannot login yet
    response = client.get(endpoint)

    # All fields present on form
    assert all(x in response.text for x in ['Email', 'Username', 'Password'])

    # Registration denied without CSRF token
    registration = {'email': 'auth@test.net',
                    'password': 'authtest',
                    'username': 'authtest',
                    'address': f'0x{token_hex(20)}',
                    'confirm_password': 'authtest'}
    response = client.post(endpoint, data=registration)
    assert response.status_code == 400

    # Registration accepted with CSRF token and redirects to login on success
    with_token = {'csrf_token':g.csrf_token, **registration}
    response = client.post(endpoint, data=with_token, follow_redirects=True)
    assert response.status_code == 200
    assert len(response.history) == 1
    assert response.request.path == '/auth/login'

    # Duplicate email is rejected, even with token
    response = client.post(endpoint, data=with_token)
    assert response.status_code == 400

    # User can authenticate with newly created credentials
    response = authenticate_user(credentials=registration, client=client)
    assert response.status_code == 200

def test_login(client:FlaskClient) -> None:
    '''
    Tests the `/login` endpoint of the app. 
    
    Does not use `authenticate_user` since it assumes that `/login`
    works without testing it, which is the point of this function.
    '''
    # Future-proofing
    endpoint = '/auth/login'

    # All fields present on form
    response = client.get(endpoint) # creates CSRF token - do NOT move
    assert all(x in response.text for x in ['Email or Username', 'Password'])

    # User can login with email and is redirected to homepage
    credentials = USER_DATA[0]
    with_email = {'csrf_token': g.csrf_token,
                  'email_or_username': credentials['email'],
                  'password': credentials['password']}
    response = client.post(endpoint, data=with_email, follow_redirects=True)
    assert response.status_code == 200
    assert len(response.history) == 1
    assert response.request.path == '/'

    # User can login with username and is redirected to homepage
    with_username = {'csrf_token': g.csrf_token,
                    'email_or_username': credentials['username'],
                    'password':credentials['password']}
    response = client.post(endpoint, data=with_username, follow_redirects=True)
    assert response.status_code == 200
    assert len(response.history) == 1
    assert response.request.path == '/'

    # Login denied without CSRF token, even with valid credentials
    no_token = {'email_or_username': credentials['email'],
                'password': credentials['password']}
    response = client.post(endpoint, data=no_token)
    assert response.status_code == 400

    # Login denied with invalid password, even with CSRF token
    bad_password = {'csrf_token': g.csrf_token,
                    'email_or_username':credentials['email'],
                    'password': 'wrong'}
    response = client.post(endpoint, data=bad_password)
    assert response.status_code == 400

    # Login denied with non-registered email
    bad_email = {'csrf_token': g.csrf_token,
                 'email_or_username': 'user@wrong.com',
                 'password': credentials['password']}
    response = client.post(endpoint, data=bad_email)
    assert response.status_code == 400

    # Login denied with non-registered username
    bad_username = {'csrf_token': g.csrf_token,
                    'email_or_username': 'not_a_user',
                    'password': credentials['password']}
    response = client.post(endpoint, data=bad_username)
    assert response.status_code == 400

def test_logout(client:FlaskClient) -> None:
    '''Tests the `/logout` endpoint of the app.'''

    # Setup by logging in
    authenticate_user(credentials=USER_DATA[0], client=client)

    # Logout redirects to the homepage
    response = client.get('/auth/logout', follow_redirects=True)
    assert response.status_code == 200
    assert len(response.history) == 1
    assert response.request.path == '/'

def test_edit(client:FlaskClient) -> None:
    '''Tests the endpoint `/auth/edit`.'''

    # Future-proofing
    endpoint = '/auth/edit'
    new_creds = {
        'email': 'user-1@test.net',
        'password': 'pass-1',
        'address': f'0x{token_hex(20)}',
    }
    final_creds = {
        'email':'user-2@test.net',
        'password':'pass-2',
        'address': f'0x{token_hex(20)}',
        'current_password': new_creds['password']
    }
    new_creds['confirm_password'] = new_creds['password']
    final_creds['confirm_password'] = final_creds['password']
    final_creds['current_password'] = new_creds['password']

    # Log a sample user into the service
    sample_index = randint(0, len(USER_DATA)-1)
    old_creds = USER_DATA[sample_index]
    new_creds['current_password'] = old_creds['password']
    authenticate_user(credentials=old_creds, client=client)

    # For GET requests, see the form pre-populated with their email,
    # but NOT the password
    response = client.get(endpoint)
    assert response.status_code == 200
    assert old_creds['email'] in response.text
    assert old_creds['password'] not in response.text
    assert old_creds['address'] in response.text

    # For POST requests, will fail and redirect to form if...

    # ...New passwords don't match
    invalid_login = new_creds.copy()
    invalid_login['password'] = 'pass-2'
    response = client.post(endpoint,
                           data={'csrf_token':g.csrf_token, **invalid_login},
                           follow_redirects=True)
    assert response.status_code == 400
    assert response.request.path == endpoint

    # ...Old password is incorrect
    invalid_login = new_creds.copy()
    invalid_login['current_password'] = 'pass-2'
    response = client.post(endpoint,
                           data={'csrf_token':g.csrf_token, **invalid_login},
                           follow_redirects=True)
    assert response.status_code == 400
    assert response.request.path == endpoint

    # ...CSRF token is missing
    response = client.post(endpoint, data=new_creds, follow_redirects=True)
    assert response.status_code == 400
    assert response.request.path == endpoint

    # Otherwise, will pass if all fields are present and redirect to the
    # user's profile page
    redirect = f'/users/{sample_index + 1}'
    response = client.post(endpoint,
                           data={'csrf_token':g.csrf_token, **new_creds},
                           follow_redirects=True)
    assert response.status_code == 200
    assert response.request.path == redirect

    # Or just an email update
    just_email = final_creds.copy()
    del just_email['password']
    del just_email['confirm_password']
    del just_email['address']
    response = client.post(endpoint,
                           data={'csrf_token':g.csrf_token, **just_email},
                           follow_redirects=True)
    assert response.status_code == 200
    assert response.request.path == redirect

    # Or just an address update
    just_address = final_creds.copy()
    del just_address['email']
    del just_address['password']
    del just_address['confirm_password']
    response = client.post(endpoint,
                           data={'csrf_token':g.csrf_token, **just_address},
                           follow_redirects=True)
    assert response.status_code == 200
    assert response.request.path == redirect

    # Or just a password update
    just_password = final_creds.copy()
    del just_password['email']
    del just_password['address']
    response = client.post(endpoint,
                           data={'csrf_token':g.csrf_token, **just_password},
                           follow_redirects=True)
    assert response.status_code == 200
    assert response.request.path == redirect

    # If logged out, both GET and POST should redirect to login
    client.get('/auth/logout')
    assert_redirect(client.get(endpoint))
    assert_redirect(client.post(endpoint, data={'csrf_token':g.csrf_token,
                                                **final_creds}))

    # Logging in with the old credentials shouldn't work
    response = authenticate_user(credentials=old_creds, client=client)
    assert response.status_code == 400

    # But logging in with the old username should be fine
    response = authenticate_user(credentials=final_creds, client=client)
    assert response.status_code == 200
