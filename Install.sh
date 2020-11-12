#!/usr/bin/env bash

# BSD 2-Clause License
#
# Copyright (c) 2019, Allied Vision Technologies GmbH
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

# global parameters parsed from command line flags 
DEBUG=false

while getopts "d" flag; do
  case "${flag}" in
    d) DEBUG=true ;;
    *) ;;
  esac
done

function get_bool_input()
{
    QUESTION=$1
    TRUTHY=$2
    FALSY=$3
    DEFAULT=$4
    ANSWER=""

    while [[ "$ANSWER" != "$TRUTHY" ]] && [[ "$ANSWER" != "$FALSY" ]]
    do
        echo -n "$QUESTION"
        read ANSWER

        # Use Default value if it was supplied and the input was empty.
        if [[ -z "$ANSWER" ]] && [[ ! -z "$DEFAULT" ]]
        then
            ANSWER=$DEFAULT
        fi

        # Print message if given input is invalid.
        if [[ "$ANSWER" != "$TRUTHY" ]] && [[ "$ANSWER" != "$FALSY" ]]
        then
            echo "  Error: Given Input must be either \"$TRUTHY\" or \"$FALSY\". Try again."
        fi
    done

    # Run test command to set return value for later evaluation.
    [[ "$ANSWER" == "$TRUTHY" ]]
}

function inside_virtual_env
{
    if [ -z "$VIRTUAL_ENV" ]; then
        echo "false"
    else
        echo "true"
    fi
}

function get_python_versions
{
    DETECTED_PYTHONS=()

    # Check if the script was run from a virtual environment and set search path for binary accordingly
    if [ "$(inside_virtual_env)" = true ]; then
        if [ "$DEBUG" = true ] ; then
            echo "Detected active virtual environment" >&2
        fi
        SEARCH_PATH="$VIRTUAL_ENV"/bin
    else
        if [ "$DEBUG" = true ] ; then
            echo "No virtual environment detected" >&2
        fi
        SEARCH_PATH=$(echo "$PATH" | tr ":" " ")
    fi

    if [ "$DEBUG" = true ] ; then
        echo "Searching for python in $SEARCH_PATH" >&2
    fi

    # iterate over all detected python binaries and check if they are viable installations
    for P in $(whereis -b -B $SEARCH_PATH -f python | tr " " "\n" | grep "python[[:digit:]]\.[[:digit:]]\.\?[[:digit:]]\?$" | sort -V)
    do
        # 1) Remove results that are links (venv executables are often links so we allow those)
        if [ -L "$P" ] && [ "$(inside_virtual_env)" = false ]
        then
            if [ "$DEBUG" = true ] ; then
                echo "$P was a link" >&2
            fi
            continue
        fi

        # 2) Remove results that are directories
        if [ -d "$P" ]
        then
            if [ "$DEBUG" = true ] ; then
                echo "$P was a directory" >&2
            fi
            continue
        fi

        # 3) Remove incompatible versions (<3.7)
        # patch is ignored but has to be parsed in case the binary name contains it
        FILENAME=$(basename -- "$P")
        read -r MAJOR MINOR PATCH < <(echo $FILENAME | tr -dc "0-9." | tr "." " ")
        if [ $MAJOR -gt 3 ] || { [ $MAJOR -eq 3 ] && [ $MINOR -ge 7 ]; }; then
            : # the interperter is compatible
        else
            if [ "$DEBUG" = true ] ; then
                echo "$P is not compatible. VimbaPython requires python >=3.7" >&2
            fi
            continue
        fi

        # 4) Remove results that offer no pip support.
        $P -m pip > /dev/null 2>&1
        if [ $? -ne 0 ]
        then
            if [ "$DEBUG" = true ] ; then
                echo "$P did not have pip support" >&2
            fi
            continue 
        fi
        DETECTED_PYTHONS+=("$P")
    done
    echo "${DETECTED_PYTHONS[@]}"
}

echo "###############################"
echo "# VimbaPython install script. #"
echo "###############################"

#########################
# Perform sanity checks #
#########################

# root is only required if we are not installing in a virtual environment
if [ $UID -ne 0 ] && [ "$(inside_virtual_env)" = false ]
then
    echo "Error: Installation requires root priviliges. Abort."
    exit 1
fi

PWD=$(pwd)
PWD=${PWD##*/}

if [[ "$PWD" != "VimbaPython" ]]
then
    echo "Error: Please execute Install.sh within VimbaPython directory."
    exit 1
fi

# get path to setup.py file
SOURCEDIR="$(find . -name setup.py -type f -printf '%h' -quit)"
if [ -z "$SOURCEDIR" ]
then
    echo "Error: setup.py not found. Abort"
    exit 1
fi

PYTHONS=$(get_python_versions)

if [ -z "$PYTHONS" ]
then
    echo "Error: No compatible Python version with pip support found. Abort."
    exit 1
fi


#################################################
# Determine python installation for VimbaPython #
#################################################

# List all given interpreters and create an Index
echo "The following Python versions with pip support were detected:"

ITER=0

for ITEM in ${PYTHONS[@]}
do  
    echo "  $ITER: $ITEM"
    LAST=$ITER
    ITER=$(expr $ITER + 1)
done

# Read and verfiy user input
while true
do
    echo -n "Enter python version to install VimbaPython (0 - $LAST, default: 0): "
    read TMP

    if [ -z "$TMP" ]
    then
        TMP=0
    fi

    # Check if Input was a number. If so: assign it.
    if [ $TMP -eq $TMP ] 2>/dev/null
    then
        ITER=$TMP
    else
        echo "  Error: Given input was not a number. Try again."
        continue
    fi

    # Verify Input range
    if [ 0 -le $ITER ] && [ $ITER -le $LAST ]
    then
        break

    else
        echo "  Error: Given input is not between 0 and $LAST. Try again."
    fi
done

# Search for selected python interpreter
IDX=0
PYTHON=""

for ITEM in ${PYTHONS[@]}
do  
    if [ $IDX -eq $ITER ]
    then
        PYTHON=$ITEM
        break
    else
        IDX=$(expr $IDX + 1)
    fi
done

echo "Installing VimbaPython for $PYTHON"
echo ""

##################################################
# Determine installation targets from user input #
##################################################
TARGET=""

# Ask for numpy support
get_bool_input "Install VimbaPython with numpy support (yes/no, default: yes):" "yes" "no" "yes"
if [ $? -eq 0 ]
then
    TARGET="numpy-export"
    echo "Installing VimbaPython with numpy support."
else
    echo "Installing VimbaPython without numpy support."
fi
echo ""

# Ask for OpenCV support
get_bool_input "Install VimbaPython with OpenCV support (yes/no, default: yes):" "yes" "no" "yes"
if [ $? -eq 0 ]
then
    if [ -z $TARGET ]
    then
        TARGET="opencv-export"
    else
        TARGET="$TARGET,opencv-export"
    fi
    echo "Installing VimbaPython with OpenCV support."
else
    echo "Installing VimbaPython without OpenCV support."
fi
echo ""

# Execute installation via pip
if [ -z $TARGET ]
then
    TARGET="$SOURCEDIR"
else
    TARGET="$SOURCEDIR[$TARGET]"
fi

$PYTHON -m pip install "$TARGET"

if [ $? -eq 0 ]
then
    echo "VimbaPython installation successful."
else
    echo "Error: VimbaPython installation failed. Please check pip output for details."
fi
