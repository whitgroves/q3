'''Test for the order routes of qqueue.'''

from random import randint
from flask import g # globals
from flask.testing import FlaskClient
from tests.conftest import user_data, task_data, comment1_data, comment2_data

def login(client:FlaskClient, user_id:int) -> None:
    '''
    Helper to authenticate test user requests.

    First makes a GET request to generate a CSRF token, 
    then uses that token (via flask.g.csrf_token) to log in.

    Since this is not a `test_` method, does not have access 
    to test fixtures; `client` must be passed manually.
    '''
    client.get('/login')
    login_data = {'csrf_token': g.csrf_token,
                  'email_or_username': user_data[user_id]['email'],
                  'password': user_data[user_id]['password']}
    client.post('/login', data=login_data)

def test_index(client:FlaskClient) -> None:
    # Page loads with all tasks listed
    response = client.get('/tasks')
    assert response.status_code == 200
    for task in task_data:
        assert all(field in response.text for field in task.values())
    
def test_task(client:FlaskClient) -> None:
    # Page loads with all task fields and comments
    task_id = randint(0, len(task_data)-1) # random sample
    response = client.get(f'/tasks/{task_id}')
    assert response.status_code == 200
    assert all(field in response.text for field in task_data[task_id].values())
    assert all(comment in response.text for comment in comment1_data)
    assert all(comment in response.text for comment in comment2_data)

    # Redirect to index on non-extant task id
    response = client.get(f'/tasks/{len(task_data)}', follow_redirects=True)
    assert response.status_code == 200
    assert response.request.path == '/tasks/'


