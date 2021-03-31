# Text Summariser

## Introduction
This project is the result of a final project created by Killian using existing
graph technology created by Diarmuid O'Donoghue.

The aim of this project is to create a system which can reliably create
human-like summaries of pieces of text. My aim is to utilise both Extractive
and Abstractive method of summarisation. Graphs are built using nodes and edges
parsed from text by SpaCy Parser.

## Python version
[Version 3.9.0](https://www.python.org/downloads/release/python-390/)

## Library Dependencies
See setup.py

## Configuration

### Activate virtual environment
Enter project folder
'''
source venv/bin/activate

## Build library
'''
 cd textsummarizationfyp/textsummarizationfyp
 python setup.py bdist_wheel
'''
### Install built library
'''
pip install path/to/project/root/dist/textsummarizationfyp-0.2-py3-none-any.whl
'''

## Module Descriptions
### summaries
#### make_summaries(text_file)
Creates top triple, finds key sentences, creates three word summaries and 
writes to a file in docs/summarys

#### getTopTriple(Grf)
Takes graphs built using build_grpah_from_csv(). Returns most important
triple as list.

#### getKeySentences(file, *top_triple=[])
Takes text file and top triple (Optional).
Returns key sentences from document. Method does require a graph to exist.
Calling method without text and graph folders present will cause method to fail.
top_triple is optional as it will generate one from the graph if it is not present.

### textmanip
#### convert
##### json_convert(json_path,text_path)
Converts json documents not in text_path.
