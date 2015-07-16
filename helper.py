#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import os
import zipfile
import hashlib
import xml.etree.ElementTree as ET

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

# some checks
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1] in set(['zip'])

def get_needed_fields():
        return ['Title', 'MovieID', 'Medium', 'Year', 'Genre', 'Director', 'Actor', 'Cover', 'Country', 'Length', 'MPAA', 'Plot', 'ReleaseDate']

# hashfile
def hashfile(filepath):
    # helper function http://stackoverflow.com/questions/1869885/calculating-sha1-of-a-file
    sha1 = hashlib.sha1()
    f = open(filepath, 'rb')
    try:
        sha1.update(f.read())
    finally:
        f.close()
    return sha1.hexdigest()

def get_histfile():
    return os.path.join(os.path.expanduser("~"), ".pymoviez-converter-lasthash")

def load_old_hash():
    old_hash = None
    try:
        file = open(get_histfile(), 'r')
        old_hash = file.read()
        file.close()
        return old_hash
    except IOError:
        pass

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

def process_zip(file_name, output_dir):
    xml_file_name = "export.xml"
    xml_file_path = None
    try:
        zfobj = zipfile.ZipFile(file_name)
    except zipfile.BadZipfile:
        logging.error("File is not a zip file")
        return

    if hashfile(file_name) == load_old_hash():
        logging.info("Not running, same hashes that means no update")
        return

    if xml_file_name not in zfobj.namelist():
        logging.error("No %s found in zipfile" % xml_file_name)
        return
    else:
        cover_count = 0
        for name in zfobj.namelist():
            try:
                uncompressed = zfobj.read(name)
            except Exception as e:
                logging.error("Error opening Zip File: %s" % e)
                return

            # save uncompressed data to disk
            outputFilename = os.path.join(output_dir, name)
            output = open(outputFilename,'wb')
            output.write(uncompressed)
            output.close()

            if name == xml_file_name:
                xml_file_path = outputFilename
            else:
                cover_count += 1

        logging.info("Found %s covers and xml %s" % (cover_count, xml_file_path))
        return xml_file_path

def get_movie_attribs(movie):
    scriptPath = os.path.dirname(os.path.realpath(__file__))
    textAttributes = ['Title', 'Cover', 'Country', 'Loaned', 'LoanDate', 'Length', 'URL', 'MovieID', 'MPAA', 'PersonalRating', 'PurchaseDate', 'Seen', 'Rating', 'Status', 'Plot', 'ReleaseDate', 'Notes', 'Position', 'Location']
    listAttributes = ['Medium', 'Genre', 'Director', 'Actor' ]
    intAttributes  = ['Year']
    neededFields = get_needed_fields()
    movieData = {}
    unknownTags = []

    for attrib in movie.iter("*"):
        if attrib.tag in textAttributes:
            if attrib.text:
                movieData[attrib.tag] = attrib.text
            else:
                movieData[attrib.tag] = ""
        elif attrib.tag in intAttributes:
            if attrib.text:
                movieData[attrib.tag] = int(attrib.text)
            else:
                movieData[attrib.tag] = 0
        elif attrib.tag in listAttributes:
            try:
                movieData[attrib.tag]
            except:
                movieData[attrib.tag] = []

            if attrib.tag == "Medium":
                movieData[attrib.tag].append(attrib.text)
            elif attrib.tag == "Genre":
                if attrib.text:
                    if "&" in attrib.text:
                        for value in attrib.text.split('&'):
                            movieData[attrib.tag].append(value.strip())
                    else:
                        movieData[attrib.tag].append(attrib.text)
            elif attrib.tag == "Director":
                if attrib.text:
                    if "," in attrib.text:
                        for value in attrib.text.split(','):
                            movieData[attrib.tag].append(value.strip())
                    else:
                        movieData[attrib.tag].append(attrib.text)
            elif attrib.tag == "Actor":
                if attrib.text:
                    if attrib.text.count(',') > 1:
                        for value in attrib.text.split(','):
                            movieData[attrib.tag].append(value.strip())
                    else:
                        movieData[attrib.tag].append(attrib.text)
        else:
            if attrib.text:
                if len(attrib.text.strip()) > 0:
                    unknownTags.append(attrib.tag)

    for field in neededFields:
        if field not in movieData:
            tmpTitle = os.urandom(16).encode('hex')
            if 'Title' in movieData:
                tmpTitle = movieData['Title']
            # movieData[field] = tmpTitle

    for field in textAttributes:
        if field not in movieData.keys():
            movieData[field] = ""
    for field in listAttributes:
        if field not in movieData.keys():
            movieData[field] = []
    for field in intAttributes:
        if field not in movieData.keys():
            movieData[field] = 0

    if len(unknownTags) > 0:
        logging.info("Unknown or empty tags for movie: %s (%s)" % (movieData['Title'], ', '.join(unknownTags)))

    if movieData['Cover']:
        if not os.path.isfile(os.path.join(scriptPath, "output/", movieData['Cover'])):
            logging.info("Missing Cover for movie: %s" % movieData['Title'])

    if 'Year' in movieData.keys() < 10:
        movieData['Year'] = 0
        logging.info("Missing movie Year for: %s" % movieData['Title'])

    if 'Length' not in movieData.keys():
        movieData['Length'] = 0
    elif "min" in movieData['Length']:
        movieData['Length'] = movieData['Length'].replace('min', '').strip()

    return movieData