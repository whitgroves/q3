'''Tests for the task endpoints of qqueue.'''

from random import choice, randint
from flask import g # globals - needed for CSRF token
from flask.testing import FlaskClient
from tests.conftest import USER_DATA, TASK_DATA, Task, date, timedelta, authenticate_user, assert_redirect, database
from qqueue.config import ACCEPTED_CURRENCIES

def test_index(client:FlaskClient) -> None: # pylint: disable=too-many-statements
    '''Tests the endpoint /tasks'''

    # Future-proofing
    endpoint = '/tasks/'
    logged_in_shared_text = [
        '<p>Need a task done? <a href=',
        '>Click here</a> to create a request.</p>',
    ]
    logged_in_with_tasks_text = [
        '<p>Here are these open requests from other users:</p>'
    ]
    logged_out_with_tasks_text = [
        '>Register now</a> to view, create, and complete tasks like:</p>',
        '<p>Already registered? <a href=',
        '>Click here</a> to login.</p>',
    ]
    logged_in_no_tasks_text = [
        '<p>There are no other open requests at this time.</p>',
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
        # Tasks 0-3 are accepted, so should only see 4, 5, 6, 7, 8
        if i > 8 or 'accepted_by' in task:
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
    # should be visible for all unclaimed tasks in the system or for any tasks
    # related to the user (they are requester or accepter)
    user_id = randint(1, 3)
    authenticate_user(credentials=USER_DATA[user_id-1], client=client)
    response = client.get(endpoint)
    assert response.status_code == 200
    for task in TASK_DATA:
        if 'accepted_at' not in task or\
            (user_id in [task['accepted_by'], task['requested_by']] and 'completed_at' not in task): # pylint: disable=line-too-long
            assert task['summary'] in response.text
            assert task['detail'] in response.text
            assert str(task['reward_amount']) in response.text
            assert task['reward_currency'] in response.text
            assert str(task['due_by']) in response.text
            assert f'/users/{task["requested_by"]}' in response.text
        else:
            assert task['summary'] not in response.text
            assert task['detail'] not in response.text
            assert str(task['reward_amount']) not in response.text
            assert task['reward_currency'] not in response.text
            assert str(task['due_by']) not in response.text
            assert str(task['accepted_at']) not in response.text
            # cannot check for absence of user links since there are 2 of them
            # and either could have a value the other isn't supposed to            
    assert all(text in response.text for text in logged_in_with_tasks_text)
    assert all(text not in response.text for text in logged_out_with_tasks_text)
    assert all(text not in response.text for text in logged_in_no_tasks_text)
    assert all(text not in response.text for text in logged_out_no_tasks_text)

    # Now delete *unaccepted* tasks to test scenario where
    # no tasks should be displayed
    Task.query.filter(Task.accepted_at == None).delete(synchronize_session=False) # pylint: disable=line-too-long, singleton-comparison

    # We will use user3 since they are not associated with any tasks
    authenticate_user(credentials=USER_DATA[3], client=client)
    response = client.get(endpoint)
    assert response.status_code == 200
    for task in TASK_DATA:
        assert task['summary'] not in response.text
        assert task['detail'] not in response.text
        assert str(task['reward_amount']) not in response.text
        assert task['reward_currency'] not in response.text
        assert str(task['due_by']) not in response.text
    assert all(text in response.text for text in logged_in_shared_text)
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
    assert_redirect(client.get(endpoint))
    assert_redirect(client.post(endpoint, data=new_task))

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
    assert all(str(value) in response.text for value in new_task.values())

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

def test_get_task(client:FlaskClient) -> None: # pylint: disable=too-many-statements
    '''Tests the endpoint /tasks/<task_id>'''

    # Future-proofing
    shared_text = [ # always visible
        '/comment',
        '<button class="btn btn-primary">Leave a Comment</button>',
    ]
    update_text = [
        '/edit',
        '<button class="btn btn-primary">Edit Request</button></a>',
        '/delete',
        '<button class="btn btn-danger">Delete Task</button></form>',
    ]
    accept_text = [
        '/accept',
        '<button class="btn btn-success">Accept Request</button></form>',
    ]
    provider_text = [
        '/complete',
        '<button class="btn btn-success">Complete Order</button></form>',
        '/release',
        '<button class="btn btn-warning">Release Task</button></form>',
    ]
    approver_text = [
        '/approve',
        '<button class="btn btn-primary">Approve Work</button></form>',
        '/reject',
        '<button class="btn btn-danger">Reject Order</button></form>',
    ]
    display_fields = [
        'summary',
        'detail',
        'reward_amount',
        'reward_currency',
        'due_by',
        'requested_by'
    ]
    def get_sample(min_id:int, max_id:int) -> tuple[str, dict]:
        '''Helper that pulls a sample task based on database id (NOT index)'''
        task_id = randint(min_id, max_id)
        return f'/tasks/{task_id}', TASK_DATA[task_id-1]

    # The first sample is any of the non-accepted tasks in the test data
    endpoint, sample_task = get_sample(5, len(TASK_DATA))

    # Accessing while logged out redirects to login
    assert_redirect(client.get(endpoint))

    # Logged in user can see all fields in the test data and the option to
    # accept or comment but not the options to edit or delete. We use user3
    # since they aren't associated with any tasks.
    authenticate_user(credentials=USER_DATA[3], client=client)
    response = client.get(endpoint)
    assert response.status_code == 200
    assert all(str(sample_task[field]) in response.text
               for field in display_fields)
    assert all(text in response.text for text in shared_text)
    assert all(text not in response.text for text in update_text)
    assert all(text in response.text for text in accept_text)
    assert all(text not in response.text for text in provider_text)
    assert all(text not in response.text for text in approver_text)

    # The requester of the task should be able to see edit, delete, and comment,
    # but not to accept the task themselves
    authenticate_user(credentials=USER_DATA[sample_task['requested_by']-1],
                      client=client)
    response = client.get(endpoint)
    assert response.status_code == 200
    assert all(str(sample_task[field]) in response.text
               for field in display_fields)
    assert all(text in response.text for text in shared_text)
    assert all(text in response.text for text in update_text)
    assert all(text not in response.text for text in accept_text)
    assert all(text not in response.text for text in provider_text)
    assert all(text not in response.text for text in approver_text)

    # For an accepted task, the requester should not see edit/delete options,
    # but only have the option to leave a comment...
    endpoint, sample_task = get_sample(3, 3)
    authenticate_user(credentials=USER_DATA[sample_task['requested_by']-1],
                      client=client)
    response = client.get(endpoint)
    assert response.status_code == 200
    assert all(str(sample_task[field]) in response.text
               for field in display_fields)
    assert all(text in response.text for text in shared_text)
    assert all(text not in response.text for text in update_text)
    assert all(text not in response.text for text in accept_text)
    assert all(text not in response.text for text in provider_text)
    assert all(text not in response.text for text in approver_text)

    # ...the provider should not see edit/delete options,
    # but have the options to leave a comment, release, or complete the task...
    authenticate_user(credentials=USER_DATA[sample_task['accepted_by']-1],
                      client=client)
    response = client.get(endpoint)
    assert response.status_code == 200
    assert all(str(sample_task[field]) in response.text
               for field in display_fields)
    assert all(text in response.text for text in shared_text)
    assert all(text not in response.text for text in update_text)
    assert all(text not in response.text for text in accept_text)
    assert all(text in response.text for text in provider_text)
    assert all(text not in response.text for text in approver_text)

    # ...and unrelated users should get redirected to the tasks index.
    authenticate_user(credentials=USER_DATA[3], client=client)
    assert_redirect(client.get(endpoint), redirect='/tasks')

    # For accepted and completed tasks, the provider should only see the option
    # to comment...
    endpoint, sample_task = get_sample(4, 4)
    authenticate_user(credentials=USER_DATA[sample_task['accepted_by']-1],
                      client=client)
    response = client.get(endpoint)
    assert response.status_code == 200
    assert all(str(sample_task[field]) in response.text
               for field in display_fields)
    assert all(text in response.text for text in shared_text)
    assert all(text not in response.text for text in update_text)
    assert all(text not in response.text for text in accept_text)
    assert all(text not in response.text for text in provider_text)
    assert all(text not in response.text for text in approver_text)

    # ...the requester should have options to comment/approve/reject...
    authenticate_user(credentials=USER_DATA[sample_task['requested_by']-1],
                      client=client)
    response = client.get(endpoint)
    assert response.status_code == 200
    assert all(str(sample_task[field]) in response.text
               for field in display_fields)
    assert all(text in response.text for text in shared_text)
    assert all(text not in response.text for text in update_text)
    assert all(text not in response.text for text in accept_text)
    assert all(text not in response.text for text in provider_text)
    assert all(text in response.text for text in approver_text)

    # ...and unrelated users should get redirected to the tasks index.
    authenticate_user(credentials=USER_DATA[3], client=client)
    assert_redirect(client.get(endpoint), redirect='/tasks')

    # Once approved, the only option available for providers and requesters
    # is to leave a comment; all other users get redirected.
    endpoint, sample_task = get_sample(1, 2)
    authenticate_user(credentials=USER_DATA[sample_task['accepted_by']-1],
                      client=client)
    response = client.get(endpoint)
    assert response.status_code == 200
    assert all(str(sample_task[field]) in response.text
               for field in display_fields)
    assert all(text in response.text for text in shared_text)
    assert all(text not in response.text for text in update_text)
    assert all(text not in response.text for text in accept_text)
    assert all(text not in response.text for text in provider_text)
    assert all(text not in response.text for text in approver_text)

    authenticate_user(credentials=USER_DATA[sample_task['requested_by']-1],
                      client=client)
    response = client.get(endpoint)
    assert response.status_code == 200
    assert all(str(sample_task[field]) in response.text
               for field in display_fields)
    assert all(text in response.text for text in shared_text)
    assert all(text not in response.text for text in update_text)
    assert all(text not in response.text for text in accept_text)
    assert all(text not in response.text for text in provider_text)
    assert all(text not in response.text for text in approver_text)

    authenticate_user(credentials=USER_DATA[3], client=client)
    assert_redirect(client.get(endpoint), redirect='/tasks')

def test_edit_task(client:FlaskClient) -> None:
    '''Tests the endpoint /tasks/<task_id>/edit'''

    # Future-proofing
    task_edits = {
        'summary': 'Make edits to this task',
        'detail': 'Something you would not expect to see!',
        'reward_amount': 69.0,
        'reward_currency': choice(ACCEPTED_CURRENCIES),
        'due_by': date.today()+timedelta(randint(0, 30)),
    }
    def get_sample(min_id:int, max_id:int) -> tuple[str, dict]:
        '''Helper that pulls a sample task based on database id (NOT index)'''
        task_id = randint(min_id, max_id)
        return f'/tasks/{task_id}/edit', TASK_DATA[task_id-1]

    # Sample is drawn from non-accepted tasks
    endpoint, sample_task = get_sample(5, len(TASK_DATA))

    # Both GET and POST requests redirect to login when logged out
    assert_redirect(client.get(endpoint))
    assert_redirect(client.post(endpoint, data=task_edits))

    # Login to generate CSRF token and valid edit data
    authenticate_user(credentials=USER_DATA[3], client=client)
    data = {'csrf_token':g.csrf_token, **task_edits}

    # Even when logged in, non-requesters are redirected to the task's
    # display page. user3 is used here since they have 0 requests.
    redirect = endpoint.replace('/edit', '')
    assert_redirect(client.get(endpoint), redirect=redirect)
    assert_redirect(client.post(endpoint, data=data), redirect=redirect)

    # Only the task requester can load into the edit page, whic pre-populates
    # with the existing task data for all editable fields
    authenticate_user(credentials=USER_DATA[sample_task['requested_by']-1],
                      client=client)
    response = client.get(endpoint)
    assert response.status_code == 200
    assert response.request.path == endpoint
    assert all(str(sample_task[field]) in response.text for field in task_edits)

    # And edits that they make are accepted and displayed after the app
    # redirects to the task page upon submission
    response = client.post(endpoint, data=data, follow_redirects=True)
    assert response.status_code == 200
    assert response.request.path == redirect
    # for value in task_edits.values():
    #     assert str(value) in response.text
    assert all(str(value) in response.text for value in task_edits.values())

    # But no updates are accepted without the CSRF token.
    # Here, we attempt to re-update to new values, but this should fail
    response = client.post(endpoint, data=task_edits)
    assert response.status_code == 400

    # For accepted/completed/approved tasks, the user should get redirected
    # to the task page with no changes if related, or the tasks index if not
    test_cases = {
        'accepted': get_sample(3, 3),
        'completed': get_sample(4, 4),
        'approved': get_sample(1, 2),
    }
    for _, (endpoint, sample_task) in test_cases.items():
        authenticate_user(credentials=USER_DATA[sample_task['requested_by']-1],
                          client=client)
        redirect = endpoint.replace('/edit', '')
        assert_redirect(client.get(endpoint), redirect=redirect)
        assert_redirect(client.post(endpoint, data=data), redirect=redirect)
        authenticate_user(credentials=USER_DATA[3], client=client)
        redirect = '/tasks'
        assert_redirect(client.get(endpoint), redirect=redirect)
        assert_redirect(client.post(endpoint, data=data), redirect=redirect)

def test_delete_task(client:FlaskClient) -> None:
    '''Tests the endpoint /tasks/<task_id>/delete'''
    
    # Future-proofing
    redirect = '/tasks/'
    def get_sample(min_id:int, max_id:int) -> tuple[str, dict]:
        '''Helper that pulls a sample task based on database id (NOT index)'''
        task_id = randint(min_id, max_id)
        return task_id, f'/tasks/{task_id}/delete', TASK_DATA[task_id-1]

    # A user that is unrelated to the task cannot delete it, and will be
    # redirected to the tasks index with the task still in the database
    # We use user3 (id:4) again since they aren't associated with any tasks.
    authenticate_user(credentials=USER_DATA[3], client=client)
    task_id, endpoint, sample_task = get_sample(5, len(TASK_DATA))
    
    response = client.post(endpoint)
    assert response.status_code == 403
    assert database.session.get(Task, task_id) is not None
    assert sample_task['detail'] in client.get(redirect).text

    # The task requester, however, can delete the task, and gets redirected
    # back to the task index with the task removed from the database
    authenticate_user(credentials=USER_DATA[sample_task['requested_by']-1],
                      client=client)
    assert database.session.get(Task, task_id) is not None # sanity check
    assert_redirect(response=client.post(endpoint),redirect=redirect)
    assert database.session.get(Task, task_id) is None
    response = client.get(f'/tasks/{task_id}')
    assert response.status_code == 404
    response = client.get(redirect)
    assert sample_task['summary'] in response.text # Task "<summary>" was deleted
    assert sample_task['detail'] not in response.text

    # For an accepted/completed/approved task, the delete request should fail
    # for any user, even the accepter or requester
    task_id, endpoint, sample_task = get_sample(1, 4)
    test_cases = [
        USER_DATA[3],                             # unrelated user
        USER_DATA[sample_task['requested_by']-1], # requester
        USER_DATA[sample_task['accepted_by']-1],  # accepter
    ]
    for i, test_user in enumerate(test_cases):    # order matters
        authenticate_user(credentials=test_user, client=client)
        response = client.post(endpoint)
        assert response.status_code == 403
        assert database.session.get(Task, task_id) is not None

def test_accept_task(client:FlaskClient) -> None:
    '''Tests the endpoint /tasks/<task_id>/accept'''
    
    # Future-proofing
    def get_sample(min_id:int, max_id:int) -> tuple[str, dict]:
        '''Helper that pulls a sample task based on database id (NOT index)'''
        task_id = randint(min_id, max_id)
        return task_id, f'/tasks/{task_id}/accept', TASK_DATA[task_id-1]

    # The user that requested the task cannot accept it
    task_id, endpoint, sample_task = get_sample(5, len(TASK_DATA))
    authenticate_user(credentials=USER_DATA[sample_task['requested_by']-1],
                      client=client)
    response = client.post(endpoint)
    assert response.status_code == 403
    assert database.session.get(Task, task_id).accepted_at is None

    # However, any other user can. We use either user1 or user3 since neither
    # has requested any tasks
    authenticate_user(credentials=USER_DATA[choice([1, 3])], client=client)
    assert_redirect(response=client.post(endpoint), redirect=f'/tasks/{task_id}')
    assert database.session.get(Task, task_id).accepted_at is not None

    # For an accepted/completed/approved task, the endpoint will fail for
    # any and all users without updating the database
    task_id, endpoint, sample_task = get_sample(1, 4)
    accepted_at = database.session.get(Task, task_id).accepted_at
    for test_user in USER_DATA:
        authenticate_user(credentials=test_user, client=client)
        response = client.post(endpoint)
        assert response.status_code == 403
        assert database.session.get(Task, task_id).accepted_at == accepted_at

def test_release_task(client:FlaskClient) -> None:
    '''Tests the endpoint /tasks/<task_id>/release'''
    
    # Future-proofing
    def get_sample(min_id:int, max_id:int) -> tuple[int, str, dict]:
        '''Helper that pulls a sample task based on database id (NOT index)'''
        task_id = randint(min_id, max_id)
        return task_id, f'/tasks/{task_id}/release', TASK_DATA[task_id-1]

    # Only task index 2 (id:3) is accepted but not completed/approved
    task_id, endpoint, sample_task = get_sample(3, 3)
    assert database.session.get(Task, task_id).accepted_at is not None
    assert database.session.get(Task, task_id).completed_at is None

    # Neither the requester nor an unrelated user can release a task
    for user_index in [3, sample_task['requested_by']-1]:
        authenticate_user(credentials=USER_DATA[user_index], client=client)
        response = client.post(endpoint)
        assert response.status_code == 403
        assert database.session.get(Task, task_id).accepted_at is not None

    # Only the accepter can release it, which redirects to the task's page
    authenticate_user(credentials=USER_DATA[sample_task['accepted_by']-1],
                      client=client)
    assert_redirect(client.post(endpoint), redirect=f'/tasks/{task_id}')
    assert database.session.get(Task, task_id).accepted_at is None

    # For completed tasks, no one may release it
    task_id, endpoint, sample_task = get_sample(1, 4)
    accepted_at = database.session.get(Task, task_id).accepted_at
    for test_user in USER_DATA:
        authenticate_user(credentials=test_user, client=client)
        response = client.post(endpoint)
        assert response.status_code == 403
        assert database.session.get(Task, task_id).accepted_at == accepted_at

def test_complete_task(client:FlaskClient) -> None:
    '''Tests the endpoint /tasks/<task_id>/complete'''

    # Future-proofing
    def get_sample(min_id:int, max_id:int) -> tuple[int, str, dict]:
        '''Helper that pulls a sample task based on database id (NOT index)'''
        task_id = randint(min_id, max_id)
        return task_id, f'/tasks/{task_id}/complete', TASK_DATA[task_id-1]

    # Only task index 2 (id:3) is ready to be completed (not approved/rejected)
    task_id, endpoint, sample_task = get_sample(3, 3)
    assert database.session.get(Task, task_id).accepted_at is not None
    assert database.session.get(Task, task_id).completed_at is None

    # Neither the requester nor an unrelated user can complete a task
    for user_index in [3, sample_task['requested_by']-1]:
        authenticate_user(credentials=USER_DATA[user_index], client=client)
        response = client.post(endpoint)
        assert response.status_code == 403
        assert database.session.get(Task, task_id).completed_at is None

    # Only the accepter can complete it, which redirects to the task's page
    authenticate_user(credentials=USER_DATA[sample_task['accepted_by']-1],
                      client=client)
    assert_redirect(client.post(endpoint), redirect=f'/tasks/{task_id}')
    assert database.session.get(Task, task_id).completed_at is not None

    # For completed tasks, no one may complete it
    task_id, endpoint, sample_task = get_sample(1, 4)
    completed_at = database.session.get(Task, task_id).completed_at
    for test_user in USER_DATA:
        authenticate_user(credentials=test_user, client=client)
        response = client.post(endpoint)
        assert response.status_code == 403
        assert database.session.get(Task, task_id).completed_at == completed_at

def test_approve_task(client:FlaskClient) -> None:
    '''Tests the endpoint /tasks/<task_id>/approve'''

    # Future-proofing
    def get_sample(min_id:int, max_id:int) -> tuple[int, str, dict]:
        '''Helper that pulls a sample task based on database id (NOT index)'''
        task_id = randint(min_id, max_id)
        return task_id, f'/tasks/{task_id}/approve', TASK_DATA[task_id-1]

    # Only task index 3 (id:4) is ready to be approved (completed/unrejected)
    task_id, endpoint, sample_task = get_sample(4, 4)
    assert database.session.get(Task, task_id).completed_at is not None
    assert database.session.get(Task, task_id).approved_at is None

    # Neither the accepter nor an unrelated user can approve a task
    for user_index in [3, sample_task['accepted_by']-1]:
        authenticate_user(credentials=USER_DATA[user_index], client=client)
        response = client.post(endpoint)
        assert response.status_code == 403
        assert database.session.get(Task, task_id).approved_at is None

    # Only the requester can approve it, which redirects to the task's page
    authenticate_user(credentials=USER_DATA[sample_task['requested_by']-1],
                      client=client)
    assert_redirect(client.post(endpoint), redirect=f'/tasks/{task_id}')
    assert database.session.get(Task, task_id).approved_at is not None

    # For approved tasks, no one may re-approve it
    task_id, endpoint, sample_task = get_sample(1, 2)
    approved_at = database.session.get(Task, task_id).approved_at
    for test_user in USER_DATA:
        authenticate_user(credentials=test_user, client=client)
        response = client.post(endpoint)
        assert response.status_code == 403
        assert database.session.get(Task, task_id).approved_at == approved_at

def test_reject_task(client:FlaskClient) -> None:
    '''Tests the endpoint /tasks/<task_id>/reject'''

    # Future-proofing
    def get_sample(min_id:int, max_id:int) -> tuple[int, str, dict]:
        '''Helper that pulls a sample task based on database id (NOT index)'''
        task_id = randint(min_id, max_id)
        return task_id, f'/tasks/{task_id}/reject', TASK_DATA[task_id-1]

    # Only task index 3 (id:4) is ready to be rejected (not approved/completed)
    task_id, endpoint, sample_task = get_sample(4, 4)
    assert database.session.get(Task, task_id).completed_at is not None
    assert database.session.get(Task, task_id).approved_at is None

    # Neither the accepter nor an unrelated user can reject a task
    for user_index in [3, sample_task['accepted_by']-1]:
        authenticate_user(credentials=USER_DATA[user_index], client=client)
        response = client.post(endpoint)
        assert response.status_code == 403
        assert database.session.get(Task, task_id).completed_at is not None

    # Only the requester can reject it, which redirects to the task's page
    authenticate_user(credentials=USER_DATA[sample_task['requested_by']-1],
                      client=client)
    assert_redirect(client.post(endpoint), redirect=f'/tasks/{task_id}')
    assert database.session.get(Task, task_id).completed_at is None

    # For approved tasks, no one may reject it
    task_id, endpoint, sample_task = get_sample(1, 2)
    completed_at = database.session.get(Task, task_id).completed_at
    for test_user in USER_DATA:
        authenticate_user(credentials=test_user, client=client)
        response = client.post(endpoint)
        assert response.status_code == 403
        assert database.session.get(Task, task_id).completed_at == completed_at

def test_requested_by(client:FlaskClient) -> None:
    '''Tests the endpoint /tasks/requested/<user_id>'''
    pass

def test_accepted_by(client:FlaskClient) -> None:
    '''Tests the endpoint /tasks/accepted/<user_id>'''
    pass
