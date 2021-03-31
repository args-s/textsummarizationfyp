import sys
import json
import os
import constants as const
import graphs
import textmanip
import itertools
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
    if(os.path.exists(os.path.join(const.doc_path, file))):
        text_path = os.path.join(const.doc_path, file)
        print(text_path)
    else:
        print("Text does not exist")
        sys.exit()

    # Build Graph
    G = graphs.build_graph_from_csv(graph_path)

    # Get top triple options
    top_triple = list(graphs.getTopTriple(G))
    print('Top Triple: ', top_triple, '\n')
    print(type(top_triple))

    # Get Key Sentences
    key_sentences = graphs.getKeySentences(file, top_triple)
    #print("Key Sentences: ", key_sentences, '\n')
    # print(type(key_sentences))

    # Get three word summary
    triple = graphs.threeWordSummary(G)
    print("Triple: ", triple, '\n')
    print(type(triple))
    # Print  possible summaries as string

    summaries = list()
    for comb in itertools.combinations(triple, 3):
        summary = ''
        for i in comb:
            if len(i) != 0:
                print(i[0])
                if summary == '':
                    summary = i[0]
                else:
                    summary = summary + " " + i[0]
        summaries.append(summary)
    print("Possible Summaries: ", summaries, '\n')

    write_path = os.path.join("C:\\Users\\killi\\Documents\\results_" + file)

    with open(write_path, 'w', encoding='utf8') as r:
        r.write("################# Results #################\n")
        r.write("Top Triple: \n [")
        for group in top_triple:
            for word in group:
                print(word)
        r.write(']\n')
        r.write("Three Word Summary:\n")
        r.write("Triple:\n")
        for group in triple:
            for word in group:
                r.write(word + " ")
        r.write('\n')
        r.write("Possible 3 words\n")
        for i in range(len(summaries)):
            r.write(summaries[i] + "\n")
        r.write("Simplified Key Sentences:\n")

        for sentence in key_sentences:

            r.write("Sentence:" + sentence + '\n')

        r.close()

        # TODO: Return dict of toptriple, key sentences, three word summary
