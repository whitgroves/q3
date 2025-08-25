"""Test module for q3. Assumes app/ is in the same parent directory."""
import pytest
import flask
import flask.testing
import werkzeug.security as ws
import qqueue
# from qqueue import models
# from qqueue import config as cfg
# from qqueue import extensions as ext

# initialized outside of the app fixture so the other test modules can access.
# it's not "best practice" to do this, but it makes writing tests much easier.
user_data = [{'email':f'user{i}@test.net',
              'username':f'user{i}',
              'password':f'test{i}'} for i in range(2)]
post_data = [{'title': f'Underwater Basket Weaving {i+1}01',
              'content': f'Step {i}: I put on my robe and wizard hat 🧙‍♂️'} 
              for i in range(2)]
comment_data = ['first', 'second']
tag_data = [f'tag{i}' for i in range(1)]

@pytest.fixture()
def app() -> flask.Flask: # pyright: ignore[reportInvalidTypeForm]
    """Creates an instance of the q3 app.
    
    Each instance is seeded with test records and returned within q3's app
    context for ease of writing tests.
    """
    app = qqueue.create_app() #cfg.TestConfig)

    with app.app_context(): # setup test records
        # test_users = [models.User(email=u['email'],
        #                           username=u['username'],
        #                           password= \
        #                             ws.generate_password_hash(u['password']))
        #                           for u in user_data]
        # test_posts = [models.Post(title=t['title'],
        #                           content=t['content'],
        #                           user=test_users[0])
        #                           for t in post_data]
        # test_comments = [models.Comment(content=x,
        #                                 post=test_posts[0],
        #                                 user=test_users[0])
        #                                 for x in comment_data]
        # test_tags = [models.Tag(name=t) for t in tag_data]
        # test_posts[0].tags.extend(test_tags)

        # ext.db.session.add_all(test_users)
        # ext.db.session.add_all(test_posts)
        # ext.db.session.add_all(test_comments)
        # ext.db.session.add_all(test_tags)
        # ext.db.session.commit()

        # yielded in app context so downstream fixtures/tests have access to it
        # https://testdriven.io/blog/flask-contexts/#testing-example
        yield app

@pytest.fixture()
def client(app:flask.Flask) -> flask.testing.FlaskClient: # fixtures, pylint:disable=redefined-outer-name
    return app.test_client()