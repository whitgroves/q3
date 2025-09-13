'''Separate file for flask extensions to avoid circular references.'''

from flask import current_app, request, abort
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import warnings
warnings.simplefilter('ignore') # ignore DeprecationWarning in web3
from web3 import Web3, EthereumTesterProvider

database = SQLAlchemy()
login = LoginManager()
w3 = Web3(EthereumTesterProvider())

def endpoint_exception() -> None:
    '''
    Handler for unexpected HTTP requests abstracted out to make coding easier.
    Logs the request and aborts it with HTTP code 405 (Method Not Allowed)
    '''
    current_app.logger.warning(f'405: {request.path} {request.method}: {request}') # pylint: disable=line-too-long
    abort(405)

# No type hints as this would cause circular imports because of database
# being imported into qqueue.models. TODO: fix this
def display_user(user):
    '''
    Helper that modifies `User` fields to display expected values, instead of
    converting values like `None` to "None".
    '''
    user.headline = user.headline or ''
    user.bio = user.bio or ''
    return user