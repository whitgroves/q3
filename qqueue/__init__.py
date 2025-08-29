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
    from qqueue.models import User, Task                        # pylint: disable=import-outside-toplevel
    from qqueue.routes.main import blueprint as main_routes     # pylint: disable=import-outside-toplevel
    from qqueue.routes.auth import blueprint as auth_routes     # pylint: disable=import-outside-toplevel
    from qqueue.routes.users import blueprint as user_routes    # pylint: disable=import-outside-toplevel
    from qqueue.routes.tasks import blueprint as task_routes    # pylint: disable=import-outside-toplevel

    # init login
    login.login_view = 'auth.login'
    @login.user_loader
    def load_user(user_id:int) -> User|None:
        return User.query.get(int(user_id))

    # register routes
    app.register_blueprint(main_routes)
    app.register_blueprint(auth_routes)
    app.register_blueprint(user_routes, url_prefix='/users')
    app.register_blueprint(task_routes, url_prefix='/tasks')

    # init database
    if SQLITE_PREFIX in config.SQLALCHEMY_DATABASE_URI:
        os.makedirs(DATABASE_DIR, exist_ok=True)
    with app.app_context():
        rebuild_database = app.testing # Always rebuild on test
        if not rebuild_database:
            inspector = inspect(database.engine)
            # Don't forget to add new tables !!!
            for table in [User, Task]:
                # Check that each table exists
                if not inspector.has_table(table.__tablename__):
                    rebuild_database = True
                # And if it does, that all its columns are present in the model
                if not rebuild_database:
                    for column in inspector.get_columns(table.__tablename__):
                        if not hasattr(table, column['name']):
                            rebuild_database = True
                            break
                # If any snags are hit, stop immediately
                else: break
        # if (vs else) in case flag flipped during integrity check
        if rebuild_database:
            app.logger.log(level=(20 if app.testing else 40),
                           msg='Rebuilding database...')
            database.drop_all()
            database.create_all()
    app.logger.info('Database ready.')

    return app


if __name__ == '__main__':
    application = create_app()
    application.debug = True
    application.run()
