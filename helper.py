#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import os

def getLogger(level=logging.INFO):
    logPath = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'log/pymoviezweb.log')
    logging.basicConfig(filename=logPath, format='%(asctime)s %(levelname)s:%(message)s', datefmt='%Y-%d-%m %H:%M:%S', level=level)
    console = logging.StreamHandler()
    console.setLevel(logging.DEBUG)
    # formatter = logging.Formatter('%(levelname)-7s %(name)-25s| %(message)s')
    # formatter = logging.Formatter("[%(levelname)8s] --- %(message)s (%(filename)s:%(lineno)s)")
    formatter = logging.Formatter("%(levelname)-7s %(message)s (%(filename)s:%(lineno)s)")
    console.setFormatter(formatter)
    logging.getLogger('').addHandler(console)
    return logging.getLogger(__name__)

# check for allowed file extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1] in set(['zip'])

# pymoviez stats method
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

# pymoviez import methods
def process_xml(xml_data):
    if not xml_data:
        return
        
    movies = []
    movie_ids = []
    
    try:
        tree = ET.parse(xml_data)
    except Exception as e:
        logging.error("unable to load xml data: %s" % e)

    try:
        root = tree.getroot()
    except Exception as e:
        logging.error("unable to load xml data: %s" % e)
        return

    for movie in root.iter("Movie"):
        movieData = get_movie_attribs(movie)
        movies.append(movieData)

        if movieData['MovieID'] in movie_ids:
            logging.warning("Duplicated MovieID found! Please fix: %s" % movieData['Title'])
        else:
            movie_ids.append(movieData['MovieID'])

    logging.info("Parsed %s sets of movie data" % (len(movies)))
    return movies
