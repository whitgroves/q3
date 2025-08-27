'''Missing docstring says "what?"'''

import os
from flask import Flask
from sqlalchemy import inspect
from qqueue.config import BaseConfig, DevConfig, DATABASE_DIR, SQLITE_PREFIX
from qqueue.extensions import database, login

def create_app(config:BaseConfig=DevConfig) -> Flask:
    '''Creates and returns an instance of qqueue. Order matters here.'''

    # create instance
    app = Flask(__name__)
    app.config.from_object(config)
    if app.testing: app.logger.info('App configured for testing mode.')

    # init extensions
    database.init_app(app=app)
    login.init_app(app=app)

    # internal imports to avoid circular references
    from qqueue.models import User                              # pylint: disable=import-outside-toplevel
    from qqueue.routes.main import blueprint as main_routes     # pylint: disable=import-outside-toplevel
    from qqueue.routes.auth import blueprint as auth_routes     # pylint: disable=import-outside-toplevel
    from qqueue.routes.users import blueprint as user_routes    # pylint: disable=import-outside-toplevel

    # init login
    login.login_view = 'auth.login'
    @login.user_loader
    def load_user(user_id:int) -> User|None:
        return User.query.get(int(user_id))

    # register routes
    app.register_blueprint(main_routes)
    app.register_blueprint(auth_routes)
    app.register_blueprint(user_routes, url_prefix='/users')

    # init database
    if SQLITE_PREFIX in config.SQLALCHEMY_DATABASE_URI:
        os.makedirs(DATABASE_DIR, exist_ok=True)
    with app.app_context():
        tables = [User]
        if app.testing or not all(inspect(database.engine).has_table(x.__tablename__) for x in tables): #pylint: disable=line-too-long
            app.logger.warning('Rebuilding database...')
            database.drop_all()
            database.create_all()
    app.logger.info('Database ready.')

    return app


if __name__ == '__main__':
    application = create_app()
    application.debug = True
    application.run()
