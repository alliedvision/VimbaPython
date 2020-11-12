#!/bin/bash

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

        # 3) Remove results that offer no pip support.
        $P -m pip > /dev/null 2>&1
        if [ $? -ne 0 ]
        then
            if [ "$DEBUG" = true ] ; then
                echo "$P did not have pip support" >&2
            fi
            continue 
        fi

        # 4) Remove results where VimbaPython is not installed
        if [ $($P -m pip list --format=columns | grep "VimbaPython" | wc -l) -ne 1 ]
        then
            if [ "$DEBUG" = true ] ; then
                echo "$P did not have VimbaPython installed" >&2
            fi
            continue
        fi
        DETECTED_PYTHONS+=("$P")
    done
    echo "${DETECTED_PYTHONS[@]}"
}
echo "#################################"
echo "# VimbaPython uninstall script. #"
echo "#################################"

#########################
# Perform sanity checks #
#########################

if [ $UID -ne 0 ] && [ "$(inside_virtual_env)" = false ]
then
    echo "Error: Uninstallation requires root privileges. Abort."
    exit 1
fi

PWD=$(pwd)
PWD=${PWD##*/}

if [[ "$PWD" != "VimbaPython" ]]
then
    echo "Error: Please execute Uninstall.sh within VimbaPython directory."
    exit 1
fi

PYTHONS=$(get_python_versions)

if [ -z "$PYTHONS" ]
then
    echo "Can't remove VimbaPython. No installation was found."
    exit 0
fi

#############################################
# Determine python to uninstall VimbaPython #
#############################################

# List all given interpreters and create an Index
echo "VimbaPython is installed for the following interpreters:"

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
    echo -n "Enter python version to uninstall VimbaPython (0 - $LAST, all: a, default: a): "
    read TMP

    # Set TMP to default value if nothing was entered.
    if [ -z $TMP ]
    then
        TMP="a"
    fi

    # Check if Input was "a". If so skip further Input verification.
    if [ "$TMP" == "a" ]
    then
        echo "  Removing all installations of VimbaPython."
        ITER=$TMP
        break

    else
        # Check if Input was a number. If so: assign it.
        if [ $TMP -eq $TMP ] 2>/dev/null
        then
            ITER=$TMP

        else
            echo "  Error: Given input was not a number. Try again."
            continue
        fi
    
        # Verify Input range
        if [ 0 -le $ITER -a $ITER -le $LAST ]
        then
            break

        else
            echo "  Error: Given input is not between 0 and $LAST. Try again."
        fi
    fi
done

# Search for selected python interpreter
IDX=0
PYTHON=""

for ITEM in ${PYTHONS[@]}
do  
    if [ "$ITER" == "a" ]
    then
        PYTHON=$PYTHONS
        break

    elif [ $IDX -eq $ITER ]
    then
        PYTHON=$ITEM
        break
    else
        IDX=$(expr $IDX + 1)
    fi
done


# Remove VimbaPython via pip
for P in ${PYTHON[@]}
do
    echo ""
    echo "Remove VimbaPython for $P"

    $P -m pip uninstall --yes VimbaPython

    if [ $? -eq 0 ]
    then
        echo "VimbaPython removal for $P was successful."
    else
        echo "Error: VimbaPython removal for $P failed. Please check pip output for details."
    fi
done
