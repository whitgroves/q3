'''Tests for the task endpoints of qqueue.'''

from random import choice, randint
from flask import g # globals - needed for CSRF token
from flask.testing import FlaskClient
from tests.conftest import USER_DATA, TASK_DATA, authenticate_user

def test_index(client:FlaskClient) -> None:
    '''Tests the endpoint /tasks'''
    endpoint = '/tasks'
    
    # When logged out, summaries of 5 unclaimed tasks with the nearest due
    # dates are visible, but nothing else
    response = client.get(endpoint, follow_redirects=True)
    assert response.status_code == 200
    tasks_seen = 0
    for i, task in enumerate(TASK_DATA):
        # Tasks 0 and 1 are accepted, so should only see 2, 3, 4, 5, and 6
        if i > 6 or 'accepted_by' in task:
            assert task['summary'] not in response.text
        else:
            assert task['summary'] in response.text
            tasks_seen += 1
        assert task['detail'] not in response.text
        assert str(task['reward_amount']) not in response.text
        assert task['reward_currency'] not in response.text
        assert str(task['due_by']) not in response.text
        assert USER_DATA[task['requested_by']-1]['username'] not in response.text
    assert tasks_seen == 5

    # But when logged in, summaries, details, requester, due date, and rewards
    # should be visible for all unclaimed tasks in the system
    authenticate_user(credentials=choice(USER_DATA), client=client)
    response = client.get(endpoint, follow_redirects=True)
    assert response.status_code == 200
    for task in TASK_DATA:
        if 'accepted_by' in task:
            assert task['summary'] not in response.text
            assert task['detail'] not in response.text
            assert str(task['reward_amount']) not in response.text
            assert task['reward_currency'] not in response.text
            assert str(task['due_by']) not in response.text
            # assert USER_DATA[task['accepted_by']-1]['username'] not in response.text
            assert str(task['accepted_at']) not in response.text
            # assert USER_DATA[task['requested_by']-1]['username'] not in response.text
        else:
            assert task['summary'] in response.text
            assert task['detail'] in response.text
            assert str(task['reward_amount']) in response.text
            assert task['reward_currency'] in response.text
            assert str(task['due_by']) in response.text
            assert f'/users/{task["requested_by"]}' in response.text

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
