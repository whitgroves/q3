from qqueue import create_app
from qqueue.config import TestConfig #, CloudConfig

application = create_app(TestConfig) # must be called `application` for EB to work

if __name__ == "__main__":
    application.debug = True # remove before pushing to prod
    application.run()