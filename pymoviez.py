#!/usr/bin/env python

import os
# import urllib
import hashlib
import sys
import zipfile
import os.path
import xml.etree.ElementTree as ET

# http://stackoverflow.com/questions/7806563/how-to-unzip-a-zip-file-with-python-2-4
def get_needed_fields():
        return ['Title', 'MovieID', 'Medium', 'Year', 'Genre', 'Director', 'Actor', 'Cover', 'Country', 'Length', 'MPAA', 'Plot', 'ReleaseDate']

def get_movie_attribs(movie):
    textAttributes = ['Title', 'Cover', 'Country', 'Loaned', 'LoanDate', 'Length', 'URL', 'MovieID', 'MPAA', 'PersonalRating', 'PurchaseDate', 'Seen', 'Rating', 'Status', 'Plot', 'ReleaseDate', 'Notes', 'Position']
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
            print "Missing field: %s for %s" % (field, tmpTitle)
            movieData[field] = tmpTitle

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
        print "Unknown or empty tags for movie: %s (%s)" % (movieData['Title'], ', '.join(unknownTags))

    if movieData['Cover']:
        if not os.path.isfile("output/" + movieData['Cover']):
            print "Missing Cover for movie: %s" % movieData['Title']

    if 'Year' in movieData.keys() < 10:
        movieData['Year'] = 0
        print "Missing movie Year for: %s" % movieData['Title']

    if 'Length' not in movieData.keys():
        movieData['Length'] = 0
    elif "min" in movieData['Length']:
        movieData['Length'] = movieData['Length'].replace('min', '').strip()

    return movieData

def process_xml(xml_data):
    if not xml_data:
        return
        
    movies = []
    movie_ids = []
    
    try:
        tree = ET.parse(xml_data)
    except Exception as e:
        print "unable to load xml data: %s" % e

    try:
        root = tree.getroot()
    except Exception as e:
        print "unable to load xml data: %s" % e
        return

    for movie in root.iter("Movie"):
        movieData = get_movie_attribs(movie)
        movies.append(movieData)

        if movieData['MovieID'] in movie_ids:
            print "WARNING: duplicated MovieID found! Please fix: %s" % movieData['Title']
        else:
            movie_ids.append(movieData['MovieID'])

    print "Parsed %s sets of movie data" % (len(movies))
    return movies

def create_html(movies):
    html_data  = "<html><head><title>Movie List</title></head><body>\n"
    html_data += "<table>\n" #<tr><th>Title</th><th>Medium</th></tr>
    for movie in movies:
        if movie['URL']:
            title = "<a href='%s' target='_new'>%s</a>" % (movie['URL'], movie['Title'].encode('ascii', 'xmlcharrefreplace'))
        else:
            title = movie['Title'].encode('ascii', 'xmlcharrefreplace')

        if movie['Cover']:
            cover = "<img src='%s' alt='%s' style='max-height: 80px; max-width: 80px'/>" % (movie['Cover'], movie['Title'].encode('ascii', 'xmlcharrefreplace'))
        else:
            cover = ""

        if movie['Year']:
            if movie['Country']:
                year = " (" + movie['Country'] +  ", " + str(movie['Year']) + ")"
            else:
                year = " (" + str(movie['Year']) + ")"
        else:
            year = ""

        if movie['Genre']:
            genre = " | " + movie['Genre']
        else:
            genre = ""

        if movie['Medium']:
            medium = " | " + movie['Medium']
        else:
            medium = ""

        html_data += "<tr><td>%s</td><td><b>%s%s</b><br />%s%s%s</td></tr>\n" % (cover,
                                                                                title,
                                                                                year,
                                                                                movie['Length'],
                                                                                genre,
                                                                                medium)
    html_data += "</table></body></html>\n"

    print "created html table with %s entries" % len(movies)
    return html_data

def create_csv(movies):
    csv_data  = ""
    for movie in movies:
        csv_data += "%s;%s;%s;%s;%s;%s;%s;%s;%s\n" % (movie['Title'].encode("utf-8"),
                                                movie['Year'],
                                                movie['Country'],
                                                movie['Length'],
                                                movie['Genre'].encode("utf-8"),
                                                movie['Medium'],
                                                movie['Loaned'].encode("utf-8"),
                                                movie['LoanDate'],
                                                movie['Cover'])

    print "created csv data with %s entries" % len(movies)
    return csv_data

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

def process_zip(file_name, output_dir):
    xml_file_name = "export.xml"
    xml_file_path = None
    try:
        zfobj = zipfile.ZipFile(file_name)
    except zipfile.BadZipfile:
        print "file is not a zip file"
        return

    if hashfile(file_name) == load_old_hash():
        print "not running, same hashes that means no update"
        return

    if xml_file_name not in zfobj.namelist():
        print "no %s found in zipfile" % xml_file_name
        return
    else:
        cover_count = 0
        for name in zfobj.namelist():
            try:
                uncompressed = zfobj.read(name)
            except Exception as e:
                print "Error opening Zip File: %s" % e
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

        print "found %s covers and xml %s" % (cover_count, xml_file_path)
        return xml_file_path

# main
if __name__ == '__main__':
    if len(sys.argv) > 1:
        try:
            output_dir = sys.argv[2]
        except IndexError:
            output_dir = "output/"
            pass

        # load data from zipfile
        xml_file_path = process_zip(sys.argv[1], output_dir)
        movies_dict = process_xml(xml_file_path)

        # render outputs
        if movies_dict:
            csv_data = create_csv(movies_dict)
            output = open(os.path.join(output_dir, "movies.csv"), 'wb')
            output.write(csv_data)
            output.close()

            html_data = create_html(movies_dict)
            output = open(os.path.join(output_dir, "index.html"), 'wb')
            output.write(html_data)
            output.close()

            # saving hash
            try:
                file = open(get_histfile(), 'w')
                file.write(hashfile(sys.argv[1]))
                file.close()
            except IOError:
                print("unable to save last hash to %s" % get_histfile())

    else:
        print "please add a filepath/name to movies.zip export file"