from http import HTTPStatus
from typing import List, Optional

from flask import Flask, Response, abort, jsonify, make_response, request
from sqlalchemy.sql import func
from sqlalchemy_pagination import paginate

from .auth import auth
from .database import create_session, init_db
from .models import Movie, MovieRating, User

OPT_MOVIES = Optional[List[Movie]]
OPT_MOVIES_RATING = Optional[List[MovieRating]]
OPT_STR = Optional[str]


app = Flask(__name__)
init_db()


@app.route('/users', methods=['POST'])
def new_user() -> Response:
    username: OPT_STR = request.json.get('username')
    password: OPT_STR = request.json.get('password')
    if username is None or password is None:
        abort(HTTPStatus.BAD_REQUEST)
    with create_session() as session:
        if session.query(User).filter_by(username=username).first() is not None:
            abort(HTTPStatus.BAD_REQUEST)
        user: User = User(username=username)
        user.hash_password(password)
        session.add(user)
        session.flush()
        session.refresh(user)
        return make_response(
            jsonify({'id': user.id, 'username': user.username}),
            HTTPStatus.CREATED,
            {'Location': f'/users/{user.id}'},
        )


@app.route('/users/<int:id>')
@auth.login_required
def get_user(id: str) -> Response:
    with create_session() as session:
        user: User = session.query(User).get(int(id))
        if not user:
            abort(HTTPStatus.BAD_REQUEST)
        return make_response(jsonify({'username': user.username}), HTTPStatus.OK)


@app.route('/movies', methods=['POST'])
@auth.login_required
def add_movie() -> Response:
    name: OPT_STR = request.json.get('name')
    year: OPT_STR = request.json.get('year')
    if name is None or year is None:
        abort(HTTPStatus.BAD_REQUEST)
    with create_session() as session:
        if session.query(Movie).filter_by(name=name, year=year).first() is not None:
            abort(HTTPStatus.BAD_REQUEST)
        movie: Movie = Movie(name, year)
        session.add(movie)
        session.flush()
        session.refresh(movie)
        return make_response(
            jsonify({'id': movie.id, 'movie': movie.name, 'year': int(movie.year)}),
            HTTPStatus.CREATED,
            {'Location': f'/movies/{movie.id}'},
        )


@app.route('/movies/<int:id>', methods=['GET'])
@auth.login_required
def get_movie(id: str) -> Response:
    with create_session() as session:
        movie: Optional[Movie] = session.query(Movie).get(id)
        if not movie:
            abort(HTTPStatus.BAD_REQUEST)
        return make_response(
            jsonify({'movie': movie.name, 'year': movie.year}), HTTPStatus.OK
        )


@app.route('/movies', methods=['GET'])
def search_movie() -> Response:
    substring: OPT_STR = request.args.get('filter')
    year: OPT_STR = request.args.get('year')
    top: OPT_STR = request.args.get('top')
    size: OPT_STR = request.args.get('size')
    page: OPT_STR = request.args.get('page')
    with create_session() as session:
        if size and page:
            size: int = int(size)
            page: int = int(page)
            if substring:
                movies: OPT_MOVIES = paginate(
                    session.query(Movie).filter(Movie.name.contains(substring)),
                    page,
                    size,
                ).items
            elif year:
                movies: OPT_MOVIES = paginate(
                    session.query(Movie).filter(Movie.year == int(year)), page, size
                ).items
            elif top:
                movies: OPT_MOVIES = paginate(
                    session.query(Movie)
                    .join(MovieRating)
                    .group_by(Movie.id)
                    .order_by(func.avg(MovieRating.rating)),
                    page,
                    size,
                ).items
            else:
                movies: OPT_MOVIES = paginate(session.query(Movie), page, size).items
        else:
            if substring:
                movies: OPT_MOVIES = session.query(Movie).filter(
                    Movie.name.contains(substring)
                )
            elif year:
                movies: OPT_MOVIES = session.query(Movie).filter(
                    Movie.year == int(year)
                )

            elif top:
                movies: OPT_MOVIES = session.query(Movie).join(MovieRating).group_by(
                    Movie.id
                ).order_by(func.avg(MovieRating.rating)).limit(int(top))
            else:
                movies: OPT_MOVIES = session.query(Movie).all()
        result: dict = {
            'Movies': [
                {'id': movie.id, 'name': movie.name, 'year': movie.year}
                for movie in movies
            ]
        }
    return make_response(jsonify(result), HTTPStatus.OK)


@app.route('/movies/<int:id>/ratings', methods=['POST'])
@auth.login_required
def rate_movie(id: str) -> Response:
    rating: OPT_STR = request.json.get('rating')
    review: OPT_STR = request.json.get('review')
    if not (rating or review):
        abort(HTTPStatus.BAD_REQUEST)
    with create_session() as session:
        username = auth.username()
        user: User = session.query(User).filter_by(username=username).first()
        movie: Movie = session.query(Movie).filter_by(id=int(id)).first()
        if not movie:
            abort(HTTPStatus.BAD_REQUEST)
        user_id: int = user.id
        movie_name: str = movie.name
        movie_rating: Optional[MovieRating] = session.query(MovieRating).filter_by(
            user_id=user_id, movie_id=id
        ).first()
        result: dict = {'name': movie_name}
        if movie_rating:
            if rating:
                movie_rating.rating = rating
                result['rating'] = rating
                result['review'] = movie_rating.review
            if review:
                movie_rating.review = review
                result['rating'] = movie_rating.rating
                result['review'] = review
        else:
            movie_rating: MovieRating = MovieRating(
                user_id=user_id, movie_id=int(id), rating=int(rating), review=review
            )
            result['rating'] = movie_rating.rating
            result['review'] = movie_rating.review
            session.add(movie_rating)
        return make_response(
            jsonify(result),
            HTTPStatus.CREATED,
            {'Location': f'/movies/{id}/ratings/{movie_rating.id}'},
        )


@app.route('/movies/<int:id>/ratings', methods=['GET'])
@auth.login_required
def get_movie_rating(id: str) -> Response:
    avg: OPT_STR = request.args.get('avg')
    n_rates: OPT_STR = request.args.get('rates')
    n_reviews: OPT_STR = request.args.get('reviews')
    with create_session() as session:
        movie: Optional[Movie] = session.query(Movie).get(id)
        if not movie:
            abort(HTTPStatus.BAD_REQUEST)
        result: dict = {'Movie': movie.name}
        if avg:
            avg_rating: float = session.query(func.avg(MovieRating.rating)).filter(
                MovieRating.movie_id == id
            ).first()[0]
            result['Average rating'] = avg_rating
        elif n_rates:
            number_of_rates: int = session.query(MovieRating).filter(
                MovieRating.movie_id == id and MovieRating.rating.isnot(None)
            ).count()
            result['Number of rates'] = number_of_rates
        elif n_reviews:
            number_of_reviews: int = session.query(MovieRating).filter(
                MovieRating.movie_id == id and MovieRating.review.isnot(None)
            ).count()
            result['Number of reviews'] = number_of_reviews
        else:
            ratings_and_reviews: OPT_MOVIES_RATING = session.query(MovieRating).filter(
                MovieRating.movie_id == id
            ).all()
            result['Ratings and reviews'] = [
                {'Rating': item.rating, 'Review': item.review}
                for item in ratings_and_reviews
            ]
    return make_response(jsonify(result), HTTPStatus.OK)


@app.route('/ratings/<int:id>', methods=['GET'])
@auth.login_required
def get_rating(id: str) -> Response:
    with create_session() as session:
        movie_rating: Optional[MovieRating] = session.query(MovieRating).get(id)
        if not movie_rating:
            abort(HTTPStatus.BAD_REQUEST)
        movie_name: str = session.query(Movie).get(movie_rating.movie_id).name
        username: str = session.query(User).get(movie_rating.user_id).username
        return make_response(
            jsonify(
                {
                    'movie': movie_name,
                    'user': username,
                    'rating': movie_rating.rating,
                    'review': movie_rating.review,
                }
            )
        )
