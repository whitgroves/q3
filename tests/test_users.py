"""Test for the post routes of q3.

This test relies on using flask's global app context to generate/fetch CSRF
tokens for protected forms. See test_auth.py for full explanation.
"""
import flask
from flask import testing
from .conftest import user_data

user0 = user_data[0]
user1 = user_data[1]

def test_index(client:testing.FlaskClient) -> None:
    # Page loads with all info
    response = client.get('/users/')
    assert all(u['username'] in response.text for u in user_data)

def test_user(client:testing.FlaskClient) -> None:
    # Page loads with all info
    response = client.get('/users/1')
    assert user_data[0]['email'] in response.text

def test_edit(client:testing.FlaskClient) -> None:
    # Setup - login
    client.get('/login') # creates CSRF token - do NOT move
    login_data = {'csrf_token': flask.g.csrf_token,
                  'user_email': user0['email'],
                  'password': user0['password']}
    client.post('/login', data=login_data) #pylint: disable=duplicate-code

    # Page loads with all info (when signed in)
    response_get_valid = client.get('/users/1/edit')
    assert all(x in response_get_valid.text for x in ['Email',
                                                      'Username',
                                                      'Bio',
                                                      'Update',
                                                      'Delete'])

    # User data is updated successfully
    bio = 'Not turtle-y enough for the turtle club.'
    update_data_valid = {'csrf_token': flask.g.csrf_token, 'bio': bio, **user0}
    response_post_valid = client.post('/users/1/edit',
                                      data=update_data_valid,
                                      follow_redirects=True)
    assert response_post_valid.status_code == 200
    assert response_post_valid.request.path == '/users/1'

    # Confirm user is redirected to profile after edit
    assert bio in response_post_valid.text

    # Cannot update without CSRF token
    update_data_no_token = {'bio': "That boy ain't right.", **user0}
    response_post_no_token = client.post('/users/1/edit',
                                         data=update_data_no_token)
    assert response_post_no_token.status_code == 400

    # Cannot update email to existing address on another account
    update_data_duplicate = {'csrf_token': flask.g.csrf_token,
                             'email': user1['email']}
    response_duplicate = client.post('/users/1/edit',
                                     data=update_data_duplicate)
    assert response_duplicate.status_code == 400

    # Cannot update another account
    update_data_wrong_account = {'csrf_token': flask.g.csrf_token, **user1}
    response_wrong_account = client.post('/users/2/edit',
                                         data=update_data_wrong_account)
    assert response_wrong_account.status_code == 403

    # Cannot update when logged out; redirects to login
    client.get('/logout')
    response_no_login = client.post('/users/1/edit', data=update_data_valid)
    assert response_no_login.status_code == 302
    assert response_no_login.location[:6] == '/login' # some params are appended
