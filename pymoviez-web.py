# http://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-i-hello-world

# http://webpy.org/  http://webpy.org/docs/0.3/tutorial
# https://github.com/defunkt/pystache 
#!/usr/bin/env python
# http://blog.miguelgrinberg.com/post/designing-a-restful-api-with-python-and-flask

import os
import sys
import flask
import signal

from pymoviez import *

HOST='127.0.0.1'
PORT=12000

moviesList = None
serverApp = flask.Flask(__name__)
serverApp.secret_key = os.urandom(24)
serverApp.debug = True

def calc_stats(moviesList):
    stats = {}
    stats['movieCount'] = len(moviesList)

    media = []
    allMedia = []

    actor = []
    allActor = []
    genre = []
    allGenre = []
    director = []
    allDirector = []

    actorToMovie = {}
    genereToMovie = {}
    directorToMovie = {}

    for movie in moviesList:
        # calculate media stats
        for medium in movie['Medium']:
            allMedia.append(medium)
        media = sorted(list(set(allMedia)))

        # calculate actor stats
        for actor in movie['Actor']:
            allActor.append(actor)
            if actor in actorToMovie.keys():
                actorToMovie[actor].append(movie['Title'])
            else:
                actorToMovie[actor] = [movie['Title']]
        actor = sorted(list(set(allActor)))

        # calculate genere stats
        for genre in movie['Genre']:
            allGenre.append(genre)
            if genre in genereToMovie.keys():
                genereToMovie[genre].append(movie['Title'])
            else:
                genereToMovie[genre] = [movie['Title']]
        genre = sorted(list(set(allGenre)))

        # calculate director stats
        for director in movie['Director']:
            allDirector.append(director)
            if director in directorToMovie.keys():
                directorToMovie[director].append(movie['Title'])
            else:
                directorToMovie[director] = [movie['Title']]
        director = sorted(list(set(allDirector)))

    for i in xrange(len(media)):
        media[i] = (media[i], allMedia.count(media[i]))
    for i in xrange(len(actor)):
        actor[i] = (actor[i], allActor.count(actor[i]), ', '.join(actorToMovie[actor[i]]))
    for i in xrange(len(genre)):
        genre[i] = (genre[i], allGenre.count(genre[i]), ', '.join(genereToMovie[genre[i]]))
    for i in xrange(len(director)):
        director[i] = (director[i], allDirector.count(director[i]), ', '.join(directorToMovie[director[i]]))

    stats['media'] = media
    stats['numMedium'] = len(media)
    stats['numActor'] = len(actor)
    stats['numGenere'] = len(genre)
    stats['numDirector'] = len(director)

    return (stats, actor, genre, director)

# flask error handlers
@serverApp.errorhandler(404)
def not_found(error):
    return flask.render_template('error.html'), 404

# flask urls / paths
@serverApp.route('/')
def show_index():
    return flask.render_template('index.html', movies = moviesList)

@serverApp.route('/search/<string:field>/<string:token>', methods = ['GET'])
def show_search(field, token):
    resultList = []
    for movie in moviesList:
        if isinstance(movie[field], int):
            if movie[field] == int(token):
                resultList.append(movie)
        elif token in movie[field]:
            resultList.append(movie)
    return flask.render_template('search_result.html', movies = resultList, field = field, token = token)

@serverApp.route('/genre')
def show_genre():
    return flask.render_template('2_colum_table.html', data = genre, searchToken = "Genre")

@serverApp.route('/director')
def show_director():
    return flask.render_template('2_colum_table.html', data = director, searchToken = "Director")

@serverApp.route('/actor')
def show_actor():
    return flask.render_template('2_colum_table.html', data = actor, searchToken = "Actor")

@serverApp.route('/statistics')
def show_statistics():
    return flask.render_template('statistics.html', statsData = stats)

@serverApp.route('/problems')
def show_problems():
    requiredFields = get_needed_fields()
    failMovies = []
    for movie in moviesList:
        missing = {}
        print movie
        print movie['Title']
        missing['name'] = movie['Title']
        missing['index'] = movie['index']
        missing['missingFields'] = []

        for field in requiredFields:
            if movie[field] != "":
                missing['missingFields'].append()

        if len(missing['missingFields']) > 0:
            failMovies.append(missing)

    return flask.render_template('problem_movies.html', movieData = failMovies)

@serverApp.route('/movie/<int:movieId>', methods = ['GET'])
def movie_detail(movieId):
    try:
        movieData = moviesList[movieId]
        return flask.render_template('movie_details.html', movie = movieData)
    except IndexError:
        flask.abort(404)

@serverApp.route('/images/<int:movieId>', methods = ['GET'])
def get_cover(movieId):
    cover = moviesList[movieId]['Cover']
    if cover:
        return flask.send_from_directory('output', cover)
    else:
        flask.abort(404)

@serverApp.route('/static/<string:folderName>/<string:fileName>', methods = ['GET'])
def get_static(fileName, folderName):
    if fileName:
        return flask.send_from_directory('static/' + folderName, fileName)
    else:
        flask.abort(404)

# main loop
if __name__ == '__main__':

    if not moviesList:
        output_dir = "output/"
        xml_file_path = process_zip('movies.zip', output_dir)
        moviesList = process_xml('output/export.xml')

        if moviesList:
            (stats, actor, genre, director) = calc_stats(moviesList)

            for movieData in moviesList:
                movieData['MediaString'] = ', '.join(movieData['Medium'])
                movieData['index'] = moviesList.index(movieData)

            print "Loaded %s movies" % len(moviesList)
            # print moviesList

            # go into endless loop
            # serverApp.run(host='0.0.0.0')
            serverApp.run(host=HOST, port=PORT)
            # process = Process(target=serverApp.run(host='0.0.0.0'))

        else:
            print "unrecoverable errors found. exiting!"