'''The main set of routes for qqueue.'''
from datetime import datetime, timezone
from flask import Blueprint, Response, render_template

blueprint = Blueprint('main', __name__)

@blueprint.route('/')
def index() -> Response:
    '''Returns the qqueue homepage.'''
    return render_template('index.html', dt_utc=datetime.now(timezone.utc))

@blueprint.route('/about')
def about() -> Response:
    '''Returns the about page.'''
    return render_template('about.html')
