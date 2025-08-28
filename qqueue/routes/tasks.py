'''
Task routes for qqueue. Includes:
    /tasks - All tasks that have been created but not accepted
    /tasks/requested/<user_id> - All tasks created by user_id, either open or associated with current_user
    /tasks/accepted/<user_id> - All tasks accepted by user_id that are associated with current_user
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
    data['tasks'] = Task.query.filter_by(Task.accepted_at is None)
    return render_template('tasks/index.html', **data)

@blueprint.route('/requested/<int:user_id>')
def requested_by(user_id:int) -> Response:
    pass

@blueprint.route('/accepted/<int:user_id>')
def accepted_by(user_id:int) -> Response:
    pass