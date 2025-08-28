#!/bin/bash
#
# Run this script as sudo to perform initial set-up.
#

# Name and path of this script
GA_SCRIPT="$0"
#GA_PATH="realpath $GA_SCRIPT"
echo "Script is $GA_SCRIPT"  #, path is $GA_PATH"
#exit 0

# We use this file to tell us if we are starting the script vs continuing after shell restart
FILE="~/miniforge3_installed.txt"

# Download and install miniconda if we don't have it.
function get_miniconda() {

	# Miniforge conda
	echo "Checking for miniforge (miniconda)..."
	which conda | grep -E miniforge
	if [ "$?" -eq "0" ]
	then
        	echo "Miniconda version OK"
		touch "$FILE"
		return 0
	fi

	echo "Miniconda not found. Downloading miniconda..."

	mkdir -p /opt/miniforge3
    	wget "https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-$(uname)-$(uname -m).sh"  -O /opt/miniforge3/miniforge.sh

	chmod +x /opt/miniforge3/miniforge.sh
	/opt/miniforge3/miniforge.sh -b -u -p /opt/miniforge3
	
	if  [ "$?" -ne "0" ]
        then
		echo "Permissions error. Please try running script again."
		exit 1
	fi

    	chgrp -R anaconda /opt/miniforge3/
    	chmod 770 -R /opt/miniforge3/

    	/opt/miniforge3/bin/conda init

        # We need to close and re-open the shell for changes to take effect.
	# How to continue the script? -> touch/delete a file
	touch "$FILE"

	echo "Restarting shell to pick up changes..."
	#exec "$SHELL"
	. ~/.bashrc
}


# Install Python environment
function set_up_python_envt() {
	echo

	echo "Checking for Python environment..."
	conda env list | grep py313
	if [ "$?" -ne "0" ]
	then
		echo "Installing Python environment"
		# Installs a conda environment at /opt/miniforge3/envs/py313.
		conda create -n py313 python=3.13 -c conda-forge
		conda init
	fi
	conda activate py313
}


# Download and install the packages we want, using apt-get
# NB Initial version uses basic Postgres, which should be OK if everything is
# on the same machine. Otherwise, if need TLS/SSL, ned to compile it.
function download_packages() {
	# To install wget in Docker bash container: apt-get update && apt-get install -y wget 
	# We assume they already have git installed as they will be cloning the repo.
	echo "Download packages with apt-get..."
	apt-get update # && apt-get install -y wget postgres git 
	# We loop over each package so we continue if a package fails to install.
	# It would be good if we could keep track of which ones don't get installed, and
	# tell the user at the end
	for PKG in wget postgresql git build-essential nano
	do
		echo "Downloading $PKG"
		apt-get install -y $PKG
	done
}


# main function
echo "**************************"
echo "Performing intial set-up"
echo "**************************"

# Are we continuing the script after a shell restart?
if  [ ! -f "$FILE" ]  # No, we are not; this is first script invocation.
then
	echo "** Before checking for conda **"
	download_packages
	get_miniconda # should create the file
	#echo "** 
	#exec "$SHELL" # $GA_SCRIPT"
fi

# We already checked for conda, and possibly restarted the shell
echo "** After checking for conda (and possible shell restart) **"
rm "$FILE"
set_up_python_envt

