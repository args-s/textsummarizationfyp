import sys
import json
import os
import constants as const
import graphs
import textmanip
from nltk.stem.snowball import SnowballStemmer

stemmer = SnowballStemmer("english")


def make_summaries(file):
    # Gets 3 word, 6 word and 9-word summary of a document/graph
    print(file)
    print('Starting Summary of {}'.format(file))
    # Read in document
    doc = ""

    # Path to knowledge graph and text doc.
    graph_path = os.path.join(const.GRAPHS, file + '.dcorf.csv')
    print(graph_path)
    text_path = os.path.join(const.TEXT, file)
    print(text_path)

    if(os.path.exists(text_path)):
        print("Exists")
        with open(text_path, 'r', encoding='utf8') as x:
            doc = x.read()

    # Break up document into sentences
    sentences = textmanip.getSentences2(doc)

    # POS Tag Sentences
    pos_sentences = textmanip.partOfSpeech(doc)
    # print(pos_sentences)

    # Build Graph
    G = graphs.build_graph_from_csv(graph_path)

    # Three word summary
    top_triple = list(graphs.threeWordSummary(G))
    print('Key Terms: ', top_triple, '\n')

    # Get root forms of top triple options to search document
    top_triple_roots = list()
    for words in top_triple:
        new_roots = []
        for word in words:
            new_roots.append(stemmer.stem(word))
        top_triple_roots.append(new_roots)
    print("Top triple roots: ", top_triple_roots, '\n')

    summ_opts = list()
    # Check each sentence
    for sentence in sentences:
        sentence_root = ''
        # Get stemmed sentence
        for word in sentence:
            var = stemmer.stem(word)
            if(sentence_root == ' '):
                sentence_root = var
            else:
                sentence_root = sentence_root + " " + var
        #print("Sentence: ", sentence, '\n')
        # Check if stemmed sentence contains version of stemmed 3-word summary
        for n1, r, n2 in [(n1, r, n2) for n1 in top_triple_roots[0] for r in top_triple_roots[1] for n2 in top_triple_roots[2]]:
            # print(n1, r, n2)
            if(sentence_root.find(n1) != -1 and sentence_root.find(r) != -1 and sentence_root.find(n2) != -1):
                print("Adding sentence: ", sentence, '\n')
                summ_opts.append(sentence)
                break
    print("Sentences Matched: ", summ_opts)
    print()
    # Show sentences - Go through each sentence and combine into string. Print String
    for sentence in summ_opts:
        print_sent = ''
        for word in sentence:
            if(print_sent == ' '):
                print_sent = word
            else:
                print_sent = print_sent + " " + word
        print(print_sent, '\n')

# need a way to check if  sentence is already in the list or skip to the next setence when added


'''
    # Find sentence in raw document that contains words whose roots are the results of 3-word summary
    summ_options = []
    for s in sentences:
        score = 0
        sentstr = ''
        for word in s:
            # print(stemmer.stem(word))
            if ((stemmer.stem(word) == stemmer.stem(res3[0])) or (stemmer.stem(word) == stemmer.stem(res3[1])) or (stemmer.stem(word) == stemmer.stem(res3[2]))):
                score += 1

        if score > 2:
            sentstr = ' '.join(s)
            summ_options.append(sentstr)

    for s in range(len(summ_options)):
        print("\nSentence {}: {}\n".format(s+1, summ_options[s]))
        '''
