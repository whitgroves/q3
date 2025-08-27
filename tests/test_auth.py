"""Test for the auth routes of qqueue.

For this and other tests against CSRF forms, we do a little wizardry based on
https://gist.github.com/singingwolfboy/2fca1de64950d5dfed72?permalink_comment_id=4556252#gistcomment-4556252
to interact with protected forms without having to set WTF_CSRF_ENABLED=False in
the TestConfig. Essentially, any GET request will generate a valid CSRF token,
which can then be pulled from flask's global app context (g.csrf_token). 

Notably, a GET request to any CSRF-enabled page will generate the token --
e.g., GET -> /login followed by POST -> /register will still work.
"""
from flask import g #globals
from flask.testing import FlaskClient
from tests.conftest import USER_DATA, authenticate_user

def test_register(client:FlaskClient) -> None:
    '''Tests the `/register` endpoint of the app.'''

    # Manually create CSRF token since user cannot login yet
    response = client.get('/register')

    # All fields present on form
    assert all(x in response.text for x in ['Email', 'Username', 'Password'])

    # Registration denied without CSRF token
    registration = {'email': 'auth@test.net',
                    'password': 'authtest',
                    'username': 'authtest',
                    'confirm_password': 'authtest'}
    response = client.post('/register', data=registration)
    assert response.status_code == 400

    # Registration accepted with CSRF token and redirects to login on success
    with_token = {'csrf_token':g.csrf_token, **registration}
    response = client.post('/register', data=with_token, follow_redirects=True)
    assert response.status_code == 200
    assert len(response.history) == 1
    assert response.request.path == '/login'

    # Duplicate email is rejected, even with token
    response = client.post('/register', data=with_token)
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
    # All fields present on form
    response = client.get('/login') # creates CSRF token - do NOT move
    assert all(x in response.text for x in ['Email or Username', 'Password'])

    # User can login with email and is redirected to homepage
    credentials = USER_DATA[0]
    with_email = {'csrf_token': g.csrf_token,
                  'email_or_username': credentials['email'],
                  'password': credentials['password']}
    response = client.post('/login', data=with_email, follow_redirects=True)
    assert response.status_code == 200
    assert len(response.history) == 1
    assert response.request.path == '/'

    # User can login with username and is redirected to homepage
    with_username = {'csrf_token': g.csrf_token,
                    'email_or_username': credentials['username'],
                    'password':credentials['password']}
    response = client.post('/login', data=with_username, follow_redirects=True)
    assert response.status_code == 200
    assert len(response.history) == 1
    assert response.request.path == '/'

    # Login denied without CSRF token, even with valid credentials
    no_token = {'email_or_username': credentials['email'],
                'password': credentials['password']}
    response = client.post('/login', data=no_token)
    assert response.status_code == 400

    # Login denied with invalid password, even with CSRF token
    bad_password = {'csrf_token': g.csrf_token,
                    'email_or_username':credentials['email'],
                    'password': 'wrong'}
    response = client.post('/login', data=bad_password)
    assert response.status_code == 400

    # Login denied with non-registered email
    bad_email = {'csrf_token': g.csrf_token,
                 'email_or_username': 'user@wrong.com',
                 'password': credentials['password']}
    response = client.post('/login', data=bad_email)
    assert response.status_code == 400

    # Login denied with non-registered username
    bad_username = {'csrf_token': g.csrf_token,
                    'email_or_username': 'not_a_user',
                    'password': credentials['password']}
    response = client.post('/login', data=bad_username)
    assert response.status_code == 400

def test_logout(client:FlaskClient) -> None:
    '''Tests the `/logout` endpoint of the app.'''
    
    # Setup by logging in
    authenticate_user(credentials=USER_DATA[0], client=client)

    # Logout redirects to the homepage
    response = client.get('/logout', follow_redirects=True)
    assert response.status_code == 200
    assert len(response.history) == 1
    assert response.request.path == '/'
