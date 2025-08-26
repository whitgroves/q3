"""Test for the main routes of qqueue."""
from flask.testing import FlaskClient

def test_index(client:FlaskClient) -> None:
    response = client.get('/')
    assert 'The current time is' in response.text

def test_about(client:FlaskClient) -> None:
    response = client.get('/about')
    assert '<a href="https://github.com/whitgroves" target="_blank">whitgroves</a>' in response.text # pylint: disable=line-too-long
    assert '<a href="https://linkedin.com/in/whitgroves" target="_blank">LinkedIn</a>' in response.text # pylint: disable=line-too-long
    assert '<a href="mailto:whitney.groves@gmail.com" target="_blank">whitney.groves@gmail.com</a>' in response.text # pylint: disable=line-too-long
