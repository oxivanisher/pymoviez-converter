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
import logging


from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash, make_response, send_from_directory, current_app
from werkzeug.utils import secure_filename
from sqlite3 import dbapi2 as sqlite3

logging.basicConfig(filename='/tmp/pymoviezweb.log', format='%(asctime)s %(levelname)s:%(message)s', datefmt='%Y-%d-%m %H:%M:%S', level=logging.DEBUG)
console = logging.StreamHandler()
console.setLevel(logging.INFO)
formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
console.setFormatter(formatter)
logging.getLogger('').addHandler(console)
log = logging.getLogger(__name__)

try:
    from imdb import IMDb, IMDbError
except ImportError:
    log.error("Please install the IMDB lib: apt-get install python-imdbpy")
    sys.exit(2)

from pymoviez import *

app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config['scriptPath'] = os.path.dirname(os.path.realpath(__file__))
app.config['moviesList'] = False
app.config['moviesStats'] = False
app.config['dbFile'] = "pymoviezweb.db"

try:
    app.config.from_envvar('PYMOVIEZ_CFG', silent=False)
except RuntimeError as e:
    log.error(e)
    sys.exit(2)

if not app.debug:
    from logging.handlers import SMTPHandler
    mail_handler = SMTPHandler(app.config['EMAILSERVER'], app.config['EMAILFROM'], ADMINS, current_app.name + ' failed!')
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

# check for allowed file extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1] in set(['zip'])

# flask error handlers
@app.errorhandler(404)
def not_found(error):
    return render_template('error.html'), 404

# flask urls / paths
@app.route('/')
def show_index():
    moviesList = get_moviesData()
    if not moviesList:
        flash('Error loading movies!')
    return render_template('index.html', movies = moviesList)

@app.route('/Upload/', methods = ['POST'])
def upload():
    if 'logged_in' not in session:
        log.info('Not logged in user tried to upload file')
    else:
        if request.method == 'POST':
            file = request.files['file']
            log.info('Uploaded file: %s' % file.filename)
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                # file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                file.save(os.path.join(app.config['scriptPath'], 'movies.zip'))
                flash('File uploaded')
            else:
                flash('Filename not allowed')
        else:
            flash('Wrong method')
    return redirect(url_for('admin'))

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
        return send_from_directory(os.path.join(app.config['scriptPath'], app.config['OUTPUTDIR']), cover)
    else:
        abort(404)

@app.route('/Login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form['username'] != app.config['USERNAME']:
            log.info("Invalid username for %s" % request.form['username'])
            flash('Invalid login')
        elif request.form['password'] != app.config['PASSWORD']:
            log.info("Invalid password for %s" % request.form['username'])
            flash('Invalid login')
        else:
            log.info("%s Logged in" % request.form['username'])
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
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    else:
        return render_template('admin.html')

@app.route('/Problems')
def show_problems():
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    else:
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

@app.route('/LookupName/<string:token>')
def search_imdb_name(token):
    ia = IMDb()
    # s_result = ia.search_movie(token)
    log.debug("Querying IMDB for movie name: %s" % token)
    try:
        s_result = ia.search_movie(token)
        log.debug(s_result)
        for item in s_result:
            log.debug(item['long imdb canonical title'], item.movieID)
    except IMDbError, err:
        log.debug(err)

    return show_index()

@app.route('/Admin/ReloadXML')
def reload_xml():
    if 'logged_in' in session:
        app.config['moviesList'] = False
        app.config['moviesStats'] = False
        flash('Memory cleared')
    return redirect(url_for('admin'))

@app.route('/Admin/ClearDir')
def clear_dir():
    if 'logged_in' in session:
        outputDir = os.path.join(app.config['scriptPath'], app.config['OUTPUTDIR'])
        for the_file in os.listdir(outputDir):
            file_path = os.path.join(outputDir, the_file)
            if the_file != '.keep':
                try:
                    if os.path.isfile(file_path):
                        os.unlink(file_path)
                except Exception, e:
                    log.warning('File removal error: ' % e)
        flash('Directory emptied')
    return redirect(url_for('admin'))

@app.route('/Admin/DownloadZip')
def download_zip():
    if 'logged_in' in session:
        return send_from_directory(app.config['scriptPath'], 'movies.zip')

@app.teardown_appcontext
def close_db(error):
    """Closes the database again at the end of the request."""
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()

def connect_db():
    """Connects to the specific database."""
    rv = sqlite3.connect(app.config['dbFile'])
    rv.row_factory = sqlite3.Row
    return rv

def init_db():
    """Initializes the database."""
    db = get_db()
    with app.open_resource('schema.sql', mode='r') as f:
        db.cursor().executescript(f.read())
    db.commit()

def get_db():
    """Opens a new database connection if there is none yet for the
    current application context.
    """
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = connect_db()
    return g.sqlite_db

def get_moviesData():
    db = get_db()
    # cur = db.execute('select ts, anrede, vorname, name, firma, funktion, email, bemerkungen from entries order by id desc')
    # entries = cur.fetchall()

    # textAttributes = ['Title', 'Cover', 'Country', 'Loaned', 'LoanDate', 'Length', 'URL', 'MovieID', 'MPAA', 'PersonalRating', 'PurchaseDate', 'Seen', 'Rating', 'Status', 'Plot', 'ReleaseDate', 'Notes', 'Position']
    # listAttributes = ['Medium', 'Genre', 'Director', 'Actor' ]
    # intAttributes  = ['Year']

    if not app.config['moviesList']:
        outputDir = os.path.join(app.config['scriptPath'], app.config['OUTPUTDIR'])
        xmlFilePath = os.path.join(outputDir, 'export.xml')
        zipFilePath = os.path.join(app.config['scriptPath'], 'movies.zip')

        if not os.path.isfile(xmlFilePath):
            log.info("Processing ZIP file")
            try:
                process_zip(zipFilePath, outputDir)
                flash('Movies extracted from ZIP')
            except IOError as e:
                log.warning("Unable to load movies: %s" % e)
                return []

        log.info("Loading movies from XML")
        app.config['moviesList'] = process_xml(xmlFilePath)

        for movieData in app.config['moviesList']:
            movieData['MediaString'] = ', '.join(movieData['Medium'])
            movieData['index'] = app.config['moviesList'].index(movieData)
        flash('Movies loaded from XML')
    return app.config['moviesList']

def get_moviesStats():
    if not app.config['moviesStats']:
        log.info("Calculating statistics")
        app.config['moviesStats'] = calc_stats(get_moviesData())
        flash('Movies stats calculated')
    return app.config['moviesStats']

if __name__ == '__main__':
    app.run()