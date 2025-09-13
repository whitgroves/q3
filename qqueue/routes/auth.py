'''
Authentication routes for qqueue. Includes:
    /register   - adds a new user to the system
    /login      - authenticates an existing user
    /logout     - de-authenticates a logged in user

Note that unlike most routes, these do not need to be prefixed.
'''

from flask import Blueprint, Response, request, render_template, flash, current_app, redirect, url_for, abort
from flask_login import login_user, login_required, current_user, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
from qqueue.forms import RegisterForm, LoginForm, CredentialsForm
from qqueue.models import User
from qqueue.extensions import database, w3, endpoint_exception, display_user

blueprint = Blueprint('auth', __name__)

@blueprint.route('/register', methods=('GET', 'POST'))
def register() -> Response:
    '''Handles new user registrations.'''
    form = RegisterForm()
    match request.method:
        case 'GET':
            return render_template('auth/register.html', form=form)
        case 'POST':
            email = form.email.data.strip().lower()
            username = form.username.data.strip().lower()
            password = form.password.data.strip()
            confirm_password = form.confirm_password.data.strip()
            address = form.address.data.strip().lower()
            errors = False
            if password != confirm_password:
                flash('Passwords do not match.')
                errors = True
            elif len(User.query.filter_by(email=email).all()) > 0:
                flash('Email already registered.')
                errors = True
            elif not w3.is_address(address):
                flash('Address must be a valid blockchain address.')
                errors = True
            if not errors and form.validate_on_submit():
                password = generate_password_hash(password=password)
                user = User(email=email, username=username, password=password, address=address)
                database.session.add(user)
                database.session.commit()
                message = f'User "{user.username}" ({user.email}) registered successfully.'
                current_app.logger.info(msg=message)
                flash(message)
                return redirect(url_for('auth.login'))
            return render_template('auth/register.html', form=form), 400
        case _:
            endpoint_exception()

@blueprint.route('/login', methods=('GET', 'POST'))
def login() -> Response:
    '''Handles user login requests.'''
    form = LoginForm()
    match request.method:
        case 'GET':
            return render_template('auth/login.html', form=form)
        case 'POST':
            email_or_username = form.email_or_username.data.strip().lower()
            password = form.password.data.strip()
            errors = False
            user = User.query.filter(database.or_(
                User.email == email_or_username,
                User.username == email_or_username
            )).first()
            if not user or not check_password_hash(user.password, password):
                flash('Invalid user credentials. Please try again.')
                errors = True
            if not errors and form.validate_on_submit():
                login_user(user, remember=True)
                message = f'User "{user.username}" ({user.email}) logged in successfully.'
                current_app.logger.info(msg=message)
                flash(message)
                return redirect(url_for('main.index'))
            return render_template('auth/login.html', form=form), 400
        case _:
            endpoint_exception()

@blueprint.route('/edit', methods=('GET', 'POST'))
@login_required
def edit() -> Response:
    '''Allows `current_user` to edit their login credentials.'''
    user = database.session.get(User, current_user.id)
    if not user: redirect(url_for('main.index'), code=403)
    form = CredentialsForm()
    match request.method:
        case 'GET':
            return render_template('auth/edit.html',
                                   user=display_user(user),
                                   form=form)
        case 'POST':
            email = (form.email.data or user.email).strip().lower()
            password = (form.password.data or '').strip()
            confirm_password = (form.confirm_password.data or '').strip()
            current_password = form.current_password.data.strip() # never None
            address = (form.address.data or '').strip().lower()
            errors = False
            if not check_password_hash(user.password, current_password):
                flash('Current password is incorrect.')
                errors = True
            elif password != confirm_password:
                flash('New passwords do not match.')
                errors = True
            elif len(User.query.filter_by(email=email).all()) >\
                    int(user.email == email): # change = false = 0 = no matches
                flash('Email already registered to another user.')
                errors = True
            elif address and not w3.is_address(address):
                flash('Address must be a valid blockchain address.')
                errors = True
            if not errors and form.validate_on_submit():
                user.email = email
                if password: user.password = generate_password_hash(password)
                if address: user.address = address
                database.session.add(user)
                database.session.commit()
                flash(f'Credentials for {user.username} updated successfully.')
                return redirect(url_for('users.get_user', user_id=user.id))
            return render_template('auth/edit.html',
                                   user=display_user(user),
                                   form=form), 400
        case _:
            endpoint_exception()

@login_required
@blueprint.route('/logout')
def logout() -> Response:
    '''Clears credentials for the current user.'''
    username = current_user.username
    logout_user()
    flash(f'User {username} was logged out.')
    return redirect(url_for('main.index'))
