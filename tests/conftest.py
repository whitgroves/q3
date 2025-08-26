"""Test module for qqueue. Assumes app/ is in the same parent directory."""
from pytest import fixture
from flask import Flask
from flask.testing import FlaskClient
from werkzeug.security import generate_password_hash
from qqueue import create_app
from qqueue.models import User
from qqueue.config import TestConfig
from qqueue.extensions import database

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

@fixture()
def application() -> Flask: # pyright: ignore[reportInvalidTypeForm]
    """Creates an instance of the qqueue app.
    
    Each instance is seeded with test records and returned within qqueue's app
    context for ease of writing tests.
    """
    app = create_app(TestConfig)

    with app.app_context(): # setup test records
        test_users = [User(email=u['email'],
                           username=u['username'],
                           password=generate_password_hash(u['password']))
                                for u in user_data]
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

        database.session.add_all(test_users)
        # ext.db.session.add_all(test_posts)
        # ext.db.session.add_all(test_comments)
        # ext.db.session.add_all(test_tags)
        # ext.db.session.commit()

        # yielded in app context so downstream fixtures/tests have access to it
        # https://testdriven.io/blog/flask-contexts/#testing-example
        yield app

@fixture()
def client(application:Flask) -> FlaskClient: # fixtures, pylint:disable=redefined-outer-name
    return application.test_client()
