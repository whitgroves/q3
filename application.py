from qqueue import create_app

application = create_app() # must be called `application` for EB to work

if __name__ == "__main__":
    application.debug = True # remove before pushing to prod
    application.run()