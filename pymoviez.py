
# import os
# import urllib
import hashlib
import sys
import zipfile
import os.path
import xml.etree.ElementTree as ET

# http://stackoverflow.com/questions/7806563/how-to-unzip-a-zip-file-with-python-2-4

def process_xml(xml_data):
    movies = []
    
    try:
        tree = ET.parse(xml_data)
    except Exception as e:
        print "unable to load xml data"
        return

    root = tree.getroot()
    count = 0
    for movie in root.iter("Movie"):
        medium_list = []
        genere_list = []
        loaned = ""
        loandate = ""
        country = ""
        cover = None
        title = None
        length = None
        url = None
        genere = None

        for attrib in movie.iter("*"):

            # print attrib.tag, attrib.text
            # Title, Cover, Medium, LoanDate
            if attrib.tag == "Title":
                count += 1
                title = attrib.text
            elif attrib.tag == "Cover":
                if attrib.text:
                    cover = attrib.text
            elif attrib.tag == "Medium":
                medium_list.append(attrib.text)
            elif attrib.tag == "Genre":
                if attrib.text:
                    genere_list.append(attrib.text)
            elif attrib.tag == "Country":
                if attrib.text:
                    country = attrib.text
            elif attrib.tag == "Year":
                year = int(attrib.text)
            elif attrib.tag == "Loaned":
                if attrib.text:
                    loaned = attrib.text
            elif attrib.tag == "LoanDate":
                loandate = attrib.text
            elif attrib.tag == "Length":
                length = attrib.text
            elif attrib.tag == "URL":
                if attrib.text:
                    url = attrib.text


        if cover:
            if os.path.isfile("output/" + cover):
                cover = cover

        if len(medium_list) > 0:
            medium = ", ".join(medium_list)
        else:
            medium = ""

        if len(genere_list) > 0:
            genere = ", ".join(genere_list)
        else:
            genere = ""

        if year < 10:
            year = ""

        if not length:
            length = ""
        elif "min" in length:
            pass
        elif length > 0:
            length = length + " min"

        if title:
            movies.append({ 'Title'    : title,
                            'Cover'    : cover,
                            'Medium'   : medium,
                            'Year'     : year,
                            'Genre'    : genere,
                            'URL'      : url,
                            'Loaned'   : loaned,
                            'Length'   : length,
                            'Country'  : country,
                            'LoanDate' : loandate })
    print "loaded %s sets of movie data" % (count)
    return movies

# create html output
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

def show_differences(movies_a, movies_b):
    # show_differences(movies_a, movies_b)
    movies_a_list = []
    movies_b_list = []

    for movie in sorted(movies_a.keys()):
        movies_a_list.append(movie)

    for movie in sorted(movies_b.keys()):
        movies_b_list.append(movie)

    for movie in movies_a_list:
        if movie not in movies_b_list:
            print "new movie %s" % movie
    for movie in movies_b_list:
        if movie not in movies_a_list:
            print "new movie %s" % movie

def read_zip(file_name):
    xml_file_name = None
    try:
        zfobj = zipfile.ZipFile(file_name)
    except zipfile.BadZipfile:
        print "file is not a zip file"
        return
        
    cover_count = 0

    for name in zfobj.namelist():
        uncompressed = zfobj.read(name)

        # save uncompressed data to disk
        outputFilename = "output/" + name
        output = open(outputFilename,'wb')
        output.write(uncompressed)
        output.close()
        if ".xml" not in name:
            cover_count += 1
        else:
            xml_file_name = outputFilename

    print "found %s covers and xml %s" % (cover_count, xml_file_name)
    return xml_file_name

if len(sys.argv) > 1:
    xml_file_name = read_zip(sys.argv[1])
    movies_dict = process_xml(xml_file_name)

    if movies_dict:
        csv_data = create_csv(movies_dict)
        output = open("output/movies.csv",'wb')
        output.write(csv_data)
        output.close()

        html_data = create_html(movies_dict)
        output = open("output/index.html",'wb')
        output.write(html_data)
        output.close()
else:
    print "please add a filepath/name"

# print html_data

# load xml files
# movies_a = process_xml("import/export_a.xml")
# movies_b = process_xml("import/export_b.xml")


# print html_data
