"""Test for the main routes of q3."""
from flask import testing

def test_index(client:testing.FlaskClient) -> None:
    response = client.get('/')
    assert 'The current time is' in response.text

def test_about(client:testing.FlaskClient) -> None:
    response = client.get('/about')
    test_link = 'https://github.com/whitgroves/q3'
    assert f'<a href="{test_link}" target="_blank">' in response.text