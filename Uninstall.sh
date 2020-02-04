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
#
# THE SOFTWARE IS PRELIMINARY AND STILL IN TESTING AND VERIFICATION PHASE AND
# IS PROVIDED ON AN “AS IS” AND “AS AVAILABLE” BASIS AND IS BELIEVED TO CONTAIN DEFECTS.
# A PRIMARY PURPOSE OF THIS EARLY ACCESS IS TO OBTAIN FEEDBACK ON PERFORMANCE AND
# THE IDENTIFICATION OF DEFECT SOFTWARE, HARDWARE AND DOCUMENTATION.

function get_python_versions
{
    for P in $(whereis -b python | tr " " "\n" | grep "python[[:digit:]]\?\.\?[[:digit:]]\?\.\?[[:digit:]]\?$")
    do
        PYTHON=$P

        # 1) Remove results that are links
        if [ -L $PYTHON ]
        then
            continue
        fi

        # 2) Remove results that are directories
        if [ -d $PYTHON ]
        then
            continue
        fi

        # 3) Remove results that offer no pip support.
        $PYTHON -m pip > /dev/null 2>&1
        if [ $? -ne 0 ]
        then
            continue 
        fi

        # 4) Remove results there VimbaPython is not installed
        if [ $($PYTHON -m pip list | grep "VimbaPython" | wc -l) -ne 1 ]
        then
            continue
        fi

        echo -n "$PYTHON "
    done
}

echo "#################################"
echo "# VimbaPython uninstall script. #"
echo "#################################"

#########################
# Perform sanity checks #
#########################

if [ $UID -ne 0 ]
then
    echo "Error: Installation requires root privileges. Abort."
    exit 1
fi

PWD=$(pwd)
PWD=${PWD##*/}

if [[ "$PWD" != "VimbaPython" ]]
then
    echo "Error: Please execute Install.sh within VimbaPython directory."
    exit 1
fi

PYTHONS=$(get_python_versions)

if [ -z "$PYTHONS" ]
then
    echo "Can't remove VimbaPython. Is not installed."
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

    yes | $P -m pip uninstall VimbaPython

    if [ $? -eq 0 ]
    then
        echo "VimbaPython removal for $P was successful."
    else
        echo "Error: VimbaPython removal for $P failed. Please check pip output for details."
    fi
done
