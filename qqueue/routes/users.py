'''
User routes for qqueue. Includes:
    /users - A list of all users, if the current user is logged in
    /users/<user_id> - Public profile page for a specific user
    /users/edit - Allows the current user to edit their own profile
'''

from flask import Blueprint, Response, request, render_template, flash, redirect, url_for, abort
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from qqueue.forms import UserForm
from qqueue.models import User
from qqueue.extensions import database, endpoint_exception

blueprint = Blueprint('users', __name__)

def display_format(user:User) -> User:
    '''
    Helper that modifies `User` fields to display expected values, instead of
    converting values like `None` to "None".
    '''
    user.headline = user.headline or ''
    user.bio = user.bio or ''
    return user

@blueprint.route('/')
def index() -> Response:
    data = dict()
    users = User.query.all()
    if current_user.is_authenticated:
        data['users'] = [display_format(user) for user in users]
    else:
        data['user_count'] = len(users)
    return render_template('users/index.html', **data)

@blueprint.route('/<int:user_id>')
def get_user(user_id:int) -> Response:
    data = dict()
    user = database.session.get(User, user_id)
    if current_user.is_authenticated:
        data['user'] = display_format(user)
    else:
        data['has_requests'] = len(user.requests) > 0
        data['has_orders'] = len(user.orders) > 0
    return render_template('users/user.html', **data)

@blueprint.route('/edit', methods=('GET', 'POST'))
@login_required
def edit_user() -> Response:
    user = database.session.get(User, current_user.id)
    if not user: redirect(url_for('main.index'), code=403)
    form = UserForm()
    match request.method:
        case 'GET':
            return render_template('users/edit.html', 
                                   user=display_format(user), 
                                   form=form)
        case 'POST':
            # email = form.email.data.strip() or user.email
            username = (form.username.data or user.username).strip()
            # password = form.password.data.strip()
            # confirm_password = form.confirm_password.data.strip()
            headline = (form.headline.data or user.headline).strip()
            bio = (form.bio.data or user.bio).strip()
            # current_password = form.current_password.data.strip()
            errors = False
            # if not check_password_hash(user.password, current_password):
            #     flash('Current password is incorrect.')
            #     errors = True
            # elif password != confirm_password:
            #     flash('Passwords do not match.')
            #     errors = True
            # elif len(User.query.filter_by(email=email).all()) >\
            #     int(user.email == email): # change = false = 0 = no matches
            #     flash('Email already registered to another user.')
            #     errors = True
            if len(User.query.filter_by(username=username).all()) >\
                int(user.username == username):
                flash('Requested username is already taken.')
                errors = True
            if not errors and form.validate_on_submit(): 
                # user.email = email
                user.username = username
                # if password is not None: user.password = generate_password_hash(password=password)
                user.headline = headline
                user.bio = bio
                database.session.add(user)
                database.session.commit()
                flash(f'User info for {username} updated successfully.')
                return redirect(url_for('users.get_user', user_id=user.id))
            return render_template('users/edit.html', user=user, form=form), 400 # pylint: disable=line-too-long
        case _:
            endpoint_exception()