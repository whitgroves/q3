'''Test for the order routes of qqueue.'''

from random import randint
from datetime import date
from typing_extensions import Any
from flask import Response, g # globals
from flask.testing import FlaskClient
from tests.conftest import user_data, task_data, comment1_data, comment2_data

def login(client:FlaskClient, user_idx:int) -> None:
    '''
    Helper to authenticate test user requests.

    First makes a GET request to generate a CSRF token, 
    then uses that token (via flask.g.csrf_token) to log in.

    Since this is not a `test_` method, does not have access 
    to test fixtures; `client` must be passed manually.
    '''
    client.get('/login')
    login_data = {'csrf_token': g.csrf_token,
                  'email_or_username': user_data[user_idx]['email'],
                  'password': user_data[user_idx]['password']}
    client.post('/login', data=login_data)

def test_index(client:FlaskClient) -> None:
    # Page loads with all tasks listed
    response = client.get('/tasks')
    assert response.status_code == 200
    for task in task_data:
        assert all(field in response.text for field in task.values())
    
def test_task(client:FlaskClient) -> None:
    # Page loads with all task fields and comments
    task_id = randint(1, len(task_data)) # random sample, db ID's start at 1
    response = client.get(f'/tasks/{task_id}')
    assert response.status_code == 200
    assert all(field in response.text for field in task_data[task_id].values())
    assert all(comment in response.text for comment in comment1_data)
    assert all(comment in response.text for comment in comment2_data)

    # Redirect to index on non-extant task id
    response = client.get(f'/tasks/{len(task_data)+1}', follow_redirects=True)
    assert response.status_code == 200
    assert response.request.path == '/tasks/'

def test_new_task(client:FlaskClient) -> None:
    # Login as random user to generate csrf token
    login(client=client, user_idx=randint(0, len(user_data)-1))

    # Helper to future-proof requests
    def create_task(task:dict, token:Any=g.csrf_token) -> Response:
        return client.post('/tasks/new', data={'csrf_token':token, **task}, follow_redirects=True)

    # New task is created successfully
    task_valid = {'title':'New Task', 'description':'7 red lines', 'due':date(2025, 9, 1)} # pylint: disable=line-too-long
    response = create_task(task_valid)
    assert response.status_code == 200
    assert response.request.path == f'/tasks/{len(task_data)+1}'
    assert all(field in response.text for field in task_valid.values())
    
    # New tasks must have a title
    task_no_title = {'description':'untitled', 'due':date(2025, 9, 1)}
    response = create_task(task_no_title)
    assert response.status_code == 400

    # New tasks must have a due date
    task_no_due_date = {'title':'Procrastinate', 'description':'do it tomorrow'}
    response = create_task(task_no_due_date)
    assert response.status_code == 400

    # Can't create task without token
    response = create_task(task_valid, token='')
    assert response.status_code == 400

    # Can't create task while logged out; redirects to login
    task_logged_out = {'title':'logout', 'description':'throw some', 'due':date(2026, 9, 1)} # pylint: disable=line-too-long
    client.get('/logout')
    response = create_task(task_logged_out)
    assert response.status_code == 302
    assert response.location.startswith('/login')

    # Confirm task was not created despite redirect
    all_tasks = client.get('/tasks/')
    assert all(field not in all_tasks.text for field in task_logged_out.values())

def test_edit_task(client:FlaskClient) -> None:
    # Login as random user to generate csrf token
    login(client=client, user_idx=randint(0, len(user_data)-1))

    # Helper to future-proof requests
    def edit_task(task_id:int, task:dict, token:Any=g.csrf_token) -> Response:
        return client.post(f'/tasks/{task_id}/edit', data={'csrf_token':token, **task}, follow_redirects=True)
    
    # Task can only be edited by the associated user and no one else.
    # Tasks are assigned randomly for testing, so we sample a random task and loop through all users
    # to ensure only 1 can edit it.
    # When that one is found, we run other sub-tests as well (e.g., updating only 1 field at a time)
    
    successful_updates = 0
    task_id = randint(1, len(task_data))
    
    for i in range(len(user_data)):

        # Attempt to update the task while logged in as each user
        login(client=client, user_idx=i)
        task_valid = {'title':'Updated Task', 'description':'2 in green ink', 'due':date(2025, 9, 2)} # pylint: disable=line-too-long
        response = edit_task(task_id, task_valid)

        # Skip to next user if the edit failed
        if response.status_code != 200: continue
        
        # On successful edit, redirect to task page with updates visible
        assert response.request.path == f'/tasks/{task_id}'
        assert all(field in response.text for field in task_valid.values())

        # Only one user can update the task
        successful_updates += 1
        if successful_updates > 1: break
        
        # Tasks can be updated with only the title
        title_only = {'title':'Updated Again'}
        response = edit_task(task_id, title_only)
        assert response.status_code == 200
        assert response.request.path == f'/tasks/{task_id}'
        assert title_only['title'] in response.text

        # Tasks can be updated with only the description
        description_only = {'description':'1 in invisible ink'}
        response = edit_task(task_id, description_only)
        assert response.status_code == 200
        assert response.request.path == f'/tasks/{task_id}'
        assert description_only['description'] in response.text

        # Tasks can be updated with only the due date
        due_only = {'due':date(2025, 9, 3)}
        response = edit_task(task_id, due_only)
        assert response.status_code == 200
        assert response.request.path == f'/tasks/{task_id}'
        assert due_only['due'] in response.text

        # Can't update without the token
        response = edit_task(task_id, task_valid, token='')
        assert response.status_code == 400

        # Can't create task while logged out; redirects to login
        task_logged_out = {'title':'logout', 'description':'roto rooter', 'due':date(2026, 9, 1)} # pylint: disable=line-too-long
        client.get('/logout')
        response = edit_task(task_logged_out)
        assert response.status_code == 302
        assert response.location.startswith('/login')

        # Confirm task was not created despite redirect
        task = client.get(f'/tasks/{task_id}')
        assert all(field not in task.text for field in task_logged_out.values())
    
    # Again, one and only one user can update the task
    assert successful_updates == 1

def test_delete_task(client:FlaskClient) -> None:
    # Login as random user to generate csrf token
    login(client=client, user_idx=randint(0, len(user_data)-1))

    # Helper to future-proof requests
    def delete_task(task_id:int, token:Any=g.csrf_token) -> Response:
        return client.post(f'/tasks/{task_id}/delete', data={'csrf_token':token}, follow_redirects=True)
    
    # Task can only be deleted by the associated user and no one else.
    # We test this in a similar way to edit functionality (see test_edit_task).
    
    successful_updates = 0
    task_id = randint(1, len(task_data))
    
    for i in range(len(user_data)):

        # Attempt to delete the task while logged in as each user
        login(client=client, user_idx=i)

        # Make 1 attempt without the token to confirm it's required
        response = delete_task(task_id, token='')
        assert response.status_code == 400

        # Valid deletion (attempt)
        response = delete_task(task_id)

        # Skip to next user if the delete fails
        if response.status_code != 200: continue
        
        # On successful delete, redirect to tasks index
        assert response.request.path == f'/tasks'

        # Only one user can delete the task
        successful_updates += 1
        if successful_updates > 1: break
        
        # Tasks can't be deleted twice
        response = delete_task(task_id)
        assert response.status_code == 404

        # Non-extant tasks can't be deleted
        response = delete_task(len(task_data)+1)
        assert response.status_code == 404

        # We have to create a new task so we can test deletion while logged out
        task_remade = {'title':'Yep', 'description':"We'll do it live", 'due':date.today()}
        client.post('/tasks/new', data={'csrf_token':g.csrf_token, **task_remade})
        client.get('/logout')
        response = delete_task(len(task_data)) # possibly s/b +1, we'll find out
        assert response.status_code == 403
        assert all(field in response.text for field in task_remade.values())
    
    # Again, one and only one user can delete the task
    assert successful_updates == 1

