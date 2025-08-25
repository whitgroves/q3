'''Missing docstring says "what?"'''

import flask

def create_app() -> flask.Flask:
    '''Creates an instance of qqueue.'''
    app = flask.Flask(__name__)

    from qqueue.routes.main import blueprint as main_routes # pylint: disable=import-outside-toplevel

    app.register_blueprint(main_routes)

    return app

if __name__ == '__main__':
    app = create_app()
    app.debug = True
    app.run()
