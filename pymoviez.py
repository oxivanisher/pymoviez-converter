#!/usr/bin/env python

import os
# import urllib
import sys
import os.path
import logging

from helper import *

logging.getLogger(__name__)

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

    logging.info("created html table with %s entries" % len(movies))
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

    logging.info("created csv data with %s entries" % len(movies))
    return csv_data

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
                logging.error("unable to save last hash to %s" % get_histfile())

    else:
        logging.error("please add a filepath/name to movies.zip export file")