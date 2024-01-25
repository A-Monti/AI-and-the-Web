import csv
from sqlalchemy.exc import IntegrityError
from models import Movie, MovieGenre, Links, Tags, Rating

def check_and_read_data(db):
    # check if we have movies in the database
    # read data if database is empty
    print("Number of movies: ", Movie.query.count())
    if Movie.query.count() == 0:
        # read movies from csv
        with open('data/movies.csv', newline='', encoding='utf8') as csvfile:
            reader = csv.reader(csvfile, delimiter=',')
            count = 0
            for row in reader:
                if count > 0:
                    try:
                        id = row[0]
                        title = row[1]
                        movie = Movie(id=id, title=title)
                        db.session.add(movie)
                        genres = row[2].split('|')  # genres is a list of genres
                        for genre in genres:  # add each genre to the movie_genre table
                            movie_genre = MovieGenre(movie_id=id, genre=genre)
                            db.session.add(movie_genre)
                        db.session.commit()  # save data to database
                    except IntegrityError:
                        print("Ignoring duplicate movie: " + title)
                        db.session.rollback()
                        pass
                count += 1
                if count % 100 == 0:
                    print(count, " movies read")
        
        with open('data/links.csv', newline='', encoding='utf8') as csvfile:
            reader = csv.reader(csvfile, delimiter=',')
            count = 0
            for row in reader:
                if count > 0:
                    print(row)
                    try:
                        print(row)
                        id = row[0]
                        imdb = row[1]
                        tmdb = row[2]
                        movie_links = Links(id=id, imdb_id=imdb, tmdb_id=tmdb)
                        db.session.add(movie_links)
                        db.session.commit()
                    except IntegrityError:
                        print("Ignoring duplicate movie: " + title)
                        db.session.rollback()
                        pass
                count += 1
                if count % 100 == 0:
                    print(count, " movies read")
                    
        with open('data/tags.csv', newline='', encoding='utf8') as csvfile:
            reader = csv.reader(csvfile, delimiter=',')
            count = 0
            for row in reader:
                if count > 0:
                    try:
                        print(row)
                        user_id = row[0]
                        id = row[1]
                        tag = row[2]
                        time = row[3]
                        # movie_tag = Tags(id=id, movie_id=id, user_id=user_id, tag=tag, timestamp=time)
                        movie_tag = Tags(movie_id=id, tag=tag)
                        print(movie_tag)
                        db.session.add(movie_tag)
                        db.session.commit()
                    except IntegrityError:
                        print("Ignoring duplicate movie: " + title)
                        db.session.rollback()
                        pass
                count += 1
                if count % 100 == 0:
                    print(count, " movies read")
        
        with open('data/ratings.csv', newline='', encoding='utf8') as csvfile:
            reader = csv.reader(csvfile, delimiter=',')
            count = 0
            for row in reader:
                if count > 0:
                    try:
                        print(row)
                        user_id = row[0]
                        id = row[1]
                        rating = row[2]
                        stamp = row[3]
                        # movie_tag = Tags(id=id, movie_id=id, user_id=user_id, tag=tag, timestamp=time)
                        movie_rating = Rating(user_id=user_id, movie_id=id, rating=rating, timestamp=stamp)
                        print(movie_rating)
                        db.session.add(movie_rating)
                        db.session.commit()
                    except IntegrityError:
                        print("Ignoring duplicate movie: " + title)
                        db.session.rollback()
                        pass
                count += 1
                if count % 100 == 0:
                    print(count, " movies read")

