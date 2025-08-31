'''Tests for the task endpoints of qqueue.'''

from random import choice, randint
from flask import g # globals - needed for CSRF token
from flask.testing import FlaskClient
from tests.conftest import USER_DATA, TASK_DATA, Task, date, timedelta, authenticate_user
from qqueue.config import ACCEPTED_CURRENCIES

def test_index(client:FlaskClient) -> None: # pylint: disable=too-many-statements
    '''Tests the endpoint /tasks'''

    # Future-proofing
    endpoint = '/tasks/'
    logged_in_with_tasks_text = [
        "<p>Here are today's open requests:</p>",
        '<p>Need your own task done? <a href=',
        '>Click here</a> to create a request.</p>',
    ]
    logged_out_with_tasks_text = [
        '>Register now</a> to view, create, and complete tasks like:</p>',
        '<p>Already registered? <a href=',
        '>Click here</a> to login.</p>',
    ]
    logged_in_no_tasks_text = [
        '<p>There are no open requests at this time.</p>',
        '>Create one</a> or see <a href=',
        '>who else</a> is on qqueue.</p>',
    ]
    logged_out_no_tasks_text = [
        '>Login</a> or <a href=',
        '>register</a> to view, create, and complete tasks.</p>',
    ]

    # When logged out, summaries of 5 unclaimed tasks with the nearest due
    # dates are visible, but nothing else
    response = client.get(endpoint)
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
        assert USER_DATA[task['requested_by']-1]['username'] not in response.text # pylint: disable=line-too-long
    assert tasks_seen == 5
    assert all(text not in response.text for text in logged_in_with_tasks_text)
    assert all(text in response.text for text in logged_out_with_tasks_text)
    assert all(text not in response.text for text in logged_in_no_tasks_text)
    assert all(text not in response.text for text in logged_out_no_tasks_text)

    # But when logged in, summaries, details, requester, due date, and rewards
    # should be visible for all unclaimed tasks in the system
    authenticate_user(credentials=choice(USER_DATA), client=client)
    response = client.get(endpoint)
    assert response.status_code == 200
    for task in TASK_DATA:
        if 'accepted_by' in task:
            assert task['summary'] not in response.text
            assert task['detail'] not in response.text
            assert str(task['reward_amount']) not in response.text
            assert task['reward_currency'] not in response.text
            assert str(task['due_by']) not in response.text
            assert str(task['accepted_at']) not in response.text
            # cannot check for absence of user links since there are 2 of them
            # and either could have a value the other isn't supposed to
        else:
            assert task['summary'] in response.text
            assert task['detail'] in response.text
            assert str(task['reward_amount']) in response.text
            assert task['reward_currency'] in response.text
            assert str(task['due_by']) in response.text
            assert f'/users/{task["requested_by"]}' in response.text
    assert all(text in response.text for text in logged_in_with_tasks_text)
    assert all(text not in response.text for text in logged_out_with_tasks_text)
    assert all(text not in response.text for text in logged_in_no_tasks_text)
    assert all(text not in response.text for text in logged_out_no_tasks_text)

    # Now delete *unaccepted* tasks to test scenario where
    # no tasks should be displayed
    Task.query.filter(Task.accepted_at == None).delete(synchronize_session=False) # pylint: disable=line-too-long, singleton-comparison

    # The user is still logged in, so test that scenario first
    response = client.get(endpoint)
    assert response.status_code == 200
    for task in TASK_DATA:
        assert task['summary'] not in response.text
        assert task['detail'] not in response.text
        assert str(task['reward_amount']) not in response.text
        assert task['reward_currency'] not in response.text
        assert str(task['due_by']) not in response.text
    assert all(text not in response.text for text in logged_in_with_tasks_text)
    assert all(text not in response.text for text in logged_out_with_tasks_text)
    assert all(text in response.text for text in logged_in_no_tasks_text)
    assert all(text not in response.text for text in logged_out_no_tasks_text)

    # Then logout and repeat the check, but for a different message
    client.get('/logout')
    response = client.get(endpoint)
    assert response.status_code == 200
    for task in TASK_DATA:
        assert task['summary'] not in response.text
        assert task['detail'] not in response.text
        assert str(task['reward_amount']) not in response.text
        assert task['reward_currency'] not in response.text
        assert str(task['due_by']) not in response.text
    assert all(text not in response.text for text in logged_in_with_tasks_text)
    assert all(text not in response.text for text in logged_out_with_tasks_text)
    assert all(text not in response.text for text in logged_in_no_tasks_text)
    assert all(text in response.text for text in logged_out_no_tasks_text)

def test_new_task(client:FlaskClient) -> None:
    '''Tests the endpoint /tasks/new'''

    # Future-proofing
    endpoint = '/tasks/new'
    new_task = {'summary':'create a new task',
                'detail':'lorem ipsum si dolor amet',
                'reward_amount': 420.0,
                'reward_currency': 'USD',
                'due_by':date.today()+timedelta(7)}

    # While logged out, both GET and POST requests redirect to login
    redirect = '/login'
    for response in [client.get(endpoint), client.post(endpoint)]:
        assert response.status_code == 302
        assert response.location[:len(redirect)] == redirect

    # User can view the form while logged in
    authenticate_user(credentials=choice(USER_DATA), client=client)
    response = client.get(endpoint)
    assert response.status_code == 200
    assert all(field.replace('_', ' ') in response.text.lower()
               for field in new_task)

    # User can create a task while logged in, with a redirect to the new task
    redirect = f'/tasks/{len(TASK_DATA)+1}'
    response = client.post(endpoint,
                           data={'csrf_token':g.csrf_token, **new_task},
                           follow_redirects=True)
    assert response.status_code == 200
    assert response.request.path == redirect
    assert all(str(text) in response.text for text in new_task.values())

    # Now try again without the CSRF token; request should fail (400)
    redirect = f'/tasks/{len(TASK_DATA)+2}'
    response = client.post(endpoint, data=new_task)
    assert response.status_code == 400

    # Request should also fail if any of the required fields are missing and
    # redirect back to the new task form. `new_task` includes only these, so
    # we loop through the keys and try to send copies missing each one
    for field in new_task:
        invalid_task = new_task.copy()
        del invalid_task[field]
        response = client.post(endpoint,
                               data={'csrf_token':g.csrf_token,
                                     **invalid_task},
                               follow_redirects=True)
        assert response.status_code == 400
        assert response.request.path == endpoint

    # The same behavior is true if a non-accepted currency is entered
    invalid_currency = 'NOGOOD'
    assert invalid_currency not in ACCEPTED_CURRENCIES # sanity check
    invalid_task = new_task.copy()
    invalid_task['reward_currency'] = invalid_currency
    response = client.post(endpoint,
                           data={'csrf_token':g.csrf_token,
                                 **invalid_task},
                           follow_redirects=True)
    assert response.status_code == 400
    assert response.request.path == endpoint

def test_get_task(client:FlaskClient) -> None:
    '''Tests the endpoint /tasks/<task_id>'''
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

def test_decline_task(client:FlaskClient) -> None:
    '''Tests the endpoint /tasks/<task_id>/decline'''
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
