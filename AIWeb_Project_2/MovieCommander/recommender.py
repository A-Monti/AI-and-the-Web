# Contains parts from: https://flask-user.readthedocs.io/en/latest/quickstart_app.html

from flask import Flask, render_template, request, redirect, url_for
from flask_user import login_required, UserManager, current_user
from flask_wtf import FlaskForm

from models import db, User, Movie, MovieGenre, Rating
from scipy.spatial.distance import cosine
from wtforms import FloatField, SubmitField
from wtforms.validators import DataRequired, NumberRange
from read_data import check_and_read_data

# import sleep from python
from time import sleep

import traceback

# Class-based application configuration
class ConfigClass(object):
    """ Flask application config """

    # Flask settings
    SECRET_KEY = 'This is an INSECURE secret!! DO NOT use this in production!!'

    # Flask-SQLAlchemy settings
    SQLALCHEMY_DATABASE_URI = 'sqlite:///movie_recommender.sqlite'  # File-based SQL database
    SQLALCHEMY_TRACK_MODIFICATIONS = False  # Avoids SQLAlchemy warning

    # Flask-User settings
    USER_APP_NAME = "MovieCommander"  # Shown in and email templates and page footers
    USER_ENABLE_EMAIL = False  # Disable email authentication
    USER_ENABLE_USERNAME = True  # Enable username authentication
    USER_REQUIRE_RETYPE_PASSWORD = True  # Simplify register form

    # make sure we redirect to home view, not /
    # (otherwise paths for registering, login and logout will not work on the server)
    USER_AFTER_LOGIN_ENDPOINT = 'home_page'
    USER_AFTER_LOGOUT_ENDPOINT = 'home_page'
    USER_AFTER_REGISTER_ENDPOINT = 'home_page'

# Create Flask app
app = Flask(__name__)
app.config.from_object(__name__ + '.ConfigClass')  # configuration
app.app_context().push()  # create an app context before initializing db
db.init_app(app)  # initialize database
db.create_all()  # create database if necessary
user_manager = UserManager(app, db, User)  # initialize Flask-User management

class RateMovieForm(FlaskForm):
    rating = FloatField('Rating', validators=[DataRequired(), NumberRange(min=0, max=5)])
    submit = SubmitField('Submit Rating')

@app.errorhandler(500)
def internal_error(exception):
   return "<pre>"+traceback.format_exc()+"</pre>"

@app.cli.command('initdb')
def initdb_command():
    global db
    """Creates the database tables."""
    check_and_read_data(db)
    print('Initialized the database.')


# The Home page is accessible to anyone
@app.route('/')
def home_page():
    # render home.html template
    # check_and_read_data(db)
    # return render_template("index.html")
    return render_template("home.html")


# The Members page is only accessible to authenticated users via the @login_required decorator
@app.route('/movies')
@login_required  # User must be authenticated
def movies_page():
    # String-based templates

    # first 10 movies
    movies = Movie.query.limit(100).all()

    # only Romance movies
    # movies = Movie.query.filter(Movie.genres.any(MovieGenre.genre == 'Romance')).limit(10).all()

    # only Romance AND Horror movies
    # movies = Movie.query\
    #     .filter(Movie.genres.any(MovieGenre.genre == 'Romance')) \
    #     .filter(Movie.genres.any(MovieGenre.genre == 'Horror')) \
    #     .limit(10).all()

    return render_template("movies.html", movies=movies)


@app.route('/rate/', methods=['GET', 'POST'])
@login_required  # User must be authenticated
def rate():
    movieid = request.form.get('movieid')
    rating = request.form.get('rating')
    userid = current_user.id

    forma = RateMovieForm()
    rating = Rating(user_id=userid, movie_id=movieid, rating=forma.rating.data)

    if forma.validate_on_submit():
        existing_rating = Rating.query.filter_by(user_id=userid, movie_id=movieid).first()
        print("ex - " , existing_rating)
        if existing_rating:
            existing_rating.rating = forma.rating.data
        else:
            print("rating saved: ", rating)
            db.session.add(rating)
            
        db.session.commit()
        return redirect(url_for('index'))
    print(rating.rating)
    db.session.add(rating)
    db.session.commit()
    print("Rate {} for {} by {}".format(rating.rating, movieid, userid))
    return render_template('rated.html', rating=rating.rating)


@app.route('/recommendations')
@login_required
def recommendations():
    recommendations = recommend_movies_collaborative(current_user.id)
    recommended_movie_ids = [movie_id for movie_id in recommendations]
    recommended_movies = []
    for movie in Movie.query.filter(Movie.id.in_(recommended_movie_ids)).all():
        recommended_movies.append({
            'movie_id': movie.id,
            'genres': movie.genres,
            'similarity': recommendations[movie.id],
            'tags': movie.tags,
            'title': movie.title
        })
    print(recommended_movies)
    return render_template('collab_rm.html', recommended_movies=recommended_movies)
    
@app.route('/recommendations/<int:movie_id>')
@login_required
def content_rm(movie_id):
    recommendations = recommend_movies_content_based(movie_id)
    recommended_movie_ids = [movie_id for movie_id in recommendations]
    recommended_movies = []
    for movie in Movie.query.filter(Movie.movie_id.in_(recommended_movie_ids)).all():
        recommended_movies.append({
            'movie_id': movie.movie_id,
            'similarity': recommendations[movie.movie_id],
            'title': movie.title
        })
    return render_template('content_rm.html', recommended_movies=recommended_movies)
    
@app.route('/ratings')
@login_required
def ratings():
    ratings = get_user_ratings(current_user.id)
    # print(ratings)
    ratings_movie_ids = [movie_id for movie_id in ratings]
    # ratings_movie_ids_sorted = sort_by_rating(ratings_movie_ids)
    # print(ratings_movie_ids_sorted)
    ratings_movies = []
    for movie in Movie.query.filter(Movie.id.in_(ratings_movie_ids)).all():
        ratings_movies.append({
            'movie_id': movie.id,
            'genres': movie.genres,
            'tags': movie.tags,
            'links': movie.links,
            'rating': ratings[movie.id],
            'title': movie.title
        })
    # ratings_movies = Movie.query.filter(Rating.rating.in_(ratings_movies)).all()
    return render_template('ratings.html', ratings=ratings_movies)

# def sort_by_rating(rating_ids):
#     for movie in 

def get_user_ratings(user_id):
    user_ratings = Rating.query.filter_by(user_id=user_id).all()
    return {rating.movie_id: rating.rating for rating in user_ratings}

def get_movie_ratings(movie_id):
    movie_ratings = Rating.query.filter_by(movie_id=movie_id).all()
    return {rating.user_id: rating.rating for rating in movie_ratings}

def calculate_user_similarity(user_ratings, other_user_ratings):
    # Calculate cosine similarity between two user rating vectors
    common_movies = set(user_ratings.keys()) & set(other_user_ratings.keys())
    if not common_movies:
        return 0.0  # No common movies, similarity is 0
    vector1 = [user_ratings[movie_id] for movie_id in common_movies]
    vector2 = [other_user_ratings[movie_id] for movie_id in common_movies]
    similarity = 1 - cosine(vector1, vector2)
    return similarity

def calculate_movie_similarity(movie_ratings1, movie_ratings2):
    # Calculate cosine similarity between two movie rating vectors
    common_users = set(movie_ratings1.keys()) & set(movie_ratings2.keys())
    if not common_users:
        return 0.0  # No common users, similarity is 0
    vector1 = [movie_ratings1[user_id] for user_id in common_users]
    vector2 = [movie_ratings2[user_id] for user_id in common_users]
    similarity = 1 - cosine(vector1, vector2)
    return similarity

def recommend_movies_collaborative(user_id, top_n=10):
    user_ratings = get_user_ratings(user_id)
    # print('Query all ratings...')
    print("user ratings: ", user_ratings)
    all_ratings = Rating.query.limit(5000).all()
    print("All ratings: ", all_ratings)
    print('Get ratings of users...')
    other_users_ratings = {rating.user_id: get_user_ratings(rating.user_id) for rating in all_ratings}
    print('Calculate user similarities...')
    movie_similarities = [(other_user_id, calculate_user_similarity(user_ratings, other_user_ratings)) for other_user_id, other_user_ratings in other_users_ratings.items() if other_user_id != user_id]
    movie_similarities.sort(key=lambda x: x[1], reverse=True)
    recommended_movies = {}
    for movie_id, similarity in movie_similarities[:top_n]:
        # Exclude movies the user has already rated
        if movie_id not in user_ratings:
            recommended_movies[movie_id] = similarity
    return recommended_movies

def recommend_movies_content_based(movie_id, top_n=10):
    target_movie_ratings = get_movie_ratings(movie_id)
    all_movies_ratings = {movie.movie_id: get_movie_ratings(movie.movie_id) for movie in Movie.query.all()}
    print('Calculate movie similarities...')
    movie_similarities = [(other_movie_id, calculate_movie_similarity(target_movie_ratings, other_movie_ratings)) for other_movie_id, other_movie_ratings in all_movies_ratings.items() if other_movie_id != movie_id]
    movie_similarities.sort(key=lambda x: x[1], reverse=True)
    recommended_movies = {}
    for other_movie_id, similarity in movie_similarities[:top_n]:
        recommended_movies[other_movie_id] = similarity
    return recommended_movies


# Start development web server
if __name__ == '__main__':
    try:
        app.run(port=5000, debug=True)
    except ModuleNotFoundError:
        pass
