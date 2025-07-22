#!/bin/bash
#
# Run this script as sudo to perform initial set-up.
#
echo "**************************"
echo "Performing intial set-up"
echo "**************************"

# TODO: install using apt here:
# wget,postgres,
# To install wget in Docker bash container: apt-get update && apt-get install -y wget 
# We assume they already have git installed as they will be cloning the repo.

# Miniforge conda
echo "Checking for miniforge (miniconda)..."
which conda | grep -E miniforge
if [ "$?" -eq "0" ]
then
	echo "Miniconda version OK"
else
	echo "Miniconda not found. Downloading miniconda..."

	cd /opt
	mkdir -p miniforge3
	# NB we should install wget first
	#wget "https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-$(uname)-$(uname -m).sh"  -O /opt/miniforge3/miniforge.sh
	#bash /opt/miniforge3/miniforge.sh -b -u -p /opt/miniforge3
	wget "https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-$(uname)-$(uname -m).sh"  -O ./miniforge3/miniforge.sh

	chgrp -R anaconda ./miniforge3/
	chmod 770 -R ./miniforge3/

	./miniforge3/bin/conda init

	# I think we need to close and re-open the shell. How to continue the script?
fi

# Install Python environment
echo
echo "Installing Python environment"
conda create -n py313 python=3.13 -c conda-forge
conda activate py313



