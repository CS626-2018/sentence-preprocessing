# Sentence Pre-processing
Hadoop MapReduce program to preprocess large amounts of text

`run.sh` assumes installation of Python 3 in the `/usr/local/bin/` directory.<br/>
The hadoop-streaming jar used in `run.sh` is the default jar for cloudera-quickstart VM 5.13.0 for VirtualBox.<br/>
The jar version is `hadoop-streaming-2.6.0-cdh5.13.0.jar` in the `/usr/lib/hadoop-mapreduce/` directory. Modify if necessary.

A jar with a custom TextInputFormat is included to run with the `run.sh` script.

`run.sh` requires the name of the input file within the `cs626/project/` HDFS directory as a parameter.<br/>
`run_local.sh` requires the path to the input file as a parameter.