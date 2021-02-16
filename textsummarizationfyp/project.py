import sys
import json
import os
import constants as const
import graphs
import textmanip
from nltk.stem.snowball import SnowballStemmer

stemmer = SnowballStemmer("english")


def run():

    # Get Raw Text Document
    doc = ""
    path = os.path.join(const.TEXT, '1-s2.0-S0140673620303603-Abstract.txt')
    if(os.path.exists(path)):
        with open(path) as x:
            f = open(path, 'r')
            doc = f.read()

    # POS Tag Document
    pos = textmanip.partOfSpeech(doc)
    print("Building Graph \n")
    # Build Graph from csv
    G = graphs.build_graph_from_csv(os.path.join(const.GRAPHS,
                                                 '0a1f43c04e0e22fb6efbd94611920bc9680d7ae3.txt.dcorf.csv'))

    res = list(graphs.threeWordSummary(G))
    print("Result of 3 word summary: {}".format(res))
    # Get sentences
    sentences = textmanip.getSentences2(doc)

    # Find sentence in document that contains words whose roots are the results of 3-word summary
    summ_options = []
    for s in sentences:
        score = 0
        sentstr = ''
        for word in s:
            # print(stemmer.stem(word))
            if ((stemmer.stem(word) == stemmer.stem(res[0])) or (stemmer.stem(word) == stemmer.stem(res[1])) or (stemmer.stem(word) == stemmer.stem(res[2]))):
                score += 1

        if score > 2:
            sentstr = ' '.join(s)
            summ_options.append(sentstr)

    for s in range(len(summ_options)):
        print("Sentence {}: {}\n".format(s+1, summ_options[s]))
