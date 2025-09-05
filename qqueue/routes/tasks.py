'''
Task routes for qqueue. Includes:
    /tasks - All tasks that have yet to be accepted in the system
'''
from datetime import date, datetime
from flask import Blueprint, Response, request, render_template, flash, redirect, url_for, abort, current_app
from flask_login import login_required, current_user
from qqueue.forms import TaskForm, CommentForm
from qqueue.models import Task, Comment
from qqueue.extensions import database, endpoint_exception

blueprint = Blueprint('tasks', __name__)

@blueprint.route('/')
def index() -> Response:
    data = dict()
    if current_user.is_authenticated:
        tasks = Task.query.filter(Task.completed_at == None).order_by(Task.due_by).all()
        data['open_tasks'] = []
        data['requested_tasks'] = []
        data['accepted_tasks'] = []
        for task in tasks:
            if task.accepted_at is None:
                data['open_tasks'].append(task)
            elif task.requested_by == current_user.id:
                data['requested_tasks'].append(task)
            elif task.accepted_by == current_user.id:
                data['accepted_tasks'].append(task)
    else:
        tasks = Task.query.filter(Task.accepted_at == None).order_by(Task.due_by).all()
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
    if task.accepted_by and current_user.id not in [task.accepted_by, task.requested_by]: # pylint disable=line-too-long
        return redirect(url_for('tasks.index'))
    return render_template('tasks/task.html', task=task)

@blueprint.route('/<int:task_id>/edit', methods=('GET', 'POST'))
@login_required
def edit_task(task_id:int) -> Response:
    '''Updates the task matching `task_id`, if it exists.'''
    task = database.session.get(Task, task_id)
    should_redirect = False
    if not task: 
        should_redirect = True
        code = 403
    elif task.accepted_by or current_user.id != task.requested_by:
        should_redirect = True
        code = 302
    if should_redirect:
        return redirect(url_for('tasks.get_task',task_id=task_id), code=code)
    form = TaskForm()
    match request.method:
        case 'GET':
            return render_template('tasks/edit.html', task=task, form=form)
        case 'POST':
            summary = form.summary.data or task.summary
            detail = form.detail.data or task.detail
            reward_amount = form.reward_amount.data or task.reward_amount
            reward_currency = form.reward_currency.data or task.reward_currency
            due_by = form.due_by.data or task.due_by
            errors = False
            if not due_by or due_by < date.today():
                flash('Due date cannot be in the past.')
                errors=True
            if not errors and form.validate_on_submit():
                task.summary=summary
                task.detail=detail
                task.reward_amount=reward_amount
                task.reward_currency=reward_currency
                task.due_by=due_by
                database.session.add(task)
                database.session.commit()
                message = f'Task "{summary}" updated successfully.'
                current_app.logger.info(msg=message)
                flash(message=message)
                return redirect(url_for('tasks.get_task', task_id=task.id))
            return render_template('tasks/edit.html', task=task, form=form), 400
        case _:
            endpoint_exception()

@blueprint.post('/<int:task_id>/delete')
@login_required
def delete_task(task_id:int) -> Response:
    '''Deletes the task matching `task_id`, if it exists.'''
    task = database.session.get(Task, task_id)
    if task.accepted_at or current_user.id != task.requested_by: abort(403)
    summary = task.summary
    database.session.delete(task)
    database.session.commit()
    flash(f'Task "{summary}" was permanently deleted.')
    return redirect(url_for('tasks.index'))

@blueprint.post('/<int:task_id>/accept')
@login_required
def accept_task(task_id:int) -> Response:
    '''Allows `current_user` to claim an unclaimed task.'''
    task = database.session.get(Task, task_id)
    if task.accepted_at or current_user.id == task.requested_by: abort(403)
    task.accepted_at = datetime.now()
    task.accepted_by = current_user.id
    database.session.commit()
    flash(f'You\'ve accepted "{task.summary}", due date: {task.due_by}.')
    return redirect(url_for('tasks.get_task', task_id=task.id))

@blueprint.post('/<int:task_id>/release')
@login_required
def release_task(task_id:int) -> Response:
    '''Allows `current_user` to release their claim on a task.'''
    task = database.session.get(Task, task_id)
    if task.completed_at or current_user.id != task.accepted_by: abort(403)
    task.accepted_at = None
    task.accepted_by = None
    database.session.commit()
    flash(f'Task "{task.summary}" released. Do not re-claim unless you can complete it.') # pylint: disable=line-too-long
    return redirect(url_for('tasks.get_task', task_id=task.id))

@blueprint.post('/<int:task_id>/complete')
@login_required
def complete_task(task_id:int) -> Response:
    '''Allows the user matching `accepted_by` to mark a task complete.'''
    task = database.session.get(Task, task_id)
    if task.completed_at or current_user.id != task.accepted_by: abort(403)
    task.completed_at = datetime.now()
    database.session.commit()
    flash(f'Task "{task.summary}" marked as complete. Waiting on requester approval.') # pylint: disable=line-too-long
    return redirect(url_for('tasks.get_task', task_id=task.id))

@blueprint.post('/<int:task_id>/approve')
@login_required
def approve_task(task_id:int) -> Response:
    '''Allows the requester to confirm a task is complete.'''
    task = database.session.get(Task, task_id)
    if task.approved_at or current_user.id != task.requested_by: abort(403)
    task.approved_at = datetime.now()
    database.session.commit()
    flash(f'Task "{task.summary}" approved. Payment to provider pending.')
    return redirect(url_for('tasks.get_task', task_id=task.id))

@blueprint.post('/<int:task_id>/reject')
@login_required
def reject_task(task_id:int) -> Response:
    '''Allows the requester to deny a task is complete, then re-open it.'''
    task = database.session.get(Task, task_id)
    if task.approved_at or current_user.id != task.requested_by: abort(403)
    task.completed_at = None
    database.session.commit()
    flash(f'Task "{task.summary}" rejected. Please leave a comment explaining why.') # pylint: disable=line-too-long
    return redirect(url_for('tasks.get_task', task_id=task.id))

@blueprint.post('/<int:task_id>/comments/new')
@login_required
def new_comment(task_id:int) -> Response:
    '''Leaves a new comment on a task.'''
    task = database.session.get(Task, task_id)
    if task.accepted_at is not None:
        if current_user.id not in [task.accepted_by, task.requested_by]:
            abort(403)
    form = CommentForm()
    text = form.text.data
    if form.validate_on_submit():
        comment = Comment(task_id=task_id,
                          created_by=current_user.id,
                          text=text)
        database.session.add(comment)
        database.session.commit()
        message = f'{comment.user.username} left a new comment.'
        current_app.logger.info(msg=message)
        flash(message=message)
        return redirect(url_for('tasks.get_task', task_id=task_id))
    abort(403)

@blueprint.route('/comments/<int:comment_id>')
@login_required
def get_comment(comment_id:int) -> Response:
    '''Gets a singular comment outside of the task's context.'''
    pass

@blueprint.route('/comments/<int:comment_id>/edit', methods=('GET', 'POST'))
@login_required
def edit_comment(comment_id:int) -> Response:
    '''Endpoint that handles task comment updates.'''
    pass

@blueprint.post('/comments/<int:commend_id>/delete')
@login_required
def delete_comment(comment_id:int) -> Response:
    '''Deletes the specified comment, if it exists.'''
    pass