'''Missing docstring says "what?"'''

import flask

def create_app() -> flask.Flask:
    '''Creates an instance of qqueue.'''
    app = flask.Flask(__name__)

    return app