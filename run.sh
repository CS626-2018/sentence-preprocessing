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

input_dir=cs626/project/data/books_smallmed/
output_dir=cs626/project/output
hadoop_jar=/usr/lib/hadoop-mapreduce/hadoop-streaming-2.6.0-cdh5.13.0.jar
mapper=mapper.py
reducer=reducer.py

# Get number of text files in the input directory
file_num=$(hadoop fs -ls $input_dir/*.txt | wc -l)
echo "Pre-processing $file_num files."

# Previously used parameters
#-D mapred.reduce.tasks=$file_num \
#-partitioner cs626.sentence.preprocessing.format.FilePartitioner \
# Execute the hadoop-streaming jar for mapreduce
time hadoop jar $hadoop_jar \
	-Dmapred.text.key.comparator.options="-k1,1 -k2n" \
	-Dmapred.output.key.comparator.class=org.apache.hadoop.mapred.lib.KeyFieldBasedComparator \
	-Dstream.num.map.output.key.fields=3 \
	-libjars lib/sent-preproc-format.jar \
	-file $mapper \
	-mapper "/usr/local/bin/python3 $mapper" \
	-file $reducer \
	-reducer "/usr/local/bin/python3 $reducer" \
	-file nltk.mod \
	-input $input_dir/* \
	-inputformat cs626.sentence.preprocessing.format.LineNumberInputFormat \
	-output $output_dir
hadoop fs -copyToLocal $output_dir/* $dir/
hadoop fs -rm -r $output_dir/

