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
from tests.conftest import user_data

user = user_data[0]

def test_register(client:FlaskClient) -> None:
    # All fields present on form
    response_get = client.get('/register') # creates CSRF token - do NOT move
    assert all(x in response_get.text
               for x in ['Email', 'Username', 'Password'])

    # Registration denied without CSRF token
    register_user_data = {'email': 'auth@test.net',
                          'password': 'authtest',
                          'username': 'authtest',
                          'confirm_password': 'authtest'}
    response_post_no_csrf = client.post('/register', data=register_user_data)
    assert response_post_no_csrf.status_code == 400

    # Registration accepted with CSRF token and redirects to login on success
    post_data_csrf = {'csrf_token':g.csrf_token, **register_user_data}
    response_post_csrf = client.post('/register',
                                     data=post_data_csrf,
                                     follow_redirects=True)
    assert response_post_csrf.status_code == 200
    assert len(response_post_csrf.history) == 1
    assert response_post_csrf.request.path == '/login'

    # Duplicate email is rejected, even with token
    response_post_dupe = client.post('/register', data=post_data_csrf)
    assert response_post_dupe.status_code == 400

def test_login(client:FlaskClient) -> None:
    # All fields present on form
    response_get = client.get('/login') # creates CSRF token - do NOT move
    assert all(x in response_get.text
               for x in ['Email or Username', 'Password'])

    # User can login with email and is redirected to homepage
    post_data_email = {'csrf_token': g.csrf_token,
                       'email_or_username': user['email'],
                       'password': user['password']}
    response_post_email = client.post('/login',
                                      data=post_data_email,
                                      follow_redirects=True)
    assert response_post_email.status_code == 200
    assert len(response_post_email.history) == 1
    assert response_post_email.request.path == '/'

    # User can login with username and is redirected to homepage
    post_data_username = {'csrf_token': g.csrf_token,
                          'email_or_username': user['username'],
                          'password':user['password']}
    response_post_username = client.post('/login',
                                         data=post_data_username,
                                         follow_redirects=True)
    assert response_post_username.status_code == 200
    assert len(response_post_username.history) == 1
    assert response_post_username.request.path == '/'

    # Login denied without CSRF token, even with valid credentials
    post_data_no_csrf = {'email_or_username': user['email'],
                         'password': user['password']}
    response_post_no_csrf = client.post('/login', data=post_data_no_csrf)
    assert response_post_no_csrf.status_code == 400

    # Login denied with invalid password, even with CSRF token
    post_data_bad_password = {'csrf_token': g.csrf_token,
                              'email_or_username':user['email'],
                              'password': 'wrong'}
    response_post_bad_password = client.post('/login',
                                             data=post_data_bad_password)
    assert response_post_bad_password.status_code == 400

    # Login denied with non-registered email
    post_data_bad_email = {'csrf_token': g.csrf_token,
                           'email_or_username': 'user@wrong.com',
                           'password': user['password']}
    response_post_bad_email = client.post('/login', data=post_data_bad_email)
    assert response_post_bad_email.status_code == 400

    # Login denied with non-registered username
    post_data_bad_username = {'csrf_token': g.csrf_token,
                              'email_or_username': 'not_a_user',
                              'password': user['password']}
    response_post_bad_username = client.post('/login',
                                             data=post_data_bad_username)
    assert response_post_bad_username.status_code == 400

def test_logout(client:FlaskClient) -> None:
    # Setup - login
    client.get('/login') # creates CSRF token - do NOT move
    login_data = {'csrf_token': g.csrf_token,
                  'email_or_username': user['email'],
                  'password': user['password']}
    client.post('/login', data=login_data)

    # Logout redirects to the homepage
    response = client.get('/logout', follow_redirects=True)
    assert response.status_code == 200
    assert len(response.history) == 1
    assert response.request.path == '/'
