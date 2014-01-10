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

@serverApp.route('/director')
def show_director():
    stats = {}
    director = []
    allDirector = []

    for movie in movies_dict:
        for director in movie['Director']:
            allDirector.append(director)
        director = list(set(allDirector))

    for i in xrange(len(director)):
        director[i] = (director[i], allDirector.count(director[i]))

    return flask.render_template('2_colum_table.html', data = director)

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
            for movieData in movies_dict:
                movieData['Directortring'] = ', '.join(movieData['Director'])
                movieData['ActorString'] = ', '.join(movieData['Actors'])
                movieData['MediaString'] = ', '.join(movieData['Media'])
                movieData['GenreString'] = ', '.join(movieData['Genres'])
                movieData['index'] = movies_dict.index(movieData)

            print "Loaded %s movies" % len(movies_dict)
            # print movies_dict

            # go into endless loop
            # serverApp.run(host='0.0.0.0')
            serverApp.run(host=HOST, port=PORT)
            # process = Process(target=serverApp.run(host='0.0.0.0'))

        else:
            print "unrecoverable errors found. exiting!"