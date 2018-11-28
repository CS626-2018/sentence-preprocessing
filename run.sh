#!/bin/bash

timestamp=$(date +%Y_%m_%d_%H%M%S)
dir=output/job_$timestamp
if [ ! -d output ]; then
   mkdir output;
fi
if [ ! -d output ]; then
   mkdir output;
fi
mkdir $dir

input_dir=cs626/project/data/books_small
output_dir=cs626/project/output
hadoop_jar=/usr/lib/hadoop-mapreduce/hadoop-streaming-2.6.0-cdh5.13.0.jar

# Get number of text files in the input directory
file_num=$(hadoop fs -ls $input_dir/*.txt | wc -l)
echo "Pre-processing $file_num files."

# Execute the hadoop-streaming jar for mapreduce
hadoop jar $hadoop_jar \
	-libjars lib/sent-preproc-format.jar \
	-D mapred.reduce.tasks=$file_num \
	-file mapper.py \
	-mapper "/usr/local/bin/python3 mapper.py" \
	-file reducer.py \
	-reducer "/usr/local/bin/python3 reducer.py" \
	-file nltk.mod \
	-input $input_dir/* \
	-inputformat cs626.sentence.preprocessing.format.LineNumberInputFormat \
	-partitioner cs626.sentence.preprocessing.format.FilePartitioner \
	-output $output_dir
	#-partitioner org.apache.hadoop.mapred.lib.HashPartitioner \
hadoop fs -copyToLocal $output_dir/* $dir/
hadoop fs -rm -r $output_dir/
