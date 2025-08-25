"""Test for the post routes of q3.

This test relies on using flask's global app context to generate/fetch CSRF
tokens for protected forms. See test_auth.py for full explanation.
"""
import flask
import flask.testing as ft
from .conftest import user_data, post_data, comment_data, tag_data

post0 = post_data[0]
post1 = post_data[1]

def login(client:ft.FlaskClient, user_id:int=0) -> None:
    """Helper function to authenticate the test user.
    
    First makes a GET request to /login to generate a CSRF token, then 
    authenticates using the credentials for <user_id> (user 0 by default).
    
    Note that the CSRF token is retained in the global app context, which makes
    it available via flask.g.csrf_token after this method is called.

    Also note that this does not get access to pytest fixtures, so <client> must
    be passed manually.
    """
    client.get('/login')
    login_data = {'csrf_token': flask.g.csrf_token,
                  'user_email': user_data[user_id]['email'],
                  'password': user_data[user_id]['password']}
    client.post('/login', data=login_data)

def test_index(client:ft.FlaskClient) -> None:
    # Page loads
    response = client.get('/posts/')
    assert response.status_code == 200
    for p in post_data:
        assert all(x in response.text for x in p.values())
    assert f'{len(comment_data)} Comment' in response.text
    assert all(x in response.text for x in tag_data)

def test_post(client:ft.FlaskClient) -> None:
    # Page loads with all info
    response = client.get('/posts/1')
    assert response.status_code == 200
    assert all(x in response.text for x in list(post0.values()))
    assert all(x in response.text for x in comment_data)
    assert all(x in response.text for x in tag_data)

    # Redirect to index on bad post id
    response = client.get(f'/posts/{len(post_data)+1}', follow_redirects=True)
    assert response.status_code == 200
    assert response.request.path == '/posts/'

def test_new_post(client:ft.FlaskClient) -> None:
    # Login to create posts
    login(client=client) # creates CSRF token - do NOT move

    endpoint = '/posts/new' # future-proofing

    # Post is added successfully
    content_valid = {'title': 'peanuts', 'content': 'the next episode'}
    tags_valid = ['charlie brown','chuck','comics','christmas special']
    response_valid = client.post(endpoint,
                                 data={'csrf_token': flask.g.csrf_token,
                                       **content_valid,
                                       'tags': ', '.join(tags_valid)},
                                 follow_redirects=True)
    assert response_valid.status_code == 200
    assert response_valid.request.path == f'/posts/{len(post_data)+1}'
    assert all(x in response_valid.text for x in list(content_valid.values()))
    assert all(x in response_valid.text for x in tags_valid)

    # Can't add post without title (ignore redirect for post result)
    no_title = {'csrf_token': flask.g.csrf_token, 'content': 'fluff'}
    response_no_title = client.post(endpoint, data=no_title)
    assert response_no_title.status_code == 400

    # Can't add post without content (ignore redirect for post result)
    no_content = {'csrf_token': flask.g.csrf_token, 'title': 'stuff'}
    response_no_content = client.post(endpoint, data=no_content)
    assert response_no_content.status_code == 400

    # Can't add post without token
    response_no_token = client.post(endpoint, data={'title': 'nope',
                                                    'content':'fail'})
    assert response_no_token.status_code == 400

    # Can't post while logged out; redirects to login
    client.get('/logout') # do NOT move
    content_no_login = {'title': 'my spaghet', 'content': 'somebody...'}
    tags_no_login = {'three', 'bears'}
    response_no_login = client.post(endpoint,
                                    data={'csrf_token': flask.g.csrf_token,
                                          **content_no_login,
                                          'tags': tags_no_login})
    assert response_no_login.status_code == 302
    assert response_no_login.location[:6] == '/login' # some params are appended

    # confirm post was not pushed despite redirect
    all_posts = client.get('/posts/')
    assert all(x not in all_posts.text for x in list(content_no_login.values()))
    assert all(x not in all_posts.text for x in tags_no_login)

def test_edit_post(client:ft.FlaskClient) -> None:
    # Login to edit post
    login(client=client) # creates CSRF token - do NOT move

    # internal helper
    def endpoint(id_:int) -> str:
        return f'/posts/{id_}/edit'

     # Post is edited successfully - user 0 owns all posts
    data_valid = {'title': 'updated title',
                  'content': 'updated content'}
    response_valid = client.post(endpoint(id_=1),
                                 data={'csrf_token': flask.g.csrf_token,
                                       **data_valid},
                                 follow_redirects=True)
    assert response_valid.status_code == 200
    assert response_valid.request.path == '/posts/1'
    assert all(x in response_valid.text for x in list(data_valid.values()))

    # Can update with no title - will default to previous title
    no_title = {'content': 'fluff'}
    response_no_title = client.post(endpoint(id_=1),
                                    data={'csrf_token': flask.g.csrf_token,
                                          **no_title},
                                    follow_redirects=True)
    assert response_valid.status_code == 200
    assert response_valid.request.path == '/posts/1'
    assert data_valid['content'] not in response_no_title.text # from first edit
    assert all(x in response_no_title.text
               for x in [*list(no_title.values()), data_valid['title']])

    # Can update with no content - will default to previous content
    no_content = {'title': 'stuff'}
    response_no_content = client.post(endpoint(id_=1),
                                      data={'csrf_token': flask.g.csrf_token,
                                            **no_content},
                                      follow_redirects=True)
    assert response_valid.status_code == 200
    assert response_valid.request.path == '/posts/1'
    assert all(x not in response_no_content.text
               for x in list(data_valid.values())) # from first edit
    assert all(x in response_no_content.text
               for x in [*list(no_title.values()), *list(no_content.values())])

    # Can't edit without token
    data_invalid = {'title': 'Something funnier than 24', 'content': '5**2'}
    response_no_token = client.post(endpoint(id_=1), data=data_invalid)
    assert response_no_token.status_code == 400

    # Can't edit post while logged out; redirects to login
    client.get('/logout') # do NOT move
    response_no_login = client.post(endpoint(id_=1),
                                    data={'csrf_token': flask.g.csrf_token,
                                          **data_invalid})
    assert response_no_login.status_code == 302
    assert response_no_login.location[:6] == '/login' # some params are appended

    # Confirm post was not edited despite redirect
    all_posts = client.get('/posts/')
    assert all(x not in all_posts.text for x in list(data_invalid.values()))

    # Can't edit post while logged in as another user
    login(client=client, user_id=1)
    response_wrong_user = client.post(endpoint(id_=1))
    assert response_wrong_user.status_code == 403

def test_delete_post(client:ft.FlaskClient) -> None:
    # Login to delete post
    login(client=client) # creates CSRF token - do NOT move

    # internal helper
    def endpoint(id_:int) -> str:
        return f'/posts/{id_}/delete'

    # Post is deleted successfully
    response_valid = client.post(endpoint(id_=1), follow_redirects=True)
    assert response_valid.status_code == 200
    assert response_valid.request.path == '/posts/'
    assert all(x not in response_valid.text for x in list(post0.values()))

    # Can't delete same post twice
    response_double_delete = client.post(endpoint(id_=1))
    assert response_double_delete.status_code == 404

    # Can't delete nonexistent post
    response_nonexistent = client.post(endpoint(id_=len(post_data)+1))
    assert response_nonexistent.status_code == 404

    # Can't delete post while logged out; redirects to login
    client.get('/logout')
    response_no_login = client.post(endpoint(id_=2))
    assert response_no_login.status_code == 302
    assert response_no_login.location[:6] == '/login' # some params are appended

    # Confirm post was not deleted despite redirect
    all_posts = client.get('/posts/')
    assert all(x in all_posts.text for x in list(post1.values()))

    # Can't delete post while logged in as another user
    login(client=client, user_id=1)
    response_wrong_user = client.post(endpoint(id_=2))
    assert response_wrong_user.status_code == 403

def test_tags(client:ft.FlaskClient) -> None:
    # Page loads with all info
    response = client.get('/posts/tags/')
    assert response.status_code == 200
    assert all(x in response.text for x in tag_data)

def test_tag(client:ft.FlaskClient) -> None:
    # Page loads with all info
    for t in tag_data:
        response = client.get(f'/posts/tags/{t}')
        assert response.status_code == 200
        assert all(x in response.text for x in [*list(post0.values()), t])
        # ^ all tags are on the first post

def test_comments(client:ft.FlaskClient) -> None:
    # Page loads with all info
    response = client.get('/posts/comments/')
    assert response.status_code == 200
    assert all(x in response.text
               for x in [user_data[0]['username'], 'first', 'second'])

def test_add_comment(client:ft.FlaskClient) -> None:
    # Login to add comment
    login(client=client) # creates CSRF token - do NOT move

    # internal helper
    def endpoint(id_:int) -> str:
        return f'/posts/{id_}/comments/add'

    # Comment is added successfully
    content_valid = {'csrf_token': flask.g.csrf_token, 'content': 'third'}
    response_valid = client.post(endpoint(id_=1),
                                 data=content_valid,
                                 follow_redirects=True)
    assert response_valid.status_code == 200
    assert response_valid.request.path == '/posts/1'
    assert content_valid['content'] in response_valid.text

    # Can't add empty comment (ignore redirect for post result)
    content_empty = {'csrf_token': flask.g.csrf_token}
    response_empty = client.post(endpoint(id_=1), data=content_empty)
    assert response_empty.status_code == 400

    # Can't add comment to nonexistent post
    endpoint(id_=len(post_data)+1)
    response_no_post = client.post(endpoint(id_=len(post_data)+1),
                                   data=content_valid)
    assert response_no_post.status_code == 404

    # Can't add comment without token
    response_no_token = client.post(endpoint(id_=1), data={'content':'minato'})
    assert response_no_token.status_code == 400

    # Can't comment while logged out; redirects to login
    client.get('/logout') # do NOT move
    content_no_login = {'csrf_token': flask.g.csrf_token, 'content': 'fif'}
    response_no_login = client.post(endpoint(id_=1), data=content_no_login)
    assert response_no_login.status_code == 302
    assert response_no_login.location[:6] == '/login' # some params are appended

    # confirm comment was not pushed despite redirect
    all_comments = client.get('/posts/comments/')
    assert content_no_login['content'] not in all_comments.text

def test_edit_comment(client:ft.FlaskClient) -> None:
    # Login to edit comment
    login(client=client) # creates CSRF token - do NOT move
    token = {'csrf_token': flask.g.csrf_token}

    # internal helper
    def endpoint(id_:int) -> str:
        return f'/posts/comments/{id_}/edit'

    # Edit page loads with previous comment value
    response_get = client.get(endpoint(id_=1))
    assert comment_data[0] in response_get.text

    # Comment is edited successfully - all comments are on post 0 by user 0
    data_valid = {'content': 'updated content'}
    response_valid = client.post(endpoint(id_=1),
                                 data={**token,**data_valid},
                                 follow_redirects=True)
    assert response_valid.status_code == 200
    assert response_valid.request.path == '/posts/1'
    assert comment_data[0] not in response_valid.text
    assert all(x in response_valid.text for x in [data_valid['content'],
                                                  comment_data[1]])

    # Can't push empty update
    response_empty = client.post(endpoint(id_=1), data={**token})
    assert response_empty.status_code == 400

    # Can't edit without token
    data_invalid = {'content': '42'}
    response_no_token = client.post(endpoint(id_=1), data=data_invalid)
    assert response_no_token.status_code == 400

    # Can't edit comment while logged out; redirects to login
    client.get('/logout') # do NOT move
    response_no_login = client.post(endpoint(id_=1), data={**token,
                                                           **data_invalid})
    assert response_no_login.status_code == 302
    assert response_no_login.location[:6] == '/login' # some params are appended

    # Confirm comment was not edited despite redirect
    all_posts = client.get('/posts/1')
    assert all(x not in all_posts.text for x in list(data_invalid.values()))

    # Can't edit comment while logged in as another user
    login(client=client, user_id=1)
    response_wrong_user_get = client.get(endpoint(id_=1))
    assert response_wrong_user_get.status_code == 403
    response_wrong_user_post = client.post(endpoint(id_=1),
                                           data={**token, **data_invalid})
    assert response_wrong_user_post.status_code == 403

def test_delete_comment(client:ft.FlaskClient) -> None:
    # Login to delete comment
    login(client=client) # creates CSRF token - do NOT move

    # internal helper
    def endpoint(id_:int) -> str:
        return f'/posts/comments/{id_}/delete'

    # Comment is deleted successfully
    response_valid = client.post(endpoint(id_=1), follow_redirects=True)
    assert response_valid.status_code == 200
    assert response_valid.request.path == '/posts/1'
    assert 'first' not in response_valid.text

    # Can't delete same comment twice
    response_double_delete = client.post(endpoint(id_=1))
    assert response_double_delete.status_code == 404

    # Can't delete nonexistent comment
    response_nonexistent = client.post(endpoint(id_=3))
    assert response_nonexistent.status_code == 404

    # Can't delete comment while logged out; redirects to login
    client.get('/logout')
    response_no_login = client.post(endpoint(id_=2))
    assert response_no_login.status_code == 302
    assert response_no_login.location[:6] == '/login' # some params are appended
    all_comments = client.get('/posts/comments/')
    assert 'second' in all_comments.text # confirm not deleted despite redirect

    # Can't delete comment while logged in as another user
    login(client=client, user_id=1)
    response_wrong_user = client.post(endpoint(id_=2))
    assert response_wrong_user.status_code == 403