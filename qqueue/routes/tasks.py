'''
Task routes for qqueue. Includes:
    /tasks - All tasks that have yet to be accepted in the system
'''

from flask import Blueprint, Response, request, render_template, flash, redirect, url_for, abort
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from qqueue.forms import TaskForm
from qqueue.models import Task, User
from qqueue.extensions import database

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

def get_task(task_id:int) -> Response:
    pass

def new_task(task_id:int) -> Response:
    pass

def edit_task(task_id:int) -> Response:
    pass

def delete_task(task_id:int) -> Response:
    pass

def accept_task(task_id:int) -> Response:
    pass

def complete_task(task_id:int) -> Response:
    pass

def approve_task(task_id:int) -> Response:
    pass

def reject_task(task_id:int) -> Response:
    pass

@blueprint.route('/requested/<int:user_id>')
def requested_by(user_id:int) -> Response:
    pass

@blueprint.route('/accepted/<int:user_id>')
def accepted_by(user_id:int) -> Response:
    pass