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

movies_dict = None
serverApp = flask.Flask(__name__)
serverApp.secret_key = os.urandom(24)
serverApp.debug = True

@serverApp.route('/')
@serverApp.route('/index')
def hello_world():
    return flask.render_template('index.html', movies = movies_dict)

@serverApp.route('/genres')
def show_genres():
    stats = {}
    genres = []
    allGenres = []

    for movie in movies_dict:
        for genre in movie['Genres']:
            allGenres.append(genre)
        genres = list(set(allGenres))

    for i in xrange(len(genres)):
        genres[i] = (genres[i], allGenres.count(genres[i]))

    return flask.render_template('2_colum_table.html', data = genres)

@serverApp.route('/directors')
def show_directors():
    stats = {}
    directors = []
    allDirectors = []

    for movie in movies_dict:
        for director in movie['Directors']:
            allDirectors.append(director)
        directors = list(set(allDirectors))

    for i in xrange(len(directors)):
        directors[i] = (directors[i], allDirectors.count(directors[i]))

    return flask.render_template('2_colum_table.html', data = directors)

@serverApp.route('/actors')
def show_actors():
    stats = {}
    actors = []
    allActors = []

    for movie in movies_dict:
        for actor in movie['Actors']:
            allActors.append(actor)
        actors = list(set(allActors))

    for i in xrange(len(actors)):
        actors[i] = (actors[i], allActors.count(actors[i]))

    return flask.render_template('2_colum_table.html', data = actors)

@serverApp.route('/statistics')
def show_statistics():
    stats = {}
    stats['movieCount'] = len(movies_dict)

    media = []
    allMedia = []
    for movie in movies_dict:
        for medium in movie['Media']:
            allMedia.append(medium)
        media = list(set(allMedia))

    for i in xrange(len(media)):
        media[i] = (media[i], allMedia.count(media[i]))

    stats['dtest'] = [('test', 'ok')]

    stats['media'] = media
    stats['numMedia'] = len(media)

    return flask.render_template('statistics.html', statsData = stats)

@serverApp.route('/movie/<int:movieId>', methods = ['GET'])
def movie_detail(movieId):
    movieData = movies_dict[movieId]
    movieData['DirectorString'] = ', '.join(movieData['Directors'])
    movieData['ActorString'] = ', '.join(movieData['Actors'])
    movieData['MediaString'] = ', '.join(movieData['Media'])
    movieData['GenreString'] = ', '.join(movieData['Genres'])
    # try:
    return flask.render_template('movie_details.html', movie = movieData)
    # except 
    flask.abort(404)

@serverApp.route('/images/<int:movieId>', methods = ['GET'])
def get_cover(movieId):
    cover = movies_dict[movieId]['Cover']
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

if __name__ == '__main__':

    if not movies_dict:
        output_dir = "output/"
        xml_file_path = process_zip('movies.zip', output_dir)
        movies_dict = process_xml('output/export.xml')

        if movies_dict:
            for movie in movies_dict:
                movie['index'] = movies_dict.index(movie)

            print "loaded %s movies" % len(movies_dict)
            # print movies_dict

            # go into endless loop
            serverApp.run(host='0.0.0.0')
            # process = Process(target=serverApp.run(host='0.0.0.0'))

        else:
            print "unrecoverable errors found. exiting!"