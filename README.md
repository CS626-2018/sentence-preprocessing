# Sentence Pre-processing
Hadoop MapReduce program to preprocess large amounts of text

## Installation
Simply clone this repo to get all the files you need. 

You will, however, need to install several libraries to use the Python scripts, as well as to use the scripts on HDFS.

### Required libraries:
- NLTK: `pip install nltk`
- punkt: `nltk.download('punkt')`
- vader_lexicon: `nltk.download('vader_lexicon')`

All NLTK pre-trained models that are downloaded need to be added to HDFS. NLTK looks in specific locations for these. Look at documentation for all locations. For this project we copied them to the directory `/home/nltk_data/` on HDFS. <br/>
For example, if `punkt` is located on your local machine at `/home/cloudera/nltk_data/tokenizers/punkt/english.pickle`, copy the `english.pickle` file (the pre-trained model) to HDFS at `/home/nltk_data/tokenizers/punkt/english.pickle`. Doing this allows Hadoop access to the pre-trained model while running the MapReduce Python scripts.

## Executing the program

`run.sh` assumes installation of Python 3 in the `/usr/local/bin/` directory.<br/>
The hadoop-streaming jar used in `run.sh` is the default jar for cloudera-quickstart VM 5.13.0 for VirtualBox.<br/>
The jar version is `hadoop-streaming-2.6.0-cdh5.13.0.jar` in the `/usr/lib/hadoop-mapreduce/` directory. Modify within `run.sh` if necessary.

A jar with a custom <em>TextInputFormat</em> is included to run with the `run.sh` script.<br/>
For the Java classes used within this jar, see its repository at [sentence-preprocessing-format](https://github.com/cs626-2018/sentence-preprocessing-format).

`run.sh` has the input and output directories as variables within the script. Modify if needed.<br/>
`run_local.sh` requires the path to the input directory as a parameter.

## Output

The output of this program will be in a single file, or many files, where each line will be:<br/>
`<filename>\t<sentence>\t<features>\t...`<br/>
Where `<filename>` is the original file the sentence belonged to, `<sentence>` is the actual sentence, and `<features>...` are the list of extracted features. Filename, sentence, and features will all be separated by tab (`\t`) characters.<br/>
All sentences will be outputted in the order they are found in the input file.

## Versions used

The following is a summary of the versions for all software used to test this program:
- Python 3.6.7
- NLTK 3.4