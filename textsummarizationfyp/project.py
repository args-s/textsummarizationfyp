import sys
import json
import os
import constants as const
import graphs
import textmanip
from nltk.stem.snowball import SnowballStemmer

stemmer = SnowballStemmer("english")


def make_summaries(file):
    # Gets 3 word, show key sentences, simplfy key sentence
    print(file)
    print('Starting Summary of {}'.format(file))
    # Read in document
    doc = ""
    # Check for knowledge graph
    if(os.path.exists(os.path.join(const.GRAPHS, file + '.dcorf.csv'))):
        graph_path = os.path.join(const.GRAPHS, file + '.dcorf.csv')
        print(graph_path)
    else:
        print("ERROR: Graph does not exist.")
        sys.exit()

    # Check for text file specified
    if(os.path.exists(os.path.join(const.TEXT, file))):
        text_path = os.path.join(const.TEXT, file)
        print(text_path)
    else:
        print("Text does not exist")
        sys.exit()

    # Build Graph
    G = graphs.build_graph_from_csv(graph_path)

    # Get top triple options
    top_triple = list(graphs.getTopTriple(G))
    print('Key Terms: ', top_triple, '\n')

    key_sentences = graphs.getKeySentences(file, top_triple)
    print("Key Sentences: ", key_sentences, '\n')

    triple = graphs.threeWordSummary(G)
    print("Result of 3 word summary: ", triple, '\n')
