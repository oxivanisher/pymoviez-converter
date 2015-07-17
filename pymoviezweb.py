#!/usr/bin/env python
# -*- coding: utf-8 -*-

# http://blogging.miguelgrinberg.com/post/the-flask-mega-tutorial-part-i-hello-world

# http://webpy.org/  http://webpy.org/docs/0.3/tutorial
# https://github.com/defunkt/pystache 
# http://blogging.miguelgrinberg.com/post/designing-a-restful-api-with-python-and-flask

# sudo apt-get install python-sqlobject python-imdbpy

import os
import sys
import signal
import logging

from helper import *

from werkzeug.utils import secure_filename
from sqlite3 import dbapi2 as sqlite3

# flask imports
try:
    from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash, make_response, send_from_directory, current_app, jsonify, Markup
except ImportError:
    log.error("[System] Please install flask")
    sys.exit(2)

try:
    from flask.ext.sqlalchemy import SQLAlchemy
    from sqlalchemy.exc import IntegrityError, InterfaceError, InvalidRequestError, OperationalError
except ImportError:
    log.error("[System] Please install the sqlalchemy extension for flask")
    sys.exit(2)

try:
    from imdb import IMDb, IMDbError
except ImportError:
    logging.error("Please install the IMDB lib: apt-get install python-imdbpy")
    sys.exit(2)

getLogger(level=logging.INFO)

app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config['scriptPath'] = os.path.dirname(os.path.realpath(__file__))
app.config['moviesList'] = False
app.config['moviesStats'] = False
app.config['dbFile'] = os.path.join(app.config['scriptPath'], 'pymoviezweb.db')

try:
    app.config.from_envvar('PYMOVIEZ_CFG', silent=False)
except RuntimeError as e:
    logging.error(e)
    sys.exit(2)

if not app.debug:
    from logging.handlers import SMTPHandler
    mail_handler = SMTPHandler(app.config['EMAILSERVER'], app.config['EMAILFROM'], ADMINS, current_app.name + ' failed!')
    mail_handler.setLevel(logging.ERROR)
    app.logger.addHandler(mail_handler)

db = SQLAlchemy(app)
with app.test_request_context():
    try:
        db.create_all()
    except OperationalError as e:
        log.warning("System] Unable to create or check database tables! DB Server is probably not available...")

# movie class
class Movie(db.Model):
    __tablename__ = 'movies'
    
    id = db.Column(db.Integer, primary_key=True)
    network_handle = db.Column(db.String(20))
    entry_name = db.Column(db.String(20))
    last_update = db.Column(db.Integer)
    cache_data = db.Column(db.UnicodeText) #MEDIUMTEXT
    
    __table_args__ = (db.UniqueConstraint(network_handle, entry_name, name="handle_name_uc"), )

    def __init__(self, network_handle, entry_name, cache_data = ""):
        self.network_handle = network_handle
        self.entry_name = entry_name
        self.last_update = 0
        self.cache_data = cache_data

    def __repr__(self):
        return '<MMONetworkCache %r>' % self.id

    def get(self):
        return json.loads(self.cache_data)

    def set(self, cache_data):
        self.cache_data = json.dumps(cache_data)

    def age(self):
        return int(time.time()) - self.last_update

# flask error handlers
@app.errorhandler(404)
def not_found(error):
    return render_template('error.html'), 404

# flask urls / paths
@app.before_first_request
def before_first_request():
    logging.info("Before first request called:")
    logging.info("dbFile:     %s" % app.config['dbFile'])
    logging.info("scriptPath: %s" % app.config['scriptPath'])

@app.route('/')
def show_index():
    moviesList = get_moviesData()
    if not os.path.isfile(app.config['dbFile']):
        init_db()
        flash('Database initialized.')
        logging.info('Database initialized.')
    if not moviesList:
        flash('Error loading movies!')
    return render_template('index.html', movies = moviesList)

@app.route('/Upload/', methods = ['POST'])
def upload():
    if 'logged_in' not in session:
        logging.info('Not logged in user tried to upload file')
    else:
        if request.method == 'POST':
            file = request.files['file']
            logging.info('Uploaded file: %s' % file.filename)
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
            logging.info("Invalid username for %s" % request.form['username'])
            flash('Invalid login')
        elif request.form['password'] != app.config['PASSWORD']:
            logging.info("Invalid password for %s" % request.form['username'])
            flash('Invalid login')
        else:
            logging.info("%s Logged in" % request.form['username'])
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
    logging.debug("Querying IMDB for movie name: %s" % token)
    try:
        s_result = ia.search_movie(token)
        logging.debug(s_result)
        for item in s_result:
            logging.debug(item['long imdb canonical title'], item.movieID)
    except IMDbError, err:
        logging.debug(err)

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
                    logging.warning('File removal error: ' % e)
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

    # textAttributes = ['Title', 'Cover', 'Country', 'Loaned', 'LoanDate', 'Length', 'URL', 'MovieID', 'MPAA', 'PersonalRating', 'PurchaseDate', 'Seen', 'Rating', 'Status', 'Plot', 'ReleaseDate', 'Notes', 'Position', 'Location']
    # listAttributes = ['Medium', 'Genre', 'Director', 'Actor' ]
    # intAttributes  = ['Year']

    if not app.config['moviesList']:
        outputDir = os.path.join(app.config['scriptPath'], app.config['OUTPUTDIR'])
        xmlFilePath = os.path.join(outputDir, 'export.xml')
        zipFilePath = os.path.join(app.config['scriptPath'], 'movies.zip')

        if not os.path.isfile(xmlFilePath):
            logging.info("Processing ZIP file")
            try:
                process_zip(zipFilePath, outputDir)
                flash('Movies extracted from ZIP')
            except IOError as e:
                logging.warning("Unable to load movies: %s" % e)
                return []

        logging.info("Loading movies from XML")
        app.config['moviesList'] = process_xml(xmlFilePath)

        for movieData in app.config['moviesList']:
            movieData['MediaString'] = ', '.join(movieData['Medium'])
            movieData['index'] = app.config['moviesList'].index(movieData)
        flash('Movies loaded from XML')
    return app.config['moviesList']

def get_moviesStats():
    if not app.config['moviesStats']:
        logging.info("Calculating statistics")
        app.config['moviesStats'] = calc_stats(get_moviesData())
        flash('Movies stats calculated')
    return app.config['moviesStats']

if __name__ == '__main__':
    app.run()