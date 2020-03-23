from movies.database import Base
from passlib.apps import custom_app_context as pwd_context
from sqlalchemy import CheckConstraint, Column, ForeignKey, Integer, String


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(128), nullable=False)

    def __init__(self, username):
        self.username = username

    def hash_password(self, password):
        self.password_hash = pwd_context.encrypt(password)

    def verify_password(self, password):
        return pwd_context.verify(password, self.password_hash)


class Movie(Base):
    __tablename__ = 'movies'
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    year = Column(Integer)

    def __init__(self, name, year):
        self.name = name
        self.year = year


class MovieRating(Base):
    __tablename__ = 'movierating'
    __table_args__ = (CheckConstraint('rating >= 0 and rating <= 10'),)
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey(User.id), nullable=False)
    movie_id = Column(Integer, ForeignKey(Movie.id), nullable=False)
    rating = Column(Integer)
    review = Column(String(512))

    def __init__(self, user_id, movie_id, rating, review=None):
        self.user_id = user_id
        self.movie_id = movie_id
        self.rating = rating
        self.review = review
