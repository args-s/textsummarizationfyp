import sys
import json
import os
import nltk
import textsummarizationfyp.constants as const
import textsummarizationfyp.textmanip
from textsummarizationfyp.textmanip.text import getSentences
import itertools
from nltk.stem.snowball import SnowballStemmer
from textsummarizationfyp.graphs import build_graph_from_csv, returnEdgesAsList
from nltk.corpus import wordnet as wn
import networkx as nx
from networkx.algorithms import tree

nltk.download('stopwords')
stop_words = set(nltk.corpus.stopwords.words('english'))
termSeparator = '_'
stemmer = SnowballStemmer("english")

# For POS Tag
nltk.download('punkt')
nltk.download('averaged_perceptron_tagger')

def getTopTriple(Grf):
    simplifiedGraf = nx.Graph(Grf)  # simplify to NON-Multi - Graph
    
    mst = tree.minimum_spanning_edges(
        simplifiedGraf, algorithm="kruskal", data=False)
    print(mst, '\n')
    edgelist = list(mst)
    # print("EdgeList:", edgelist, '\n')

    # PageRank  WEIGHT = Count Edges
    pr = nx.pagerank(simplifiedGraf, alpha=0.8)
    # print("pr:", pr, '\n')
    predsList = returnEdgesAsList(Grf)
    # print("predsList: ", predsList, '\n')
    predsList2 = []
    for (n1, n2) in edgelist:
        for [n3, r, n4] in predsList:
            if (n1 == n3 and n2 == n4) or (n1 == n4 and n2 == n3):
                scor = pr[n1] * pr[n2]
                predsList2.append([scor, n1, r, n2])
                break
    # Sort with highest pr score first
    predsList2.sort(key=lambda x: x[0], reverse=True)
    # print("predsList2: ", predsList2, '\n')
    # print()
    # print("Show Slicing: ", predsList2[0:5], '\n')
    '''
    for [scor, n1, r, n2] in predsList2[0:5]:
        print(n1, r, n2, end="   ")
        # Remove stop words entries?
    '''
    top_triple = predsList2[0]
    print('Top Triple: ', top_triple, '\n')

    # Split options for each word of summary into sets and remove duplicates
    n1 = list(set(top_triple[1].split(termSeparator)))
    # print("N1: ", n1, '\n')
    r = list(set(top_triple[2].split(termSeparator)))
    # print("r: ", r, '\n')
    n2 = list(set(top_triple[3].split(termSeparator)))
    # print("N2: ", n2, '\n')
    # print("Top triple: ", n1, r, n2, '\n')
    return(n1, r, n2)


def threeWordSummary(Grf):
    # Get top triple options
    top_triple = getTopTriple(Grf)
    print('Top Triple from 3word: ', top_triple, '\n')

    # Remove stop words
    filtered_triple = list()
    for group in top_triple:
        filtered_group = []
        for word in group:
            # Remove stop words and words outside wordnet
            if ((word not in stop_words) and (wn.synsets(word) != [])):
                filtered_group.append(word)
        filtered_triple.append(filtered_group)
        # print(filtered_group)
    print(filtered_triple)

    final_triple = []
    for group in filtered_triple:
        # If single word not found
        print("Now on: ", group, '\n')
        if(len(group) > 1):
            print(group, " has more than one element.\n")
            # Sort words in group according to how abstract they are
            group.sort(key=howAbstract, reverse=True)
            print("Sorted for abstraction: ", group)
            new_group = list()
            # Go through each unique pair combination of words
            for a, b in itertools.combinations(group, 2):
                synonyms = set()
                print("Checking words: ", a, b)
                # Get synonyms of a in group
                for syn in wn.synsets(a):
                    for l in syn.lemmas():
                        synonyms.add(l.name())
                # If b is a synonym of a, merge these using the average word
                print("Synonyms for", a, ": ", synonyms, '\n')
                if b in synonyms:
                    print("Merging synonyms: ", a, b, '\n')
                    # Add string version of word
                    new_group.append(wn.synsets(
                        a)[0].lowest_common_hypernyms(wn.synsets(b)[0])[0].lemmas()[0].name())
                # Get new list of merged words. Replace group with new group
            final_triple.append(new_group)
        else:
            final_triple.append(group)

    # print("Final Triple: ", final_triple)
    return(final_triple)


def howAbstract(word):
    # Get minimum distance to root form of a word
    print(word, min([len(path)
                     for path in wn.synsets(word)[0].hypernym_paths()]))
    return(min([len(path) for path in wn.synsets(word)[0].hypernym_paths()]))


def getKeySentences(file, top_triple=[]):
    remove_tags = ['RB', 'JJ', '\'\'', 'POS',
                   'JJ', 'IN', 'TO', 'WP', 'PRP', 'DT']
    # Given file and optional top_triple, return key sentences of a text document
    if(top_triple == []):
        print("No top triples given. I'll get those")
        # If being used as standalone function, get build graph to get top triple
        G = build_graph_from_csv(os.path.join(
            const.GRAPHS, file + '.dcorf.csv'))
        top_triple = getTopTriple(G)

    sentences = getSentences(file)

    # Get root forms of top triple options to search document
    top_triple_roots = list()
    for words in top_triple:
        new_roots = []
        for word in words:
            new_roots.append(stemmer.stem(word))
        top_triple_roots.append(new_roots)
    # print("Top triple roots: ", top_triple_roots, '\n')

    summ_opts = list()
    # Check each sentence for key words
    for sentence in sentences:
        sentence_root = ''
        # Get stemmed sentence
        for word in sentence:
            var = stemmer.stem(word)
            if(sentence_root == ' '):
                sentence_root = var
            else:
                sentence_root = sentence_root + " " + var
        # print("Sentence: ", sentence, '\n')
        # Check if stemmed sentence contains version of stemmed 3-word summary
        for n1, r, n2 in [(n1, r, n2) for n1 in top_triple_roots[0] for r in top_triple_roots[1] for n2 in top_triple_roots[2]]:
            # print(n1, r, n2)
            if(sentence_root.find(n1) != -1 and sentence_root.find(r) != -1 and sentence_root.find(n2) != -1):
                # print("Adding sentence: ", sentence, '\n')
                summ_opts.append(sentence)
                break

    # summ_opts = list of key sentences
    # POS tag each sentence
    for sentence in summ_opts:
        summ_opts = [nltk.pos_tag(sentence) if i ==
                     sentence else i for i in summ_opts]

    all_sents = []
    for sentence in summ_opts:
        sentence_str = ''
        for word in sentence:
            # If word not in stop words or tagged with removable tag add to sentence
            if(not((word[0] in stop_words) or (word[1] in remove_tags))):
                if(sentence_str == ''):
                    sentence_str = word[0]
                else:
                    sentence_str = sentence_str + " " + word[0]
        all_sents.append(sentence_str)
    return(all_sents)


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
    G = build_graph_from_csv(graph_path)

    # Get top triple options
    top_triple = list(getTopTriple(G))
    print('Top Triple: ', top_triple, '\n')
    print(type(top_triple))

    # Get Key Sentences
    key_sentences = getKeySentences(file, top_triple)
    #print("Key Sentences: ", key_sentences, '\n')
    # print(type(key_sentences))

    # Get three word summary
    triple = threeWordSummary(G)
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

    write_path = os.path.join(const.summarys, file)

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
