from qqueue import create_app
from qqueue.config import ProdConfig # looks for environ vars, will default to qqueue.db

application = create_app(ProdConfig) # must be called `application` for EB to work

if __name__ == "__main__":
    application.debug = True # remove before pushing to prod
    application.run()