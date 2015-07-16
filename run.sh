#!/bin/bash

# Getting script directory.
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Saving origin path.
ORIGDIR=$(pwd)

# Cleaning old .pyc files to not run into the "importing seems to work" trap again!
find ${DIR} -name "*.pyc" -exec rm {} \;

# Changing to the root path of th application.
cd ${DIR}

# Checking if PYMOVIEZ_CFG is set. If not, use the provided example file.
if [ -z "$PYMOVIEZ_CFG" ]; then
	if [ -f "dist/pymoviez.cfg" ]; then
		echo "Setting PYMOVIEZ_CFG for you. Please use your own settings for production!"
		export PYMOVIEZ_CFG="dist/pymoviez.cfg"
	else
		export PYMOVIEZ_CFG="dist/pymoviez.cfg.example"
	fi
fi

# Actually starting the application.
python pymoviezweb.py

# Changing back to origin path.
cd ${ORIGDIR}