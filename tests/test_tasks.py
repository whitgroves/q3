'''Tests for the task endpoints of qqueue.'''

from random import choice, randint
from flask import g # globals - needed for CSRF token
from flask.testing import FlaskClient
from tests.conftest import USER_DATA, TASK_DATA, authenticate_user

def test_index(client:FlaskClient) -> None:
    '''Tests the endpoint /tasks'''
    endpoint = '/tasks'
    
    # Summaries, rewards, and due dates of all unaccepted tasks are visible
    # (but nothing else) even when logged out
    response = client.get(endpoint)
    assert response.status_code == 200
    for task in TASK_DATA:
        if 'accepted_by' in task:
            assert task['summary'] not in response.text
            assert task['reward_amount'] not in response.text
            assert task['reward_currency'] not in response.text
            assert task['due_by'] not in response.text
            assert task['accepted_by'] not in response.text
            assert task['accepted_at'] not in response.text
        else:
            assert task['summary'] in response.text
            assert task['reward_amount'] in response.text
            assert task['reward_currency'] in response.text
            assert task['due_by'] in response.text
        assert task['requested_by'] not in response.text
        assert task['detail'] not in response.text

    # But when logged in, detail + previous fields should be visible
    authenticate_user(credentials=choice(USER_DATA), client=client)
    response = client.get(endpoint)
    assert response.status_code == 200
    for task in TASK_DATA:
        if 'accepted_by' in task:
            assert task['summary'] not in response.text
            assert task['reward_amount'] not in response.text
            assert task['reward_currency'] not in response.text
            assert task['due_by'] not in response.text
            assert task['accepted_by'] not in response.text
            assert task['accepted_at'] not in response.text
            assert task['requested_by'] not in response.text
            assert task['detail'] not in response.text
        else:
            assert task['summary'] in response.text
            assert task['reward_amount'] in response.text
            assert task['reward_currency'] in response.text
            assert task['due_by'] in response.text
            assert task['requested_by'] in response.text
            assert task['detail'] in response.text

def test_get_task(client:FlaskClient) -> None:
    '''Tests the endpoint /tasks/<task_id>'''
    pass

def test_new_task(client:FlaskClient) -> None:
    '''Tests the endpoint /tasks/new'''
    pass

def test_edit_task(client:FlaskClient) -> None:
    '''Tests the endpoint /tasks/<task_id>/edit'''
    pass

def test_delete_task(client:FlaskClient) -> None:
    '''Tests the endpoint /tasks/<task_id>/delete'''
    pass

def test_accept_task(client:FlaskClient) -> None:
    '''Tests the endpoint /tasks/<task_id>/accept'''
    pass

def test_complete_task(client:FlaskClient) -> None:
    '''Tests the endpoint /tasks/<task_id>/complete'''
    pass

def test_approve_task(client:FlaskClient) -> None:
    '''Tests the endpoint /tasks/<task_id>/approve'''
    pass

def test_reject_task(client:FlaskClient) -> None:
    '''Tests the endpoint /tasks/<task_id>/reject'''
    pass

def test_requested_by(client:FlaskClient) -> None:
    '''Tests the endpoint /tasks/requested/<user_id>'''
    pass

def test_accepted_by(client:FlaskClient) -> None:
    '''Tests the endpoint /tasks/accepted/<user_id>'''
    pass
