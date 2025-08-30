'''Separate file for flask extensions to avoid circular references.'''

from flask import current_app, request, abort
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager


database = SQLAlchemy()
login = LoginManager()

def endpoint_exception() -> None:
    '''
    Handler for unexpected HTTP requests abstracted out to make coding easier.
    Logs the request and aborts it with HTTP code 405 (Method Not Allowed)
    '''
    current_app.logger.warning(f'405: {request.path} {request.method}: {request}')
    abort(405)