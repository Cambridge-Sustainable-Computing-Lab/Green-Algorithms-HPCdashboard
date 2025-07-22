#!/bin/bash
#
# Run this script to perform initial set-up.
#
echo "**************************"
echo "Performing intial set-up"
echo "**************************"

echo "Checking for miniforge (miniconda)..."
which conda | grep -E miniforge
if [ "$?" -eq "0" ]
then
	echo "Miniconda version OK"
else
	echo "Miniconda not found. Downloading miniconda..."
fi


