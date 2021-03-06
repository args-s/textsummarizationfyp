import csv
import sys
import os
import nltk
import networkx as nx
from nltk.corpus import words as nltkWords
# from pattern.text.en import singularize
import textsummarizationfyp.constants as const
from nltk.tokenize import word_tokenize
from nltk.corpus import wordnet as wn

global coalescing_completed

nltk.download('wordnet')
nltk.download('words')
skip_prepositions = True
temp_graph2 = nx.OrderedMultiDiGraph()
termSeparator = '_'
wn_lemmas = set(nltk.corpus.wordnet.all_lemma_names())
wnl = nltk.stem.WordNetLemmatizer()
mode = 'English'


def is_pronoun(wrd):
    return wrd in const.PRONOUNS


def is_noun(wrd):
    zz = wn.synsets(wrd, pos=wn.NOUN)
    return zz != []


def prepositionTest(word):
    prepList = ['of', 'for', 'at', 'on', 'as', 'by', 'in', 'to', 'from',
                'into', 'through', 'toward', 'with']
    return word in prepList


def is_proper_noun(wrd):
    return ((nltkWords.words().__contains__(wrd) == False)
            and (wn.synsets(wrd) == []))


def head_word(term):  # first word before term separator
    global termSeparator
    z = term.split(termSeparator)[0]
    return z


def contains_proper_noun(wrd):  # wrd may be a coreference chain
    global termSeparator
    for wo in wrd.split(termSeparator):
        if ((nltk.corpus.words.words().__contains__(wo) == False) and (nltk.corpus.wordnet.synsets(wo) == [])):
            return wo
    return False


def pre_existing_node(graph_name, inNoun):
    """ Merges inNoun into existing nodes from that graph - if applicable """
    if inNoun == "NOUN":  # skip any header information
        return inNoun
    global termSeparator
    global temp_graph2
    global wn_lemmas
    flag = False
    inNoun_head = head_word(inNoun)
    extendedNoun = inNoun
    in_propN = contains_proper_noun(inNoun)
    dud = temp_graph2.nodes()
    for graph_node in temp_graph2.nodes():
        if inNoun == graph_node:
            flag = False
            break
        elif in_propN != False:       # inNoun contains a PROPER noun
            if (in_propN == contains_proper_noun(graph_node)) and not(inNoun is graph_node):
                flag = True  # ProperNoun parts must be identical
                break
            # and not(is_pronoun(inNoun_head)):
            elif inNoun_head == head_word(graph_node) and not (inNoun == graph_node):
                flag = True                                             # same head, not pronoun!
                break
            # and not(is_pronoun(inNoun_head)):
            elif inNoun_head.lower() == head_word(graph_node).lower() and not (inNoun == graph_node):
                flag = True                                             # same head, not pronoun!
                break
        elif inNoun_head == head_word(graph_node) and (inNoun != graph_node)\
                and inNoun_head != False:  # identical head noun
            flag = True
            break
        elif inNoun_head.lower() == head_word(graph_node).lower() and (inNoun != graph_node) \
                and inNoun_head != False:  # identical head noun
            flag = True
            break
        else:
            # tmp = head_word(graph_node)
            # identicality previously tested
            if inNoun_head != False and head_word(graph_node) != False:
                a = wnl.lemmatize(inNoun_head)
                b = wnl.lemmatize(head_word(graph_node))
                if a == b:
                    flag = True
                    break
    if flag:
        if inNoun != graph_node:
            extendedNoun = extend_as_set(inNoun.split(termSeparator), graph_node.split(
                termSeparator))  # !!!!!!!!!!!!!!!!!!!!
            extendedNoun = reorganise_coref_chain(extendedNoun)
            if graph_node != extendedNoun:
                # print(inNoun,"+", graph_node, ">>", extendedNoun, end="     ")
                remapping = {graph_node: extendedNoun}
                graph_name = nx.relabel_nodes(
                    graph_name, remapping, copy=False)
                graph_name.nodes[extendedNoun]['label'] = extendedNoun
            else:
                # Add in to show fusion steps
                print(inNoun, ">", extendedNoun, end="     ")

    return extendedNoun


def returnEdgesAsList(G):  # returnEdgesAsList(sourceGraph)
    """ returns a list of lists, each composed of triples"""
    res = []
    for (u, v, reln) in G.edges.data('label'):
        res.append([u, reln, v])
    return res


def parse_new_coref_chain(in_chain):
    """Possibly using NLTK pos_tag """
    cnt = in_chain.find("_")
    if cnt <= 0:
        return in_chain
    if cnt <= 4:         # parser works poorly on short noun sequences
        return reorganise_coref_chain(in_chain)
    else:     # parse_coref_subsentence()
        noun_lis = []
        propN_lis = []
        pron_lis = []
        # "its_warlike_neighbor_Gagrach".split("_")
        chn = in_chain.split(termSeparator)
        strg2 = " ".join(chn)
        chn2 = nltk.pos_tag(word_tokenize(strg2))
        for (tokn, po) in chn2:
            if tokn in ['a', 'the', 'its']:  # remove problematic words from coref phrases
                continue
            elif is_pronoun(tokn) or po == "PRP":
                pron_lis.append(tokn)
            elif po == "NN" or is_noun(tokn):
                noun_lis.append(tokn)
            elif po == "NNP" or is_proper_noun(tokn):
                propN_lis.append(tokn)
        res = noun_lis + propN_lis + pron_lis
        slt = "_".join(res)
        return slt
    return "ERROR - parse_new_coref_chain() "


def final_pass_coalescing():
    global termSeparator
    global temp_graph2
    global coalescing_completed
    coalescing_completed = True
    # node_list = temp_graph2.nodes()
    node_list = list(temp_graph2)
    print("FPC", end=" ")
    zz = list(temp_graph2)
    # zzz = type(zz)
    flag = False
    for graph_node in zz:  # node_list:  # Final-pass Coalescing
        gn_pn = contains_proper_noun(graph_node)
        # limit = temp_graph2.nodes()
        # t1 = node_list.index(graph_node)
        # temp = node_list[1 + node_list.index(graph_node):]
        # subsequent nodes #in limit
        for g_node2 in node_list[1 + node_list.index(graph_node):]:
            gn_pn2 = contains_proper_noun(g_node2)
            # dummy_boole = graph_node is g_node2                      #Proper noun based merge
            if not(gn_pn == False) and (gn_pn == gn_pn2) and not(graph_node is g_node2):
                flag = True
                break
            elif head_word(graph_node) == head_word(g_node2) and not (graph_node is g_node2):
                flag = True
                break
        if flag and not (graph_node == g_node2):
            extendedNoun = extend_as_set(graph_node.split(termSeparator),
                                         g_node2.split(termSeparator))
            extendedNoun = reorganise_coref_chain(extendedNoun)
            # if extendedNoun == "there_some":
            #    print("dud")
            remapping = {g_node2: extendedNoun}
            print(" R2Map", graph_node, "+", g_node2, "->",
                  extendedNoun, graph_node == g_node2, end="--    ")
            temp_graph2 = nx.relabel_nodes(temp_graph2, remapping, copy=False)
            temp_graph2.nodes[extendedNoun]['label'] = extendedNoun

            flag = False
            coalescing_completed = False
            break
        # return
        # print("again", end=" ")
    return


def build_graph_from_csv(file_name):
    """ Includes eager concept fusion rules. Enforces  noun_properNoun_pronoun"""
    # print(" ...", end="")
    global temp_graph2
    global termSeparator
    
    full_path = os.path.join(
        const.GRAPHS, file_name)
    
    unknownCounter = 1
    with open(full_path, 'r') as csvfile:
        csvreader = csv.reader(csvfile, delimiter=',', quotechar='"')
        # temp_graph2 = nx.OrderedMultiDiGraph()
        temp_graph2.clear()
        temp_graph2.graph['Graphid'] = file_name
        try:
            last_s = last_v = last_o = ""
            for row in csvreader:
                if len(row) == 3:  # subject, verb, obj
                    noun1, verb, noun2 = row
                    noun1 = noun1.strip()
                    verb = verb.strip()
                    noun2 = noun2.strip()
                    if noun1.lower() == 'unknown':
                        noun1 = chr(ord('@') + unknownCounter) + \
                            "unknown"   # Unique proper nouns
                        unknownCounter += 1
                    elif noun2.lower() == 'unknown':
                        noun2 = chr(ord('@') + unknownCounter) + "unknown"
                        unknownCounter += 1
                    if (noun1 == last_s) and (noun2 == last_o) and prepositionTest(verb):
                        # and is_phrasal_verb(last_v + " " + verb)
                        phrasal_verb = last_v + "_" + verb
                        # print("+PP", phrasal_verb, end="  ")
                        temp_graph2.remove_edge(noun1, noun2)
                        temp_graph2.add_edge(noun1, noun2, label=phrasal_verb)
                        continue
                    elif noun1 == "NOUN":       # skip any header information
                        continue                # rest of the file contains prepositions
                    elif skip_prepositions and prepositionTest(verb):
                        continue

                    #  Coreference chains
                    noun1 = parse_new_coref_chain(noun1)
                    noun2 = parse_new_coref_chain(noun2)

                    noun1 = pre_existing_node(temp_graph2, noun1)
                    if not(noun1 in temp_graph2.nodes()):
                        temp_graph2.add_node(noun1, label=noun1)

                    noun2 = pre_existing_node(temp_graph2, noun2)
                    # what if NEW node2 should replace current version of node1 23-July
                    if head_word(noun1) == head_word(noun2):
                        noun1 = pre_existing_node(temp_graph2, noun1)

                    # VERB - Edge - Predicate

                    if not (noun2 in temp_graph2.nodes()):
                        temp_graph2.add_node(noun2, label=noun2)
                    temp_graph2.add_edge(noun1, noun2, label=verb)
                    # print(noun1, verb, noun2, end="   ")

                # Code Graphs
                elif mode == 'code' or len(row) == 6 or row[0:3] == "Type":
                    # print("Mode==code", end="")
                    # termSeparator = ":"
                    # if len(row) == 6:
                    #    b1, b2, methodName, noun1, verb, noun2 = row
                    if len(row) == 6:
                        methodName, noun1, verb, noun2, nr1, nr2 = row
                        noun1 = nr1 + ":" + noun1
                        noun2 = nr2 + ":" + noun2
                    elif len(row) == 3:
                        noun1, verb, noun2 = row
                    noun1 = noun1.strip()   # remove leading spaces
                    verb = verb.strip()
                    noun2 = noun2.strip()
                    # if(noun1.find(termSeparator) != -1):     #If a word contains an underscore, maps nodLis[0] to the first part of that word
                    # noun1 = noun1.split(termSeparator) #[0]
                    temp_graph2.add_node(noun1, label=noun1)
                    # if(noun2.find(termSeparator) != -1):     #If there is a word with an underscore, maps nodLis[0] to the first part of that word
                    # noun2 = noun2.split(termSeparator) # [0]
                    temp_graph2.add_node(noun2, label=noun2)
                    temp_graph2.add_edge(noun1, noun2, label=verb)
                    # print(noun1, verb, noun2, end="   ")
                if mode == 'English':
                    last_s = noun1
                    last_v = verb  # Used for phrasal verb identification "run_by"
                    last_o = noun2
        except csv.Error as e:
            sys.exit('file %s, line %d: %s' % (csvPath, csvreader.line_num, e))

    if mode == 'English':
        # print("Coalescing:\n", temp_graph2.nodes(), end="  ")
        global coalescing_completed
        coalescing_completed = False
        iteration_limit = temp_graph2.number_of_nodes()
        while not coalescing_completed and iteration_limit > 0:
            final_pass_coalescing()
            iteration_limit -= 1
            # print(iteration_limit, end=" ")
        # print("After coalescing:\n", temp_graph2.nodes(), end="  ")
    print("Returning graph!")
    return temp_graph2


def extend_as_set(l1, l2):
    result = []
    if len(l1) >= len(l2):
        result.extend(x for x in l1 if x not in result)
        donor = l2
    else:
        result.extend(x for x in l2 if x not in result)
        donor = l1
    result.extend(x for x in donor if x not in result)
    # resulting_list = list(result.union(donor))
    coref_terms = '_'.join(word for word in result)
    return reorganise_coref_chain(coref_terms)


def reorganise_coref_chain(strg):  # noun-propernoun-pronoun
    global termSeparator
    noun_lis = []
    propN_lis = []
    pron_lis = []
    if strg.find(termSeparator) < 0:
        slt = strg
    else:
        chan = strg.split(termSeparator)
        for tokn in chan:
            if tokn in ['a', 'the', 'its']:  # remove problematic words
                continue
            elif is_pronoun(tokn.lower()):
                pron_lis.append(tokn)
            elif is_noun(tokn):
                noun_lis.append(tokn)
            elif is_proper_noun(tokn):
                propN_lis.append(tokn)
        res = noun_lis + propN_lis + pron_lis
        slt = "_".join(res)
    return slt
