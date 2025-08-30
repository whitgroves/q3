'''
Task routes for qqueue. Includes:
    /tasks - All tasks that have yet to be accepted in the system
'''
from datetime import date
from flask import Blueprint, Response, request, render_template, flash, redirect, url_for, abort, current_app
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from qqueue.forms import TaskForm
from qqueue.models import Task, User
from qqueue.extensions import database, endpoint_exception

blueprint = Blueprint('tasks', __name__)

@blueprint.route('/')
def index() -> Response:
    data = dict()
    tasks = Task.query.filter(Task.accepted_at == None).order_by(Task.due_by).all()
    if current_user.is_authenticated:
        data['tasks'] = tasks
    else:
        data['summaries'] = [task.summary for task in tasks[:5]]
    return render_template('tasks/index.html', **data)

@blueprint.route('/new', methods=('GET', 'POST'))
@login_required
def new_task() -> Response:
    '''Handles the creation of new tasks.'''
    form = TaskForm()
    match request.method:
        case 'GET':
            return render_template('tasks/new.html', form=form)
        case 'POST':
            summary = form.summary.data
            detail = form.detail.data
            reward_amount = form.reward_amount.data
            reward_currency = form.reward_currency.data
            due_by = form.due_by.data
            errors = False
            if not due_by or due_by < date.today():
                flash('Due date cannot be in the past.')
                errors=True
            if not errors and form.validate_on_submit():
                task = Task(summary=summary,
                            detail=detail,
                            reward_amount=reward_amount,
                            reward_currency=reward_currency,
                            due_by=due_by,
                            requested_by=current_user.id)
                database.session.add(task)
                database.session.commit()
                message = f'Task "{summary}" added successfully.'
                current_app.logger.info(msg=message)
                flash(message=message)
                return redirect(url_for('tasks.get_task', task_id=task.id))
            return render_template('tasks/new.html', form=form), 400
        case _:
            endpoint_exception()

@blueprint.route('/<int:task_id>')
@login_required
def get_task(task_id:int) -> Response:
    '''Fetches the task matching `task_id`, if it exists.'''
    task = Task.query.filter(Task.id == task_id).first_or_404()
    return render_template('tasks/task.html', task=task)

@blueprint.route('/<int:task_id>/edit')
@login_required
def edit_task(task_id:int) -> Response:
    '''Updates the task matching `task_id`, if it exists.'''
    pass

@blueprint.route('/<int:task_id>/delete')
@login_required
def delete_task(task_id:int) -> Response:
    '''Deletes the task matching `task_id`, if it exists.'''
    pass

@blueprint.route('/<int:task_id>/accept')
@login_required
def accept_task(task_id:int) -> Response:
    '''Allows `current_user` to claim an unclaimed task.'''
    pass

@blueprint.route('/<int:task_id>/decline')
@login_required
def decline_task(task_id:int) -> Response:
    '''Allows `current_user` to release their claim on a task.'''
    pass

@blueprint.route('/<int:task_id>/complete')
@login_required
def complete_task(task_id:int) -> Response:
    '''Allows the user matching `accepted_by` to mark a task complete.'''
    pass

@blueprint.route('/<int:task_id>/approve')
@login_required
def approve_task(task_id:int) -> Response:
    '''Allows the requester to confirm a task is complete.'''
    pass

@blueprint.route('/<int:task_id>/reject')
@login_required
def reject_task(task_id:int) -> Response:
    '''Allows the requester to deny a task is complete, then re-open it.'''
    pass

@blueprint.route('/requested/<int:user_id>')
def requested_by(user_id:int) -> Response:
    '''Returns all of the open tasks requested by `user_id`.'''
    pass

@blueprint.route('/accepted')
def accepted_by(user_id:int) -> Response:
    '''Returns all of the tasks accepted by the current user.'''
    pass
