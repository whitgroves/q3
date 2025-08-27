'''
User routes for qqueue. Includes:
    /users - A list of all users, if the current user is logged in
    /users/<user_id> - Public profile page for a specific user
    /users/<user_id>/edit - Allows the current user to edit their own profile
'''

from flask import Blueprint, Response, request, render_template, flash, current_app, redirect, url_for, abort
from flask_login import login_user, login_required, current_user, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
from qqueue.forms import RegisterForm, LoginForm
from qqueue.models import User
from qqueue.extensions import database

blueprint = Blueprint('users', __name__)

@blueprint.route('/')
def index() -> Response:
    data = dict()
    users = User.query.all()
    if current_user.is_authenticated: data['users'] = users
    else: data['user_count'] = len(users)
    return render_template('users/index.html', **data)

@blueprint.route('/<int:user_id>')
def get_user(user_id:int) -> Response:
    pass

@blueprint.route('/<int:user_id>/edit', methods=('GET', 'POST'))
def edit_user(user_id:int) -> Response:
    pass