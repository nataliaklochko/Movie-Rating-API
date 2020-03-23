import base64
import json
from http import HTTPStatus

import pytest
from movies.api import app


@pytest.fixture(scope='module')
def test_client():
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    testing_client = app.test_client()
    ctx = app.app_context()
    ctx.push()
    yield testing_client
    ctx.pop()


def test_create_user(test_client):
    response = test_client.post('/users', json={'username': 'user', 'password': 'pass'})
    assert response.status_code == HTTPStatus.CREATED
    response_second_user = test_client.post(
        '/users', json={'username': 'user', 'password': 'pass'}
    )
    assert response_second_user.status_code == HTTPStatus.BAD_REQUEST


def test_get_user(test_client):
    test_client.post('/users', json={'username': 'user', 'password': 'pass'})
    response = test_client.get(
        '/users/1',
        headers={
            'Authorization': 'Basic ' + base64.b64encode(b'user:pass').decode('utf-8')
        },
    )
    assert response.status_code == HTTPStatus.OK
    assert json.loads(response.data) == {'username': 'user'}


def test_add_movie(test_client):
    response = test_client.post(
        '/movies',
        json={'name': 'film', 'year': 2020},
        headers={
            'Authorization': 'Basic ' + base64.b64encode(b'user:pass').decode('utf-8')
        },
    )
    assert response.status_code == HTTPStatus.CREATED
    assert json.loads(response.data) == {'id': 1, 'movie': 'film', 'year': 2020}


def test_add_movie_error(test_client):
    response = test_client.post(
        '/movies',
        json={'name': 'film'},
        headers={
            'Authorization': 'Basic ' + base64.b64encode(b'user:pass').decode('utf-8')
        },
    )
    assert response.status_code == HTTPStatus.BAD_REQUEST


def test_add_movie_already_exists(test_client):
    response = test_client.post(
        '/movies',
        json={'name': 'film', 'year': 2020},
        headers={
            'Authorization': 'Basic ' + base64.b64encode(b'user:pass').decode('utf-8')
        },
    )
    assert response.status_code == HTTPStatus.BAD_REQUEST


def test_get_movie(test_client):
    response = test_client.get(
        '/movies/1',
        headers={
            'Authorization': 'Basic ' + base64.b64encode(b'user:pass').decode('utf-8')
        },
    )
    assert response.status_code == HTTPStatus.OK
    assert json.loads(response.data) == {'movie': 'film', 'year': 2020}


def test_get_movie_error(test_client):
    response = test_client.get(
        '/movies/100',
        headers={
            'Authorization': 'Basic ' + base64.b64encode(b'user:pass').decode('utf-8')
        },
    )
    assert response.status_code == HTTPStatus.BAD_REQUEST


def test_get_movies(test_client):
    response = test_client.get(
        '/movies',
        headers={
            'Authorization': 'Basic ' + base64.b64encode(b'user:pass').decode('utf-8')
        },
    )
    assert response.status_code == HTTPStatus.OK
    assert json.loads(response.data) == {
        'Movies': [{'id': 1, 'name': 'film', 'year': 2020}]
    }


def test_search_movie(test_client):
    test_client.post(
        '/movies',
        json={'name': 'new_film', 'year': '2020'},
        headers={
            'Authorization': 'Basic ' + base64.b64encode(b'user:pass').decode('utf-8')
        },
    )
    response = test_client.get(
        '/movies?filter=new',
        headers={
            'Authorization': 'Basic ' + base64.b64encode(b'user:pass').decode('utf-8')
        },
    )
    assert response.status_code == HTTPStatus.OK
    assert json.loads(response.data) == {
        'Movies': [{'id': 2, 'name': 'new_film', 'year': 2020}]
    }
    response_page = test_client.get(
        '/movies?filter=new&page=1&size=1',
        headers={
            'Authorization': 'Basic ' + base64.b64encode(b'user:pass').decode('utf-8')
        },
    )
    assert response_page.data == response.data


def test_search_movie_year(test_client):
    test_client.post(
        '/movies',
        json={'name': 'film_2021', 'year': '2021'},
        headers={
            'Authorization': 'Basic ' + base64.b64encode(b'user:pass').decode('utf-8')
        },
    )
    response = test_client.get(
        '/movies?year=2021',
        headers={
            'Authorization': 'Basic ' + base64.b64encode(b'user:pass').decode('utf-8')
        },
    )
    assert response.status_code == HTTPStatus.OK
    assert json.loads(response.data) == {
        'Movies': [{'id': 3, 'name': 'film_2021', 'year': 2021}]
    }
    response_page = test_client.get(
        '/movies?year=2021&page=1&size=1',
        headers={
            'Authorization': 'Basic ' + base64.b64encode(b'user:pass').decode('utf-8')
        },
    )
    assert response_page.data == response.data


def test_rate_movie(test_client):
    response = test_client.post(
        '/movies/1/ratings',
        json={'rating': 5, 'review': 'good'},
        headers={
            'Authorization': 'Basic ' + base64.b64encode(b'user:pass').decode('utf-8')
        },
    )
    assert response.status_code == HTTPStatus.CREATED
    assert json.loads(response.data) == {'name': 'film', 'rating': 5, 'review': 'good'}


def test_rate_movie_rating(test_client):
    response = test_client.post(
        '/movies/1/ratings',
        json={'rating': 5},
        headers={
            'Authorization': 'Basic ' + base64.b64encode(b'user:pass').decode('utf-8')
        },
    )
    assert response.status_code == HTTPStatus.CREATED
    assert json.loads(response.data) == {'name': 'film', 'rating': 5, 'review': 'good'}


def test_rate_movie_review(test_client):
    response = test_client.post(
        '/movies/1/ratings',
        json={'review': 'good'},
        headers={
            'Authorization': 'Basic ' + base64.b64encode(b'user:pass').decode('utf-8')
        },
    )
    assert response.status_code == HTTPStatus.CREATED
    assert json.loads(response.data) == {'name': 'film', 'rating': 5, 'review': 'good'}


def test_rate_movie_error(test_client):
    response = test_client.post(
        '/movies/100/ratings',
        json={'rating': 5, 'review': 'good'},
        headers={
            'Authorization': 'Basic ' + base64.b64encode(b'user:pass').decode('utf-8')
        },
    )
    assert response.status_code == HTTPStatus.BAD_REQUEST


def test_search_movie_top(test_client):
    response = test_client.get(
        '/movies?top=1',
        headers={
            'Authorization': 'Basic ' + base64.b64encode(b'user:pass').decode('utf-8')
        },
    )
    assert response.status_code == HTTPStatus.OK
    assert json.loads(response.data) == {
        'Movies': [{'id': 1, 'name': 'film', 'year': 2020}]
    }
    response_page = test_client.get(
        '/movies?top=1&page=1&size=1',
        headers={
            'Authorization': 'Basic ' + base64.b64encode(b'user:pass').decode('utf-8')
        },
    )
    assert response_page.data == response.data


def get_rating(test_client):
    response = test_client.get(
        '/ratings/1',
        headers={
            'Authorization': 'Basic ' + base64.b64encode(b'user:pass').decode('utf-8')
        },
    )
    assert response.status_code == HTTPStatus.OK
    assert json.loads(response.data) == {
        'movie': 'film',
        'user': 'user',
        'rating': 5,
        'review': 'good',
    }


def get_movie_rating_error(test_client):
    response = test_client.get(
        '/movie/100/ratings',
        headers={
            'Authorization': 'Basic ' + base64.b64encode(b'user:pass').decode('utf-8')
        },
    )
    assert response.status_code == HTTPStatus.BAD_REQUEST


def get_movie_rating_avg(test_client):
    response = test_client.get(
        '/movie/1/ratings?avg=true',
        headers={
            'Authorization': 'Basic ' + base64.b64encode(b'user:pass').decode('utf-8')
        },
    )
    assert response.status_code == HTTPStatus.OK
    assert json.loads(response.data) == {'Movie': 'film', 'Average rating': 5}


def get_movie_rating_total_rates(test_client):
    response = test_client.get(
        '/movie/1/ratings?rates=true',
        headers={
            'Authorization': 'Basic ' + base64.b64encode(b'user:pass').decode('utf-8')
        },
    )
    assert response.status_code == HTTPStatus.OK
    assert json.loads(response.data) == {'Movie': 'film', 'Number of rates': 1}


def get_movie_rating_total_reviews(test_client):
    response = test_client.get(
        '/movie/1/ratings?reviews=true',
        headers={
            'Authorization': 'Basic ' + base64.b64encode(b'user:pass').decode('utf-8')
        },
    )
    assert response.status_code == HTTPStatus.OK
    assert json.loads(response.data) == {'Movie': 'film', 'Number of reviews': 1}


def test_create_user_error(test_client):
    response = test_client.post('/users', json={'username': 'user'})
    assert response.status_code == HTTPStatus.BAD_REQUEST


def test_get_user_unauth(test_client):
    test_client.post('/users', json={'username': 'user', 'password': 'pass'})
    response = test_client.get('/users/1')
    assert response.status_code == HTTPStatus.UNAUTHORIZED


def test_get_user_error(test_client):
    test_client.post('/users', json={'username': 'user', 'password': 'pass'})
    response = test_client.get(
        '/users/10',
        headers={
            'Authorization': 'Basic ' + base64.b64encode(b'user:pass').decode('utf-8')
        },
    )
    assert response.status_code == HTTPStatus.BAD_REQUEST


def test_get_movie_rating_empty(test_client):
    response = test_client.post(
        '/movies',
        json={'name': 'film_without_rating', 'year': '2020'},
        headers={
            'Authorization': 'Basic ' + base64.b64encode(b'user:pass').decode('utf-8')
        },
    )
    movie_id = json.loads(response.data)['id']
    response = test_client.get(
        f'/movies/{movie_id}/ratings',
        headers={
            'Authorization': 'Basic ' + base64.b64encode(b'user:pass').decode('utf-8')
        },
    )
    assert response.status_code == HTTPStatus.OK


def get_rating_error(test_client):
    response = test_client.get(
        '/ratings/100',
        headers={
            'Authorization': 'Basic ' + base64.b64encode(b'user:pass').decode('utf-8')
        },
    )
    assert response.status_code == HTTPStatus.BAD_REQUEST
