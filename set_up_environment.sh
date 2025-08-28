#!/bin/bash
#
# Run this script as sudo to perform initial set-up:
# $ source ./set_up_environment.sh

# Name and path of this script
GA_SCRIPT="$0"
#GA_PATH="realpath $GA_SCRIPT"
echo "Script is $GA_SCRIPT"  #, path is $GA_PATH"
#exit 0

# We use this file to tell us if we are starting the script vs continuing after shell restart
#FILE="~/miniforge3_installed.txt"

# Download and install miniconda if we don't have it.
function get_miniconda() {

	# Miniforge conda
	#echo "Checking for miniforge (miniconda)..."
	#which conda | grep -E miniforge
	#if [ "$?" -eq "0" ]
	#then
        #	echo "Miniconda version OK"
	#	#touch "$FILE"
	#	return 0
	#fi

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

#    	chgrp -R anaconda /opt/miniforge3/
#    	chmod 770 -R /opt/miniforge3/

#    	/opt/miniforge3/bin/conda init bash

        # We need to close and re-open the shell for changes to take effect.
	# How to continue the script? -> touch/delete a file
#	touch "$FILE"

	#echo "Restarting shell to pick up changes..."
	#exec "$SHELL"
	#  . ~/.bashrc
}


function set_up_permissions() {
	#chgrp -R anaconda /opt/miniforge3/
        chmod 770 -R /opt/miniforge3/

        /opt/miniforge3/bin/conda init bash

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
		conda init bash
	fi
	conda init
	conda init bash
	source activate base
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
	for PKG in wget nano # postgresql git build-essential
	do
		echo "Downloading $PKG"
		apt-get install -y $PKG
	done
}


# This is the content that conda adds to ~/.bashrc. I'm having
# trouble getting it to reload the shell and pick up the
# changes made by installing conda. Perhaps this will 
# do the trick!
function mimic_shell_reload() {

	# >>> conda initialize >>>
	# !! Contents within this block are managed by 'conda init' !!
	__conda_setup="$('/opt/miniforge3/bin/conda' 'shell.bash' 'hook' 2> /dev/null)"
	if [ $? -eq 0 ]; then
    		eval "$__conda_setup"
	else
    		if [ -f "/opt/miniforge3/etc/profile.d/conda.sh" ]; then
        		. "/opt/miniforge3/etc/profile.d/conda.sh"
    		else
        		export PATH="/opt/miniforge3/bin:$PATH"
    		fi
	fi
	unset __conda_setup
	# <<< conda initialize <<<
}


# main function
#echo "**************************"
#echo "Performing intial set-up"
#echo "**************************"

# Are we continuing the script after a shell restart?
#if  [ ! -f "$FILE" ]  # No, we are not; this is first script invocation.

which conda | grep -E miniforge
if [ "$?" -ne "0" ]
then
	echo "** Conda not found. Downloading packages **"
	download_packages
	get_miniconda 
	#conda init
	#echo "Attempting to mimic restart of shell"
	mimic_shell_reload
	#export PATH="/opt/miniforge3/bin:$PATH"
	#source ~/.bashrc
	#conda init bash
fi

echo "*********************"
echo "I think we have conda?"
echo "*********************"

set_up_permissions

# We already checked for conda, and possibly restarted the shell
set_up_python_envt


