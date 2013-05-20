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

@serverApp.route('/generes')
def show_generes():
    return flask.render_template('generes.html', generes = generes)

@serverApp.route('/movie/<int:movieId>', methods = ['GET'])
def movie_detail(movieId):
    # try:
    return flask.render_template('movie_details.html', movie = movies_dict[movieId])
    # except 
    flask.abort(404)

@serverApp.route('/images/<int:movieId>', methods = ['GET'])
def get_cover(movieId):
    cover = movies_dict[movieId]['Cover']
    if cover:
        return flask.send_from_directory('output', cover)
    else:
        flask.abort(404)

@serverApp.route('/static/<string:fileName>', methods = ['GET'])
def get_static(fileName):
    if fileName:
        return flask.send_from_directory('static', fileName)
    else:
        flask.abort(404)

if __name__ == '__main__':

    if not movies_dict:
        # output_dir = "output/"
        # xml_file_path = process_zip('movies.zip', output_dir)
        movies_dict = process_xml('output/export.xml')
        generes = []
        count = 0
        for movie in movies_dict:
            movie['index'] = movies_dict.index(movie)
            for genere in movie['Genre']:
                generes.append(genere)

        generes = list(set(generes))
        print "loaded %s movies" % len(movies_dict)
        # print movies_dict

    # go into endless loop
    serverApp.run(host='0.0.0.0')
    # process = Process(target=serverApp.run(host='0.0.0.0'))
