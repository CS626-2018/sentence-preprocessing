#!/bin/bash

timestamp=$(date +%Y_%m_%d_%H%M%S)
if [ ! -d output ]; then
   mkdir output;
fi
if [ ! -d output ]; then
   mkdir output;
fi
for filename in $1/*.txt; do
    cat $filename | python3 mapper.py --local | sort | python3 reducer.py > output/output_$filename_$timestamp.txt
    echo $filename
done
