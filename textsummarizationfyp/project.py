import sys
import json
import os
import constants as const
import graphs
import textmanip


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

    # Build Graph from csv
    G = graphs.build_graph_from_csv(os.path.join(const.GRAPHS,
                                                 '1-s2.0-S0140673620303603-Abstract.txt.1c.nncoref.csv'))

    res = textmanip.breakupSummary(graphs.threeWordSummary(G))
    words = ''
    for x in res:
        words += x + ' '

    pos3 = textmanip.partOfSpeech(words)

    # Get sentences
    sents = textmanip.getSentences2(doc)

    # Search Doc for a sentence containing the words of 3 word summary
    summary = ""
    for sentence in sents:
        if (res[0] in sentence) and (res[1] in sentence) and (res[2] in sentence) and (res[3] in sentence):
            for x in range(len(sentence)):
                summary += x + ''

    print(summary)
    '''
    result=graphs.threeWordSummary(G)
    # Get sentence containing these words
    words=textmanip.breakupSummary(result)
    '''
