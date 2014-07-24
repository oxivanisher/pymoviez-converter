#!/usr/bin/env python
# -*- coding: utf-8 -*-

# http://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-i-hello-world

# http://webpy.org/  http://webpy.org/docs/0.3/tutorial
# https://github.com/defunkt/pystache 
#!/usr/bin/env python
# http://blog.miguelgrinberg.com/post/designing-a-restful-api-with-python-and-flask

# sudo apt-get install python-sqlobject python-imdbpy

import os
import sys
import signal

from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash, make_response, send_from_directory, current_app

# try:
#     import wsgilog
# except ImportError:
#     print "Please install the wsgilog lib: pip install wsgilog"
#     sys.exit(2)

try:
    from imdb import IMDb, IMDbError
except ImportError:
    print "Please install the IMDB lib: apt-get install python-imdbpy"
    sys.exit(2)

from pymoviez import *

app = Flask(__name__)
# app_logged_wsgi = wsgilog.WsgiLog(app, tohtml=False, tofile='pymoviez.log', tostream=True, toprint=True)
app.secret_key = os.urandom(24)
# app.debug = True
app.config.from_envvar('PYMOVIEZ_CFG', silent=False)
app.config['scriptPath'] = os.path.dirname(os.path.realpath(__file__))

if not app.debug:
    import logging
    from logging.handlers import SMTPHandler
    mail_handler = SMTPHandler(app.config['EMAILSERVER'],
                               app.config['EMAILFROM'],
                               ADMINS, __name__ + ' failed!')
    mail_handler.setLevel(logging.ERROR)
    app.logger.addHandler(mail_handler)

def calc_stats(moviesList):
    moviesList = get_moviesData()
    stats = {}
    countries = {}
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

        # calculate country
        if not movie['Country']:
            movie['Country'] = "Unknown"
        try:
            countries[movie['Country']] += 1
        except:
            countries[movie['Country']] = 1

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
    stats['allCountry'] = []
    for key in sorted(countries.keys()):
        stats['allCountry'].append({ 'name': key, 'count': countries[key] })

    return (stats, actor, genre, director)

# flask error handlers
@app.errorhandler(404)
def not_found(error):
    return render_template('error.html'), 404

# flask urls / paths
@app.route('/')
def show_index():
    moviesList = get_moviesData()
    if not moviesList:
        return "Error loading movies!"
    else:
        return render_template('index.html', movies = moviesList)

@app.route('/Search/<string:field>/<string:token>', methods = ['GET'])
def show_search(field, token):
    moviesList = get_moviesData()
    resultList = []
    for movie in moviesList:
        if isinstance(movie[field], int):
            if movie[field] == int(token):
                resultList.append(movie)
        elif token in movie[field]:
            resultList.append(movie)
    return render_template('search_result.html', movies = resultList, field = field, token = token)

@app.route('/Genre')
def show_genre():
    (stats, actor, genre, director) = get_moviesStats()
    return render_template('2_colum_table.html', data = genre, searchToken = "Genre")

@app.route('/Director')
def show_director():
    (stats, actor, genre, director) = get_moviesStats()
    return render_template('2_colum_table.html', data = director, searchToken = "Director")

@app.route('/Actor')
def show_actor():
    (stats, actor, genre, director) = get_moviesStats()
    return render_template('2_colum_table.html', data = actor, searchToken = "Actor")

@app.route('/Statistics')
def show_statistics():
    (stats, actor, genre, director) = get_moviesStats()
    return render_template('statistics.html', statsData = stats)

@app.route('/Problems')
def show_problems():
    moviesList = get_moviesData()
    requiredFields = get_needed_fields()
    failMovies = []
    fieldCount = 0
    for movie in moviesList:
        missing = {}
        missing['name'] = movie['Title']
        missing['index'] = moviesList.index(movie)
        missing['missingFields'] = []

        for field in requiredFields:
            if not movie[field]:
                missing['missingFields'].append(field)
                fieldCount += 1

        if len(missing['missingFields']) > 0:
            failMovies.append(missing)

    return render_template('problem_movies.html', movieData = failMovies, neededFields = requiredFields, numProblemMovies = len(failMovies), numProblemFields = fieldCount)

@app.route('/Movie/<int:movieId>', methods = ['GET'])
def show_movie(movieId):
    moviesList = get_moviesData()
    try:
        movieData = moviesList[movieId]
        return render_template('movie_details.html', movie = movieData)
    except IndexError:
        abort(404)

@app.route('/Images/<int:movieId>', methods = ['GET'])
def get_cover(movieId):
    moviesList = get_moviesData()
    cover = moviesList[movieId]['Cover']
    if cover:
        return send_from_directory('output', cover)
    else:
        abort(404)

@app.route('/Login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form['username'] != app.config['USERNAME']:
            print "Invalid username"
            flash('Invalid login')
        elif request.form['password'] != app.config['PASSWORD']:
            print "Invalid password"
            flash('Invalid login')
        else:
            print "Logged in"
            session['logged_in'] = True
            flash('Logged in')
            return redirect(url_for('admin'))
    return render_template('login.html')

@app.route('/Logout')
def logout():
    session.pop('logged_in', None)
    flash('Logged out')
    return redirect(url_for('show_index'))

@app.route('/Admin')
def admin():
    return render_template('index.html', movies = get_moviesData())

@app.route('/LookupName/<string:token>')
def search_imdb_name(token):
    ia = IMDb()
    # s_result = ia.search_movie(token)
    print "Querying IMDB for movie name: %s" % token
    try:
        s_result = ia.search_movie(token)
        print s_result
        for item in s_result:
            print item['long imdb canonical title'], item.movieID
    except IMDbError, err:
        print err


    return show_index()

def get_moviesData():
    # saving moviesData to application context since its not going to change
    with app.app_context():
        if not hasattr(current_app, 'moviesList'):
            outputDir = os.path.join(app.config['scriptPath'], app.config['OUTPUTDIR'])
            xmlFilePath = os.path.join(outputDir, 'export.xml')
            zipFilePath = os.path.join(app.config['scriptPath'], 'movies.zip')

            if not os.path.isfile(xmlFilePath):
                print "Processing ZIP file"
                process_zip(zipFilePath, outputDir)

            print "Loading movies from XML"
            current_app.moviesList = process_xml(xmlFilePath)

            for movieData in current_app.moviesList:
                movieData['MediaString'] = ', '.join(movieData['Medium'])
                movieData['index'] = current_app.moviesList.index(movieData)
        return current_app.moviesList

def get_moviesStats():
    # saving moviesStats to application context since its not going to change
    with app.app_context():
        if not hasattr(current_app, 'moviesStats'):
            print "Calculating statistics"
            current_app.moviesStats = calc_stats(get_moviesData())
        return current_app.moviesStats

if __name__ == '__main__':
    app.run()