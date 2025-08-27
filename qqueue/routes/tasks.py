'''Routes for tasks in qqueue.'''

from flask import Blueprint, Response, render_template
from flask_login import login_required, current_user
from qqueue.models import Task

blueprint = Blueprint('tasks', __name__)

@blueprint.route('/')
@login_required
def index() -> Response:
    '''Returns all tasks for the current user.'''
    tasks = Task.query.all()
    return render_template('tasks/index.html', tasks=tasks, user=current_user)

@blueprint.route('/<int:_id>')
@login_required
def get_task(_id:int) -> Response:
    '''Returns the task matching `_id`.'''
    pass

@blueprint.route('/new', methods=('GET', 'POST'))
@login_required
def new_task() -> Response:
    '''Creates a new task in the database.'''
    pass

@blueprint.route('/<int:_id>/edit', methods=('GET', 'POST'))
@login_required
def edit_task(_id:int) -> Response:
    '''Updates a task in the database.'''
    pass

@blueprint.route('<int:_id>/delete')
@login_required
def delete_task(_id:int) -> Response:
    '''Deletes a task from the database, if it exists.'''
    pass