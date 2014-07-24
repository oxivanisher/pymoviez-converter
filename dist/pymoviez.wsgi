import os
import sys

os.environ['PYMOVIEZ_CFG'] = "/home/oxi/www_data/wsgi/pymoviez.cfg"

sys.path.insert(0, '/home/oxi/git_checkouts/pymoviez-converter/')

from pymoviezweb import app as application
