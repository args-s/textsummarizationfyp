import networkx as nx
import isomorphvf2CB       #VF2 Modified
#from networkx.algorithms import isomorphism as isomorphvf2CB
#import DFS #my personal DFS based graph matching
#from networkx.algorithms import isomorphism
import VF3 as VF3
#import ConceptNetElaboration as CN
import csv, sys
import pprint
import numpy as np
import matplotlib.pyplot as plt
import pylab
import os
import webbrowser
import json
#from functools import reduce
#import operator
#import subprocess
from nltk.corpus import wordnet_ic
from nltk.corpus import wordnet as wn
from nltk.corpus import words as nltkWords
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize
from nltk.corpus import wordnet
import nltk
from itertools import product
from cacheout import Cache
import time
import requests
import re
import math
from tkinter import *
from itertools import count
import numpy 

from multiprocessing import Process, Queue, Manager


########################################################
############### Global Variables ######################
########################################################

# nx.OrderedMultiMultiDiGraph()  #loosely-ordered, mostly-directed, somewhat-multiGraph, self-loops, parallel edges

run_Limit = 500           # 5 # Stop after this many texts
skip_prepositions = True #False
#skip_prepositions = False
filetypeFilter = '.csv'  #'txt.S.csv'


basePath = "C:/Users/dodonoghue/Documents/Python-Me/data"
#basePath = dir_path = os.path.dirname(os.path.realpath(__file__)).replace('\\','/')
global localBranch

mode = 'English'
mode = 'code'
if mode == 'code':
    termSeparator = ":"  # "_"  hawk_he OR Block:Else: If
    localBranch = "/c-sharp-id-num/"
    # localBranch = "/C-Sharp Data/"
    # localBranch = "/Java Data/"
    # localBranch = "/TS1-TS4/"
else:
    mode == 'English'
    termSeparator = "_"
    # "test/" #Text2ROS.localBranch #""
    #localBranch = "/test/"  # "test/" #Text2ROS.localBranch #""
    # localBranch = "/iProva/"
    # localBranch = "/Covid-19/"
    # localBranch = "/Psychology Data/"
    # localBranch = "/MisTranslation Data/"

global coalescing_completed
global max_graph_size

max_graph_size = 300  # see prune_peripheral_nodes(graph)

targetGraph = nx.MultiDiGraph()  # <- targetFile
sourceGraph = nx.MultiDiGraph()  # <- sourceFile
temp_graph2 = nx.OrderedMultiDiGraph()  # create ordered graphs. Subsequently treat as unordered.

numberOfTimeOuts = 0
inferenceList = []
LCSLlist = []
mappedpairs = []
listOfSources = []
relationMapping = {}
#predicatePairs=[]
WN_cache = {}
CN_dict = {}

#semcor_ic = wordnet_ic.ic('ic-semcor.dat')
brown_ic = wordnet_ic.ic('ic-brown.dat')
vbse = 0  # VerBoSE mode for error reporting and tracing
wnl = WordNetLemmatizer()
wn_lemmas = set(wordnet.all_lemma_names())
pp = pprint.PrettyPrinter(indent=4)

########################################################
############## File Infrastructure #####################
########################################################


localPath = basePath + localBranch
htmlBranch = basePath + localBranch + "FDG/"

CN_file = basePath + "/ConceptNetdata.csv"

CSVPath = localPath + "CSVOutput/"  #Where you want the CSV file to be produced
CachePath = basePath + localBranch+ "/Cache.txt" #Where you saved the Cache txt file
CSVsummaryFileName = CSVPath + "summary.csv"
# Global csvSummaryFileHandle 
analogyFileName = CSVPath + "something.csv"
mapped_predicates = []

print("INPUT:", localPath)
print("OUTPUT:", CSVPath)

sourceFiles = os.listdir(localPath)
#all_csv_files = [i for i in sourceFiles if i.endswith('txt.S.csv')] # if ("code" in i) and (i.endswith('.csv'))]
all_csv_files = [i for i in sourceFiles if i.endswith(filetypeFilter)] 
print("CSV input files: ", all_csv_files)
print("Mode=", mode, "  Term Separator=", termSeparator)

commutativeVerbList = ['and', 'beside', 'near']  # x and y  ==>  y and x

# pronouns and pronomial adjectives
pronoun_list = ["all", "another", "any", "anybody", "anyone", "anything", "as", "aught", "both", "each",
                "each other", "either", "enough", "everybody", "everyone", "everything", "few", "he", "her",
                "hers", "herself", "him", "himself", "his", "I", "idem", "it", "its", "itself", "many", "me ",
                " mine", "most", "my", "myself", "naught", "neither", "no one", "nobody", "none", "nothing",
                "nought", "one", "one another", "other", "others", "ought", "our", "ours", "ourself",
                "ourselves", "several", "she", "some", "somebody", "someone", "something", "somewhat",
                "such", "suchlike", "that", "thee", "their", "theirs", "theirself", "theirselves", "them",
                "themself", "themselves", "there", "these", "they", "thine", "this", "those", "thou", "thy",
                "thyself", "us", "we ", " what", "whatever", "whatnot", "whatsoever", "whence", "where",
                "whereby", "wherefrom", "wherein", "whereinto", "whereof", "whereon", "wherever", "wheresoever",
                "whereto", "whereunto", "wherewith", "wherewithal", "whether", "which", "whichever",
                "whichsoever", "who", "whoever", "whom", "whomever", "whomso", "whomsoever", "whose",
                "whosever", "whosesoever", "whoso", "whosoever", "ye", "yon", "yonder", "you", "your", "yours",
                "yourself", "yourselves"]


def prepositionTest(word):
    prepList = ['of', 'for', 'at', 'on', 'as', 'by', 'in', 'to', 'from',
                'into', 'through', 'toward', 'with']
    return word in prepList 

# #################################################################################################################
# ##################################### Process Input #############################################################
# #################################################################################################################

def extend_as_set(l1,l2):
    result = []
    if len(l1) >= len(l2):
        result.extend(x for x in l1 if x not in result)
        donor = l2
    else:
        result.extend(x for x in l2 if x not in result)
        donor = l1
    result.extend(x for x in donor if x not in result)
    #resulting_list = list(result.union(donor))
    coref_terms = '_'.join(word for word in result)
    return reorganise_coref_chain(coref_terms)
#extend_as_set(['hawk', 'she'], ['hawk', 'it'])
#extend_as_set(['hunter', 'He'], ['hunter', 'he', 'him'])


def merge_concept_chains(c1, c2): #simple set merge
    global termSeparator
    c1 = c1.strip().split(termSeparator)
    c2 = c2.strip().split(termSeparator)
    if len(c1) >= len(c2):
        res = set(c1 + c2)
    else:
        res = set(c2 + c1)
    return reorganise_coref_chain(res)


def graph_contains_proper_noun(propNoun1):
    global temp_graph2
    flag = False
    zzz = propNoun1
    pred_list = temp_graph2.nodes()  
    for subj in pred_list:
        for wrd in subj.split(termSeparator):
            if propNoun1 == wrd:
                zzz = subj
    return zzz


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
            if (in_propN == contains_proper_noun(graph_node)) and not(inNoun is graph_node): #
                flag = True                       #ProperNoun parts must be identical
                break
            elif inNoun_head == head_word(graph_node) and not (inNoun == graph_node):# and not(is_pronoun(inNoun_head)):
                flag = True                                             # same head, not pronoun!
                break
            elif inNoun_head.lower() == head_word(graph_node).lower() and not (inNoun == graph_node):# and not(is_pronoun(inNoun_head)):
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
            #tmp = head_word(graph_node)
            if inNoun_head != False and head_word(graph_node) != False: # identicality previously tested
                a= wnl.lemmatize(inNoun_head)
                b = wnl.lemmatize(head_word(graph_node))
                if a == b:
                    flag = True
                    break
    if flag:
        if inNoun != graph_node:
            extendedNoun = extend_as_set(inNoun.split(termSeparator), graph_node.split(termSeparator)) #!!!!!!!!!!!!!!!!!!!!
            extendedNoun = reorganise_coref_chain(extendedNoun)
            if graph_node != extendedNoun:
                #print(inNoun,"+", graph_node, ">>", extendedNoun, end="     ")
                remapping = {graph_node: extendedNoun}
                graph_name = nx.relabel_nodes(graph_name, remapping, copy=False)
                graph_name.nodes[extendedNoun]['label'] = extendedNoun
            else:
                print(inNoun, ">", extendedNoun, end="     ")
    return extendedNoun



def build_graph_from_csv(file_name):
    """ Includes eager concept fusion rules. Enforces  noun_properNoun_pronoun"""
    #print(" ...", end="")
    global temp_graph2
    global termSeparator
    fullPath = localPath + file_name
    unknownCounter = 1
    with open(fullPath, 'r') as csvfile:
        csvreader = csv.reader(csvfile, delimiter=',', quotechar='"')
        #temp_graph2 = nx.OrderedMultiDiGraph()
        temp_graph2.clear()
        temp_graph2.graph['Graphid'] = file_name
        try:
           last_s = last_v = last_o = ""
           for row in csvreader:
                if len(row) == 3:    #subject, verb, obj
                    noun1, verb, noun2 = row
                    noun1 = noun1.strip()
                    verb = verb.strip()
                    noun2 = noun2.strip()
                    if noun1.lower() == 'unknown':
                        noun1 = chr(ord('@')+ unknownCounter) + "unknown"   # Unique proper nouns
                        unknownCounter += 1
                    elif noun2.lower() == 'unknown':
                        noun2 = chr(ord('@')+ unknownCounter) + "unknown"
                        unknownCounter += 1

                    if (noun1 == last_s) and (noun2 == last_o) and prepositionTest(verb):
                        # and is_phrasal_verb(last_v + " " + verb)
                        phrasal_verb = last_v + "_" + verb
                        #print("+PP", phrasal_verb, end="  ")
                        temp_graph2.remove_edge(noun1, noun2) 
                        temp_graph2.add_edge(noun1, noun2, label = phrasal_verb)
                        continue
                    elif noun1 == "NOUN":       # skip any header information
                        continue                # rest of the file contains prepositions
                    elif skip_prepositions and prepositionTest(verb):
                        continue

                    #  Coreference chains
                    noun1 = parse_new_coref_chain(noun1)
                    noun2 = parse_new_coref_chain(noun2)

                    noun1 = pre_existing_node(temp_graph2, noun1)
                    if not( noun1 in temp_graph2.nodes() ):
                        temp_graph2.add_node(noun1, label=noun1)

                    noun2 = pre_existing_node(temp_graph2, noun2)
                    #what if NEW node2 should replace current version of node1 23-July
                    if head_word(noun1) == head_word(noun2):
                        noun1 = pre_existing_node(temp_graph2, noun1)

                    # VERB - Edge - Predicate

                    if not (noun2 in temp_graph2.nodes()):
                        temp_graph2.add_node(noun2, label=noun2)
                    temp_graph2.add_edge(noun1, noun2, label = verb)
                    #print(noun1, verb, noun2, end="   ")

                elif mode == 'code' or len(row) == 6 or row[0:3] == "Type":    # Code Graphs
                    #print("Mode==code", end="")
                    #termSeparator = ":"
                    #if len(row) == 6:
                    #    b1, b2, methodName, noun1, verb, noun2 = row
                    if len(row) == 6:
                        methodName, noun1, verb, noun2 ,nr1, nr2 = row
                        noun1 = nr1 + ":" + noun1
                        noun2 = nr2 + ":" + noun2
                    elif len(row) == 3:
                        noun1, verb, noun2 =  row
                    noun1 = noun1.strip()   # remove leading spaces
                    verb = verb.strip()
                    noun2 = noun2.strip()
                    #if(noun1.find(termSeparator) != -1):     #If a word contains an underscore, maps nodLis[0] to the first part of that word
                    #noun1 = noun1.split(termSeparator) #[0]
                    temp_graph2.add_node(noun1, label = noun1)
                    #if(noun2.find(termSeparator) != -1):     #If there is a word with an underscore, maps nodLis[0] to the first part of that word
                    #noun2 = noun2.split(termSeparator) # [0]
                    temp_graph2.add_node(noun2, label = noun2)
                    temp_graph2.add_edge(noun1, noun2, label = verb)
                    #print(noun1, verb, noun2, end="   ")
                if mode == 'English':
                    last_s = noun1
                    last_v = verb #Used for phrasal verb identification "run_by"
                    last_o = noun2
        except csv.Error as e:
            sys.exit('file %s, line %d: %s' % (csvPath, csvreader.line_num, e))

    if mode == 'English':
        #print("Coalescing:\n", temp_graph2.nodes(), end="  ")
        global coalescing_completed
        coalescing_completed = False
        iteration_limit = temp_graph2.number_of_nodes()
        while not coalescing_completed and iteration_limit>0:
              final_pass_coalescing()
              iteration_limit -=1
              #print(iteration_limit, end=" ")
        #print("After coalescing:\n", temp_graph2.nodes(), end="  ")

    return temp_graph2
# end of build_graph_from_csv(targetFile)


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
        chn = in_chain.split(termSeparator)  # "its_warlike_neighbor_Gagrach".split("_")
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
    #node_list = temp_graph2.nodes()
    node_list = list(temp_graph2)
    print("FPC", end=" ")
    zz = list(temp_graph2)
    #zzz = type(zz)
    flag = False
    for graph_node in zz: # node_list:  # Final-pass Coalescing
        gn_pn = contains_proper_noun(graph_node)
        #limit = temp_graph2.nodes()
        #t1 = node_list.index(graph_node)
        #temp = node_list[1 + node_list.index(graph_node):]
        for g_node2 in node_list[1 + node_list.index(graph_node):]:  # subsequent nodes #in limit
            gn_pn2 = contains_proper_noun(g_node2)
            #dummy_boole = graph_node is g_node2                      #Proper noun based merge
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
            #if extendedNoun == "there_some":
            #    print("dud")
            remapping = {g_node2: extendedNoun}
            print(" R2Map", graph_node,"+",g_node2,"->", extendedNoun, graph_node == g_node2, end="--    ")
            temp_graph2 = nx.relabel_nodes(temp_graph2, remapping, copy=False)
            temp_graph2.nodes[extendedNoun]['label'] = extendedNoun

            flag = False
            coalescing_completed = False
            break
        #return
        #print("again", end=" ")
    return


def list_diff(li1, li2):
    return (list(set(li1) - set(li2)))


def reorganise_coref_chain_DEPRECATED(strg): # noun-propernoun-pronoun
    """Using NLTK pos_tag """
    global termSeparator
    noun_lis = []
    propN_lis = []
    pron_lis = []
    if strg.find(termSeparator)<0:
        slt = strg
    else:
        chn = strg.split(termSeparator) # "its_warlike_neighbor_Gagrach".split("_")
        strg2 = " ".join(chn)
        chn2 = nltk.pos_tag(word_tokenize(strg2))
        for (tokn, po) in chn2:
            if tokn in ['a', 'the', 'its']: # remove problematic words
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

def reorganise_coref_chain(strg): # noun-propernoun-pronoun
    global termSeparator
    noun_lis = []
    propN_lis = []
    pron_lis = []
    if strg.find(termSeparator)<0:
        slt = strg
    else:
        chan = strg.split(termSeparator)
        for tokn in chan:
            if tokn in ['a', 'the', 'its']: # remove problematic words
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
#reorganise_coref_chain("its_warlike_neighbor_Gagrach")
# reorganise_coref_chain("He_hunter_he_him")
#reorganise_coref_chain('hawk_she_Karla')
#reorganise_coref_chain('hawk_Karla_she')


def head_word(term): #first word before term separator
    global termSeparator
    z = term.split(termSeparator)[0]
    # if is_pronoun(z):
    #     return False
    # else:
    return z

def is_proper_noun(wrd):
    return ( (nltkWords.words().__contains__(wrd) == False)
              and (wn.synsets(wrd) == []) )
# is_proper_noun("Karla")   is_proper_noun("karla")

def contains_proper_noun(wrd): #wrd may be a coreference chain
    global termSeparator
    for wo in wrd.split(termSeparator):
        if ( (nltkWords.words().__contains__(wo) == False) and (wn.synsets(wo) == []) ):
            return wo
    return False
# contains_proper_noun("Karla")   contains_proper_noun("she_karla")

def contains_proper_noun_from_lis(lis): #wrd may be a coreference chain
    global termSeparator
    for wo in lis:
        if ( (nltkWords.words().__contains__(wo) == False) and (wn.synsets(wo) == []) ):
            return wo
    return False

def is_pronoun(wrd):
    return wrd in pronoun_list
# is_pronoun("he")

def is_noun(wrd):
    zz = wn.synsets(wrd, pos=wn.NOUN)
    return zz != []
# is_noun("a")

# ###############################
# ####### Process Graphs ########
# ###############################

 
def printEdges(G):     # printEdges(sourceGraph)
    for (u, v, reln) in G.edges.data('label'):
        print('(%s %s %s)' % (u, reln, v))


def returnEdges(G):  # returnEdges(sourceGraph)
    """returns a list of edge names, followed by a printable string """
    res = ""
    for (u, v, reln) in G.edges.data('label'):
        res = res + u + " " + reln  + " " + v + '.' + "\n"
        print(reln, end=" ")
    return res
# returnEdges(targetGraph)


def returnEdgesAsList(G):  # returnEdgesAsList(sourceGraph)
    """ returns a list of lists, each composed of triples"""
    res = []
    for (u, v, reln) in G.edges.data('label'):
        res.append([u, reln, v])
    return res
# returnEdgesAsList(targetGraph)

def ps():
    print(returnEdgesAsList(sourceGraph))
def pt():
    print(returnEdgesAsList(targetGraph))


def returnEdgesBetweenTheseObjects(subj,obj, thisGraph):
    """ returns a list of verbs (directed link labels) between objects - or else [] """ 
    res = []
    #print(thisGraph.edges.data('label'))
    for (s, o, relation) in thisGraph.edges.data('label'):
        if (s==subj) and (o==obj):
            #print(1, end=" ")
            res.append(relation)
    return res
# returnEdgesBetweenTheseObjects('woman','bus', targetGraph)


def predExists(subj,rel,obj, thisGraph): # predExists('man','drive','car', sourceGraph)
    for (s, o, r) in thisGraph.edges.data('label'):
        if (s==subj) and (o==obj) and (r==rel):
            return True
    return False


def returnMappingRatio(tgt): # returnMappingRatio(sourceGraph)
    mapped = notMapped = 0
    lis = returnEdgesAsList(tgt)
    tmp = 0
    for (s,v,o) in lis:
        if (s in GM.mapping.keys()) and (v in GM.mapping.values())  and (o in GM.mapping.keys()):
            mapped += 1
        else:
            notMapped += 1
        tmp = mapped + notMapped
    if tmp == 0:
        rslt = 0
    else:
        rslt = mapped/(mapped + notMapped)
    return mapped, rslt


def printMappedPredicates(graf): # printMappedPredicates(sourceGraph)
    mapped = notMapped = 0
    lis = returnEdgesAsList(graf)
    global mapped_predicates
    global analogyFilewriter
    mapped_predicates = []
    flag = False
    unmapped = set()
    for (s,v,o) in lis:
        s_mapped = s in GM.mapping.keys()
        v_mapped = v in GM.mapping.keys()
        o_mapped = o in GM.mapping.keys()
        if s_mapped and v_mapped and o_mapped:
            print(s,",", v,", ", o, "  == \t   ", end="")    # Full predicate mapped
            mapped += 1
            v_map = GM.mapping.get(v)
            rslt = wn_sim(v, v_map, 'v')
            mapped_predicates.append([s,v,o])
            print(GM.mapping.get(s),",", v_map,",", GM.mapping.get(o),
                  "\t\t", round( (float(rslt[0])+(float(rslt[2])))/2, 2))
            out_list = [ s, v, o, " == ", GM.mapping.get(s), v_map, GM.mapping.get(o),
                          round( (float(rslt[0])+(float(rslt[2])))/2, 2) ]
        elif s_mapped or v_mapped or o_mapped:
            print(s,", ", v,", ", o, "   == \t   ", end="")
            out_list = [s, v, o, " '== "]
            if s_mapped:           # partial predicate mapping
                print(GM.mapping.get(s), end=", ")
                out_list.append(GM.mapping.get(s))
            else:
                print("", end=" _ , ")
                out_list.append(" _")
                unmapped.add(s)
            if v_mapped:
                print(GM.mapping.get(v), end=", ")
                out_list.append(GM.mapping.get(v))
                flag = True
            else:
                print("", end=" _ , ")
                out_list.append(" _ ")
                unmapped.add(v)
            if o_mapped:
                print(GM.mapping.get(o), end="")
                out_list.append(GM.mapping.get(o))
            else:
                print(" _   ", end="")
                out_list.append(" _ ")
                unmapped.add(o)
            if flag:
                rslt = wn_sim(v, GM.mapping.get(v), 'v')
                tmp = round( (float(rslt[0])+(float(rslt[2])))/2, 2)
                print(tmp, end="")
                #out_line = out_line + tmp
                out_list.append(tmp)
            else:
                print()
        else:
            out_list = []
            unmapped.add(s)
            unmapped.add(v)
            unmapped.add(o)
        flag = False
        if out_list:
            analogyFilewriter.writerow(out_list)
    print(" UNMAPPED: ", unmapped)
    analogyFilewriter.writerow(["UNMAPPED: ",  str(unmapped).replace(",", " ") ])
    return mapped, notMapped  # numeric summary

def pm():
    printMappedPredicates(sourceGraph)


def show_graph(TgtGraph):
    plt.figure()
    pos_nodes = nx.spring_layout(TgtGraph, k=0.2, pos=None, fixed=None, iterations=150,
                                 threshold=0.01, weight='weight', scale=2, center=None, dim=2, seed=None)
    nx.draw(TgtGraph, pos_nodes, node_color='gold', with_labels=False)
    pos_attrs = {}
    for node, coords in pos_nodes.items():
        pos_attrs[node] = (coords[0], coords[1] + 0.05)
    node_attrs = nx.get_node_attributes(TgtGraph, 'label')
    custom_node_attrs = {}
    for node, attr in node_attrs.items():
        custom_node_attrs[node] = attr
    edge_labels1=dict([((u,v,),d['label'])
                 for u,v,d in TgtGraph.edges(data=True)])
    nx.draw_networkx_edge_labels(TgtGraph, pos_attrs, alpha=0.7, edge_labels = edge_labels1)
    nx.draw_networkx_labels(TgtGraph, pos_attrs, labels=custom_node_attrs)
    
    plt.title("abc") #sourceGraph.graph['Graphid'])
    plt.axis('off')
    plt.show()
#show_graph(targetGraph)


# Shows graph in html/javascript D3js force directed graph.
def show_graph_in_FF(Graph):
    data = {
        'nodes': [],
        'edges': []
    }
    for index, node in enumerate(Graph.nodes()):
        Graph.node[node]['index'] = index   # some nodes may not have label attribute set
    #print("", end="")
    for node_id, attr in Graph.nodes(data=True):
        #print(node_id, attr, end="  ")
        data['nodes'].append({'label': attr['label']})

    for source, target, attr in Graph.edges(data=True):
        data['edges'].append(
            {
                'source': Graph.node[source]['index'],
                'target': Graph.node[target]['index'],
                'label': attr['label']  
            }
        )
    graphName = Graph.graph['Graphid']
    if graphName.endswith('.csv'):
        graphName = graphName[:-4]

    # write .json & update html code
    if not os.path.exists(os.path.dirname(htmlBranch)):
        try:
            os.makedirs(os.path.dirname(htmlBranch))
        except OSError as exc:  # Guard against race condition
            if exc.errno != errno.EEXIST:
                raise

    with open(htmlBranch + graphName+'.json', 'w+') as outfile:
        json.dump(data, outfile, indent=4, sort_keys=True)

    try:
        with open('Template.html', 'r') as file:
            htmlText = file.read()
    except IOError:
        print("ERROR - Can't find the file: Template.html")
    htmlText = htmlText.replace('XXXX', graphName)    # containing XXXX.json data

    with open(htmlBranch +graphName+'.html', 'w+') as outHtmlFile:
        outHtmlFile.write(htmlText)
    outHtmlFile.close()

    x = 0
    x = webbrowser.get()
    x=1
#    subprocess.run([r'C:\Program Files\Mozilla Firefox\Firefox.exe',
#                           os.path.realpath(htmlBranch + graphName + '.html')])
    webbrowser.open(os.path.realpath(htmlBranch + graphName + '.html'), new=2)
#    webbrowser.open_new_tab( os.path.realpath(htmlBranch + graphName + '.html') )
    time.sleep(0.6)
#show_graph_in_FF(sourceGraph)

 
def ff():   # show_graph_in_FF(sourceGraph)
    show_graph_in_FF(targetGraph)
def fs():   # show_graph_in_FF(sourceGraph)
    show_graph_in_FF(sourceGraph)
def ft():   
    show_graph_in_FF(targetGraph)   


# ************************************************************************
# ************************* Cache and Similarity *************************
# ************************************************************************


global arrow
arrow = " <-> "


def read_wn_cache_to_dict():
    global CachePath
    global WN_cache
    WN_cache = {}
    with open(CachePath, "r") as wn_cache_file:
        filereader = csv.reader(wn_cache_file)
        #wn_cache_file.readline()   #skip header
        for row in filereader:
            try: 
                #print(row[0], row[1], "#####")
                WN_cache[row[0]+"-"+row[1]] = row[2:]
            except IndexError:
                pass  

#read_wn_cache_to_dict()
#print("WordNet Cache initialised.         ", end="")

def wn_sim(w1, w2, partoS):
    """ wn_sim("create","construct", 'v') -> [0.6139..., 'make(v.03)', 0.666..., 'make(v.03)'] """
    global LCSLlist
    lin_max = wup_max = 0
    LCSL_temp = LCSW_temp = []
    wn1 = wn.morphy(w1, partoS)
    wn2 = wn.morphy(w2, partoS)    
    LCSL = LCSW = "-"
    syns1 = wn.synsets(w1, pos = partoS)
    syns2 = wn.synsets(w2, pos = partoS)
    if w1 == w2:
        LCSL = w1
        LCSW = w1
        lin_max = 1
        wup_max = 1
    elif w1+"-"+w2 in WN_cache:
        zz = WN_cache[w1+"-"+w2]
        if zz[0] == partoS:
            lin_max = zz[1]
            wup_max = zz[2]
            LCSL = zz[3]
            LCSW = zz[4]
    else:
        for ss1 in syns1:       
            for ss2 in syns2:
                lin = ss1.lin_similarity(ss2, brown_ic) #semcor_ic) #brown_ic
                wup = ss1.wup_similarity(ss2)
                if lin > lin_max:
                    lin_max = lin
                    ss1_Lin_temp = ss1
                    ss2_Lin_temp = ss2
                    LCSL_temp = ss1.lowest_common_hypernyms(ss2)
                    #print(" &&&& LCSL_temp1", lin, ss1, ss2, LCSL_temp)
                if wup > wup_max:
                    wup_max = wup
                    ss1_Wup_temp = ss1
                    ss2_Wup_temp = ss2
                    LCSW_temp = ss1.lowest_common_hypernyms(ss2)   # may retrun []
                    #print(" &&&& LCSW_temp1", wup, ss1, ss2, LCSW_temp, LCSW_temp==[])
                if lin is None:
                    lin = 0
                if wup is None:
                    wup = 0
        if lin_max>0:
            LCSL_temp = ss1_Lin_temp.lowest_common_hypernyms(ss2_Lin_temp)
            LCSL = simplifyLCSList(LCSL_temp)
        if wup_max>0:
            LCSW_temp = ss1_Wup_temp.lowest_common_hypernyms(ss2_Wup_temp)
        if lin_max < 0.0000000001:
            lin_max = 0
            LCSW = simplifyLCSList(LCSW_temp)
        #print(" &&&& LCSW_temp2 ", LCSW_temp)
        if LCSW_temp == []:
            LCSW = "Synset('null." + partoS +".02')"
        write_to_wn_cache_file(w1, w2, partoS, lin_max, wup_max, LCSL, LCSW)
    LCSLlist.append(LCSL)   #for the GUI presentation
    if LCSL_temp == []:
        LCSL = "Synset('null." + partoS +".0303')"
    if LCSW_temp == []:
        LCSW = "Synset('null." + partoS +".0404')"
    return [lin_max, LCSL, wup_max, LCSW]
#wn_sim("create","construct", 'v')



def write_to_wn_cache_file(w1, w2, pos, Lin, Wup, L_lcs, W_lcs):
    global CachePath
    if w1 == w2:
        return
    with open(CachePath,"a+") as wn_cache_file:
        Stringtest = w1 + "," + w2 + "," + pos
        Stringtest += "," + str(Lin) + "," + str(Wup) + "," + L_lcs + "," + W_lcs+","
        wn_cache_file.write(" \n" + Stringtest )

###########################################################################################################

def calculate2Similarities(tgt_graph):   # source concept nodes
        #print("c2Sim ")
        global arrow
        global analogyFilewriter
        global mapped_predicates
        semcor_ic = wordnet_ic.ic('ic-semcor.dat')
        d = 0
        j = 0
        i = 0
        max_value = 0.0
        max_value2 = 0.0
        Stringtest = " "
        save =[]
        save2 =[]
        LCSL = " "
        LCSW = " "
        arrow = "<-->"
        x = 0
        y = 0
        mapped = ""
        mapped2 = ""
        global GM
        #global temp_graph
        #global temp_graph2
        global CSVPath
        #global CSVName
        #global csvfile
        global analogyFileName
        global CachePath
        global LCSLlist
        global mappedRelations
        global unmappedRelations
        global mappedConcepts
        global unmappedConcepts
        global inferenceList
        mappedRelations = 0
        unmappedRelations = 0
        mappedConcepts = 0
        unmappedConcepts = 0
        
        global numInferences
        global inferenceList

        conSim = numpy.zeros(7) # Lin0, WuP0, Lin1, Wup1, LinSum, WuPSum, 
        relSim = numpy.zeros(7)
        averageNounLin = 0
        averageNounWup = 0
        averageVerbLin = 0
        averageVerbWup = 0
        numInferences = len(inferenceList)
        anaSim = 0.0

        tgt_preds = returnEdgesAsList(tgt_graph)
        if not os.path.exists(os.path.dirname(CSVPath + analogyFileName)):
            try:
                os.makedirs(os.path.dirname(CSVPath + analogyFileName))
            except OSError as exc:  # Guard against race condition
                if exc.errno != errno.EEXIST:
                    raise
                                #########################
                                # RELATIONAL SIMILARITY #
                                #########################
        with open(CSVPath + analogyFileName, 'w+') as analogyFile:
            analogyFilewriter = csv.writer(analogyFile, delimiter=',',
                quotechar='|', quoting=csv.QUOTE_MINIMAL,  lineterminator = '\n')
            analogyFilewriter.writerow(['Type', 'Word1','Word2', 'Lin', 'Wup', 'LCS Lin', 'LCS Wup'])
            analogyFilewriter.writerow([ analogyFileName.partition("__")[0] ]) # target name
            analogyFilewriter.writerow([ analogyFileName.partition("__")[2] ])  #source name
            #if vbse>3:
            #    print("FILE:", CSVPath, analogyFileName)
            for pred in tgt_preds:
                #sPrime = pred[0].split(termSeparator)[0] # head word
                #vPrime = pred[1] #.rsplit(termSeparator)[1]  #oPrime = pred[2].split(termSeparator)[0] # head word
                if ( (mode == 'code') and (pred[0] in GM.mapping.keys()) and
                     (pred[1] in GM.mapping.keys()) and (pred[2] in GM.mapping.keys()) ):
                    #print(pred[0], pred[1], pred[2], " <-> ", end="")
                    #print(GM.mapping[pred[0]], GM.mapping[pred[1]], GM.mapping[pred[2]], end= "    \t")
                    mappedRelations += 1
                    res,Lin_LCS,Wu_LCS = evaluateRelationalSimilarity(pred[1], GM.mapping[pred[1]])
                    analogyFilewriter.writerow(['Rel', pred[1], GM.mapping[pred[1]], res[4], res[5], Lin_LCS, Wu_LCS])
                    if vbse>3:
                        print('Rel', pred[1], GM.mapping[pred[1]], res[4], res[5], Lin_LCS, Wu_LCS)
                    relSim = relSim + res
                elif (mode=='code'):
                    #print("###", pred[0], pred[1], pred[2], " \=/ ")
                    unmappedRelations += 1
                elif (mode == 'English' and (pred[0] in GM.mapping.keys()) and
                     (pred[1] in GM.mapping.keys()) and (pred[2] in GM.mapping.keys()) ):
                    #print(pred[0], pred[1], pred[2], " <-> ", end="")
                    #print(GM.mapping[pred[0]], GM.mapping[pred[1]], GM.mapping[pred[2]], end= "    \t")
                    mappedRelations += 1
                    res,Lin_LCS,Wu_LCS = evaluateRelationalSimilarity(pred[1], GM.mapping[pred[1]])
                    analogyFilewriter.writerow(['Rel', pred[1], GM.mapping[pred[1]], res[4], res[5], Lin_LCS, Wu_LCS])
                    if vbse>3:
                        print('Rel', pred[1], GM.mapping[pred[1]], res[4], res[5], Lin_LCS, Wu_LCS)
                    relSim = relSim + res
                elif (mode=='English'):
                    if vbse>3:
                        print("###", pred[0], pred[1], pred[2], " \=/ ")
                    unmappedRelations += 1
            #print("RELATIONS:", mappedRelations, unmappedRelations, relSim)
                                #########################
                                # Conceptual SIMILARITY # iterate over mapping, to avoid double counting
                                #########################
            #halt()
            setOfConcepts = set() 
            setOfRelations = set() 
            for x in tgt_preds:
                #print(x[0], end="--")
                setOfConcepts.add(x[0])  
                setOfConcepts.add(x[2])
                if vbse>3:
                    print(x[0],x[2], end="   \t")
                setOfRelations.add(x[1])
            #print("\nGID", tgt_graph.graph['Graphid'], setOfConcepts)
            for key in GM.mapping:
                if key in setOfConcepts:
                    mappedConcepts += 1
                    res,Lin_LCS,Wu_LCS = evaluateConceptualSimilarity(key, GM.mapping[key])
                    analogyFilewriter.writerow(['Con', key, GM.mapping[key], res[4], res[5], Lin_LCS, Wu_LCS])
                    if vbse>3:
                        print('Con', key, GM.mapping[key], res[4], res[5], Lin_LCS, Wu_LCS)
                    conSim =  conSim + res
                if key in setOfRelations:
                    mappedRelations += 1
                    res, Lin_LCS, Wu_LCS = evaluateRelationalSimilarity(key, GM.mapping[key])
                    analogyFilewriter.writerow(['Rel', key, GM.mapping[key], res[4], res[5], Lin_LCS, Wu_LCS])
                    if vbse > 3:
                        print('Rel', key, GM.mapping[key], res[4], res[5], Lin_LCS, Wu_LCS)
                    relSim = relSim + res
            unmappedConcepts = len(setOfConcepts) - mappedConcepts
            #print("CONCEPTS:", mappedConcepts, unmappedConcepts, conSim)

            # GROUNDED INFERENCES
            #generateCWSGInferences(sourceGraph, targetGraph)
            for a,r,b in inferenceList:
                analogyFilewriter.writerow(["Inference", a, r, b])

            # Relations
            analogyFilewriter.writerow(['#Verb Lin==0', relSim[0], 'of', (mappedRelations+ unmappedRelations)])
            analogyFilewriter.writerow(['#Verb WuP==0', relSim[1], 'of', (mappedRelations+ unmappedRelations)])
            if mappedRelations + unmappedRelations==0:
                avgLinV = 0
                avgWupV = 0
            else:
                avgLinV = relSim[4]/(mappedRelations + unmappedRelations)
                avgWupV = relSim[5]/(mappedRelations + unmappedRelations) 
            analogyFilewriter.writerow(['Avg Verb Lin ', avgLinV])
            analogyFilewriter.writerow(['Avg Verb Wup ', avgWupV])
            analogyFilewriter.writerow(['#Verb Lin== 1', relSim[2], 'of', (mappedRelations + unmappedRelations)])
            analogyFilewriter.writerow(['#Verb WuP== 1', relSim[3], 'of', (mappedRelations + unmappedRelations)])
            # Concepts
            analogyFilewriter.writerow(['#Noun Lin==0', conSim[0], 'of', (mappedConcepts + unmappedConcepts)])
            analogyFilewriter.writerow(['#Noun WuP==0', conSim[1], 'of',  (mappedConcepts + unmappedConcepts)])
            if mappedConcepts + unmappedConcepts==0:
                avgLin = 0
                avgWup = 0
            else:
                avgLin = conSim[4]/(mappedConcepts + unmappedConcepts)
                avgWup = conSim[5]/(mappedConcepts + unmappedConcepts) 
            analogyFilewriter.writerow(['Avg Noun Lin ', avgLin])
            analogyFilewriter.writerow(['Avg Noun Wup ', avgWup])
            analogyFilewriter.writerow(['#Noun Lin== 1', conSim[2], 'of', (mappedConcepts + unmappedConcepts)])
            analogyFilewriter.writerow(['#Noun WuP== 1', conSim[3], 'of', (mappedConcepts + unmappedConcepts)])

            print( avgLin ,avgWup, mappedConcepts, unmappedConcepts, avgLinV, avgWupV, mappedRelations, unmappedRelations )
            
            #analogicalSimilarity = ( ((((avgLin+avgWup)/2)*mappedConcepts)/(mappedConcepts + unmappedConcepts) * 0.5) +
            #                         ((((avgLinV+avgWupV)/2)*mappedRelations)/(mappedRelations+ unmappedRelations)*0.5) )
            analogicalSimilarity = ( ((((avgLin+avgWup)/2)*mappedConcepts) * 0.5) +
                                     ((((avgLinV+avgWupV)/2)*mappedRelations) *0.5) )
            analogyFilewriter.writerow(['AnaSim=',analogicalSimilarity])

            # Write Summary File Data
            print(targetGraph.graph['Graphid'].rpartition(".")[0], sourceGraph.graph['Graphid'].rpartition(".")[0],
                     conSim[0], conSim[1], "{:.2f}".format(avgLin), "{:.2f}".format(avgWup), conSim[2], conSim[3], " ",
                     relSim[0], relSim[1], "{:.2f}".format(avgLinV), "{:.2f}".format(avgWupV), relSim[2], relSim[3], " ",
                     numInferences, mappedConcepts, mappedRelations, "{:.2f}".format(analogicalSimilarity) )
            writeSummaryFileData(targetGraph.graph['Graphid'], sourceGraph.graph['Graphid'],
                     conSim[0], conSim[1], avgLin, avgWup, conSim[2], conSim[3],
                     relSim[0], relSim[1], avgLinV, avgWupV, relSim[2], relSim[3],
                     numInferences, mappedConcepts, mappedRelations, analogicalSimilarity) #mappedEdges

            printMappedPredicates(tgt_graph)

        #pp.pprint(GM.mapping)
        #analogyFile.flush()
        #analogyFile.close()
################################################################################################################



def evaluateRelationalSimilarity(tRel, sRel):  #car, truck
    global termSeparator
    reslt = numpy.zeros(7)   # Lin0, WuP0, Lin1, Wup1, LinSum, WuPSum,
    if tRel == sRel:
        reslt[2] = 1
        reslt[3] = 1
        reslt[4] = 1
        reslt[5] = 1
        LinLCS = tRel
        WuPLCS = tRel 
    elif mode == 'code':
        if (tRel.split(termSeparator) != []) and (tRel.split(termSeparator)[:1] == sRel.split(termSeparator)[:1]):  #Head identicality for relations?
            reslt[4] = 0.81
            reslt[5] = 0.811
            LinLCS = tRel.split(termSeparator)[:1]
            WuPLCS = tRel.split(termSeparator)[:1]
        elif tRel.split(termSeparator)[0] == sRel.split(termSeparator)[0]:
            reslt[4] = 0.33
            reslt[5] = 0.33
            LinLCS = tRel.split(termSeparator)[0]
            WuPLCS = tRel.split(termSeparator)[0]
        else:
            temp_result = wn_sim(tRel, sRel, 'v')
            #print("temp_result",temp_result)
            reslt[4] = temp_result[0]
            reslt[5] = temp_result[2]
            LinLCS = 'no-reln'
            WuPLCS = 'no-relnn'
    else:
        temp_result = wn_sim(tRel, sRel, 'v') # returns [0.6139, 'make(v.03)', 0.666, 'make(v.03)']
        if float(temp_result[0])>0 or float(temp_result[2])>0:
            if temp_result[0] == 0:
                reslt[0]=1
            elif temp_result[0] == 1:
                reslt[2]=1
            else:
                reslt[4] == temp_result[0]
            if temp_result[2] == 0:
                reslt[1]=1
            elif temp_result[2] == 1:
                reslt[3] = 1
            else:
                reslt[5] = temp_result[2]
        LinLCS = temp_result[1]  # .find('(')
        WuPLCS = temp_result[3]
    return reslt, LinLCS, WuPLCS


def evaluateConceptualSimilarity(tRel, sRel):  # ('fly','drive')
    global termSeparator
    reslt = numpy.zeros(7)   # Lin0, WuP0, Lin1, Wup1, LinSum, WuPSum,
    if tRel == sRel:
        reslt[2] = 1
        reslt[3] = 1
        reslt[4] = 1
        reslt[5] = 1
        LinLCS = tRel
        WuPLCS = tRel
    elif mode == 'code':
        if tRel.split(termSeparator)[:1] == sRel.split(termSeparator)[:1]:
            reslt[4] = 0.8
            reslt[5] = 0.8
            LinLCS = tRel.split(termSeparator)[:1]
            WuPLCS = tRel.split(termSeparator)[:1]
        elif tRel.split(termSeparator)[0] == sRel.split(termSeparator)[0]:
            reslt[4] = 0.33
            reslt[5] = 0.33
            LinLCS = tRel.split(termSeparator)[0]
            WuPLCS = tRel.split(termSeparator)[0]
        else:
            reslt[0] = 0.00001
            reslt[1] = 0.00001
            LinLCS = 'none'
            WuPLCS = 'none'
    else:
        temp_result = wn_sim(tRel, sRel, 'n') # returns [0.6139 'make(v.03)', 0.666, 'make(v.03)']
        #print("temp_result", temp_result)
        if float(temp_result[0])>0 or float(temp_result[2])>0:
            if temp_result[0] == 0:
                reslt[0]=1
            elif temp_result[0] == 1:
                reslt[2]=1
            else:
                reslt[4] == temp_result[0]
            if temp_result[2] == 0:
                reslt[1]=1
            elif temp_result[2] == 1:
                reslt[3] = 1
            else:
                reslt[5] = temp_result[2]
        LinLCS = temp_result[1]
        WuPLCS = temp_result[3]
    return reslt, LinLCS, WuPLCS



######################################################################## 
########################################################################
######################################################################## 


# simplifyLCS("Synset('object.n.01')") -> "object"    simplifyLCS(["Synset('object.n.01')"]) -> "object"
# simplifyLCSList(["Synset('physical_entity.n.01')"]) -> "object"
# simplifyLCSList(["Synset('move.v.02')"] )
def simplifyLCS(synsetName):
    #print(" >sLCS ", end="")
    #if vbse>3:
    #print(" .", synsetName, type(synsetName), end=".  ")
    if isinstance(synsetName, list):
        synsetName = simplifyLCS(synsetName[0]) + simplifyLCS(synsetName[1:])
        #print(" sLCS1 ", end=" ")
        #return synsetName
    elif (isinstance(synsetName, str)) and ("Synset" in synsetName):    
        #print(" sLCS2 -> ", end=" ")
        y = synsetName.find('(') + 2
        z = synsetName.find('.') +5
        synsetName = synsetName[y:z].replace('.','(', 1) + ")"
        #return synsetName
    elif (isinstance(synsetName, list)) and (len(synsetName) >1):
        #print(" sLCS3 ", end="")
        #print(synsetName, end=" ")
        simplifyLCS(synsetName[0]).append(simplifyLCS(synsetName[1:]))  
        simplifyLCS(str(synsetName[0])).append(simplifyLCSList(synsetName[1:]))  #11/10
        #print("{", synsetName, "}")
    else: #instance of <class 'nltk.corpus.reader.wordnet.Synset'>
        #print(" sLCS4 -> ", end=" ")
        ssString = str(synsetName)
        y = ssString.find('(') + 2
        z = ssString.find('.') + 5
        synsetName = ssString[y:z].replace('.','(', 1) + ")"
        #return synsetName
    #print("end sLCS")
    return synsetName #[synsetName]
# simplifyLCS("[Synset('whole.n.02')]")



def simplifyLCSList(synsetList):
    #print(" sLCSL*", type(synsetList), ":", synsetList, end=" ")
    if (synsetList is None):
        #print(" sLCSL6", end=" ")
        return "none1"
    elif (synsetList == []):
        #print(" sLCSL1", end=" ")
        return ""
    elif synsetList == "none":
        #print(" sLCSL0", end=" ")
        return "none"
    elif (isinstance(synsetList, str)):
        #print(" sLCSL4", end=" ")
        z = simplifyLCS(synsetList)
        #print(z, end=" shudBDone")
        return z
    elif (isinstance(synsetList, list)) and (len(synsetList) >1):
        #print(type(synsetList), end="")
        #print(" sLCSL2", end=" ")
        #print(simplifyLCS(synsetList[0]), end=" ")
        #synsetName.append(simplifyLCS(synsetName[1:]))
        return str(simplifyLCS(synsetList[0]))  + "_" + str(simplifyLCSList(synsetList[1:]))
    elif (isinstance(synsetList, list)) and (len(synsetList) ==1):
        #print(" sLCSL3", simplifyLCS(synsetList[0]), end=" ")
        return simplifyLCS(synsetList[0])
    else:
        print(" sLCSL5", end="")
        zz = simplifyLCS(synsetList)
        #print(zz, end=" ")
        return zz
# simplifyLCSList(  )
# l=simplifyLCSList([])


######################################################################## 
#############################     ######################################
############################  VF2  ##################################### 
#############################     ######################################
########################################################################


def mappingProcess(target_graph, source_graph):
    global GM
    global relationMapping
    global numberOfTimeOuts
    GM.mapping.clear()
    isomorphvf2CB.temp_sol = []
    timeLimit = 5.0

    #manager = multiprocessing.Manager()
    #return_dict = manager.dict()
    GM = isomorphvf2CB.MultiDiGraphMatcher(target_graph, source_graph)
    #print(" BEFORE TimeOut >>>>>>>>>>>>>", end="")
    #p1 = Process(target=isomorphvf2CB.MultiDiGraphMatcher,
    #             args=(source_graph, target_graph), name='MultiDiGraphMatcher')
    #p1.start()
    #p1.join(timeout=timeLimit)
    #p1.terminate()
    #if p1.exitcode is None:     # a TimeOut 
    #   print("Oops, {p1} timeouts!")
    #   numberOfTimeOuts += 1
    #   return 0
    #p2 = Process(target=isomorphvf2CB.MultiDiGraphMatcher.subgraph_is_isomorphic, args=(GM,),
    #             name='subgraph_is_isomorphic')
    #p2 = Process(target=isomorphvf2CB.MultiDiGraphMatcher.subgraph_is_isomorphic,
    #             args=(GM), name='subgraph_is_isomorphic')
    #p2.start()
    #p2.join(timeout=timeLimit)
    #p2.terminate()
    #if p2.exitcode is None:     # a TimeOut 
    #   print("Oops, {p1} timeouts!")
    #   numberOfTimeOuts += 1
    #   return 0
    #print(" <<<<<<<<<<< AFTER TimeOut")#, end="  ")
    #print("GM.mapping:", GM.mapping)
    res = GM.subgraph_is_isomorphic()
    if len(GM.mapping)==0:
        print(":-( NO Mapping:") #print(":-) SubGr Iso, Mapping:", GM.mapping)
    else:
        print("   ", len(GM.mapping), "mapped atoms. ")


def develop_analogy(target_graph, source_graph):
    print("\n###DEVELOP_ANALOGY() ", end="")
    #global GM
    global relationMapping
    global numberOfTimeOuts
    GM.mapping.clear()
    isomorphvf2CB.temp_sol = []

    if source_graph.number_of_nodes() == 0:
        return 0
    
    mappingProcess(target_graph, source_graph) # uses Multiprocessing
    print(" Mapping finished.", end="")
    addRelationsToMapping(target_graph, source_graph)  #10/10
    generateCWSGInferences(target_graph, source_graph) 

    calculate2Similarities(target_graph) # dod2020
    
    return 0
# end of develop_analogy()



def addRelationsToMapping(target_graph, source_graph): #addRelationsToMapping(sourceGraph,targetGraph)
    """ Tailored for matching code graphs"""
    #print("##aRTM", end="")
    global mapping
    global mappedpairs
    global arrow
    global relationMapping  #reorganise_coref_chain(coref_terms)
    global termSeparator
    srcEdges = returnEdgesAsList(source_graph)
    tgtEdges = returnEdgesAsList(target_graph)
    for sNoun1,sRelation,sNoun2 in srcEdges:
        tmp1 = reorganise_coref_chain(sNoun1) # he_tom -> tom_he
        tmp2 = reorganise_coref_chain(sNoun2)
        sNoun1_head = tmp1.split(termSeparator)[0]  # tom <- tom_he Block: If
        sNoun2_head = tmp2.split(termSeparator)[0]
        #if sRelation in GM.mapping:
        #    continue
        for tNoun1,tRelation,tNoun2 in tgtEdges:
            tmp3 = reorganise_coref_chain(sNoun1)  # he_tom -> tom_he
            tmp4 = reorganise_coref_chain(sNoun2)
            tNoun1_head = tmp3.split(termSeparator)[0]
            tNoun2_head = tmp4.split(termSeparator)[0]
            sNoun1_map = returnMappedConcept(sNoun1_head)
            sNoun2_map = returnMappedConcept(sNoun2_head)
            if ( ((sNoun1_map == tNoun1_head) and (sNoun2_map == tNoun2_head)) or
                 ((sNoun2_map == tNoun1_head) and (sNoun1_map == tNoun2_head)) ):
            #if ( ((n1Map == tNoun1) and (n2Map == tNoun2)) or                         # Identicality node
            #    ((n2Map == tNoun2) and (n1Map == tNoun1)) ):
                if sRelation not in GM.mapping.keys():
                    GM.mapping[sRelation] = tRelation
                    mappedpairs.append(sRelation + arrow + tRelation + "\v")
                    relationMapping[sRelation] = tRelation
                    print(" VV", sRelation," -", tRelation, end="  ")
                    break
            elif ( ((sNoun1_head == tNoun1_head) and (sNoun2_head == tNoun2_head)) or    # Identical head-words
                   ((sNoun1_head == tNoun2_head) and (sNoun2_head == tNoun1_head)) ):
                print("ok", end=" ")
                if sRelation not in GM.mapping.keys():
                    GM.mapping[sRelation] = tRelation
                    mappedpairs.append(sRelation + arrow + tRelation + "\v")
                    relationMapping[sRelation] = tRelation
                    print(" VV", sRelation," -", tRelation, end="  ")

def returnMappedConcept(s_con):
    global GM
    global termSeparator
    for thingy in GM.mapping.keys():
        if s_con in thingy.split(termSeparator)[0]:
            return GM.mapping[thingy]
    return False

#####################
# Open output files
#####################


def CSV():
    return 
    print("\nIn CSV() ", end="")
    global sourceGraph
    global targetGraph
    global CSVPath
    global CSVName
    global inferenceList 
    with open(CSVPath + CSVName, 'a') as mappingFileAppendingData:   # Hmmm :-( Mapping results read from file
        with open(CSVPath + CSVName, 'r') as mappingFileReadingData: # WHY read from mappingFileReadingData?
            LCSL = ""  # LCS Lin
            LCSW = ""  # LCS WuP
            verb1 = ""
            verb2 = ""
            max_value= 0.0     # Lin similarity 
            max_value2 = 0.0   # WuP similarity 
            mappingDataSourceItems = []
            mappingDataTargetItems = []
            subset1 = "none"
            subset2 = "none"
            rr = list(sourceGraph.nodes)
            rr2 = list(targetGraph.nodes)
            sourceGraphEdges=nx.get_edge_attributes(sourceGraph,'label') # Verb from sourceGraph
            targetGraphEdges=nx.get_edge_attributes(targetGraph,'label') # Verb from targetGraph
            x = 0
            y = 0
            d = 0
            e = 0
            
            inference = 0     # Noun/Concept metrics
            countLinZero = 0
            countWupZero = 0
            countNounList = 0
            nounLinSum = 0.0
            nounWupSum = 0.0
            countLinPerfect = 0.0
            countWupPerfect = 0.0
            averageLin = 0
            averageWup = 0

            num_target_nodes = targetGraph.number_of_nodes()  # Mapping Size
            target_nodes = targetGraph.nodes() # list or something
            target_nodes_mapped = 0
            for x in target_nodes:
                if x in GM.mapping.keys():
                    target_nodes_mapped =+ 1
            print("\nHI ", target_nodes_mapped, " of ", num_target_nodes, " nodes mapped.")
            concept_mapping_ratio = target_nodes_mapped / num_target_nodes
            
            countVerbList = 0  # Verb/Relation metrics
            countVerbLinZero = 0
            countVerbWupZero = 0
            verbsLinSum = 0.0
            verbsWupSum = 0.0
            verbLinPerfect = 0.0
            verbWupPerfect = 0.0
            averageVerbLin = 0
            averageVerbWup = 0

            AnalogicalSimilarity = 0.0
            
            LCSLlist = []
            filereader = csv.reader(mappingFileReadingData)
            fileWriter = csv.writer(mappingFileAppendingData, delimiter=',',quotechar='"', quoting=csv.QUOTE_MINIMAL,  lineterminator = '\n')
            mappingFileReadingData.readline()  # skip header
            for row in filereader:
                try:
                    mappingDataSourceItems.append(row[1])   # List of Source terms
                    mappingDataTargetItems.append(row[2])   # List of Target terms
                    if vbse>3:
                        print(row[0], row[1], row[2], end="    ")
                except IndexError:
                    pass                         
            if vbse>3:
                print("  \nData re-read ", end="")   ###############################
            mappingFileReadingData.seek(1)           #### Relational Similarity ####
            try:                                     ###############################
                mappingFileReadingData.readline()  # skip header
                for map in filereader:  #cvsfile2
                    if vbse>3:
                        print( map[1], end="  ")
                    #stop()
                    for y in range(len(mappingDataSourceItems)):
                        if vbse>3:
                            print(" map[1]&friend ",map[1], mappingDataSourceItems[y], end=" ")
                        if sourceGraph.has_edge(" map[1],mappingDataSourceItems[y] ", map[1],mappingDataSourceItems[y]):       # find a Source edge
                            verb1 = sourceGraphEdges[map[1],mappingDataSourceItems[y]] #Extracts relation information between mapped terms by checking if both terms in a mapped pair have an edge relation to 
                            print(" ok ")
                            verb1 = sourceGraphEdges[(map[1],mappingDataSourceItems[y])] #Extracts relation information between mapped terms by checking if both terms in a mapped pair have an edge relation to 
                            #verb1 = (map[1],mappingDataSourceItems[y], sourceGraph)[0]
                        elif sourceGraph.has_edge(mappingDataSourceItems[y], map[1]):
                            #another mapped pair in their original graphs, and if so maps the verb/prepositional relation and performs Lin/WuP simialrity and 
                            #verb1 = sourceGraphEdges[mappingDataSourceItems[y], map[1]]          #LCS checking as normal (As our graphs are directed, we have to check if terms have a realtion both ways manually) 
                            #verb1 = sourceGraphEdges[(mappingDataSourceItems[y], map[1])]          #LCS checking as normal (As our graphs are directed, we have to check if terms have a realtion both ways manually) 
                            verb1 = returnEdgesBetweenTheseObjects(mappingDataSourceItems[y], map[1], sourceGraph)[0]
                                                         # Commutativity Test for Verb
                            #if verb1 not in commutativeVerbList:
                            #    continue
                            #    #verb1 = None
                        if vbse>3:
                            print("For now:", map[1], mappingDataSourceItems[y], verb1, end=" ")
                        #stop()  
                        if targetGraph.has_edge(map[2],mappingDataTargetItems[y]): # converse is 40 lines down
                            #verb2 = targetGraphEdges[(map[2],mappingDataTargetItems[y])]
                            verb2 = returnEdgesBetweenTheseObjects(mappingDataSourceItems[y], map[1], targetGraph)[0]
                            print("***VERB1&2", verb1, verb2, end=" ")
                            if verb1 == verb2:    # identical realtions
                                max_value = 1
                                max_value2 = 1
                                LCSW = verb1
                                LCSL = verb1
                            else:
                                syns1 = wn.synsets(verb2, pos = 'v')  # LIN verb similarity
                                syns2 = wn.synsets(verb1, pos = 'v')
                                for ss in syns1:
                                    for ss2 in syns2:
                                        d = ss.lin_similarity(ss2, semcor_ic)
                                        e = ss.wup_similarity(ss2)
                                        if d < 0.0000000001:
                                            d = 0
                                        if d > max_value:
                                            max_value = d
                                            LCSL = ss.lowest_common_hypernyms(ss2)
                                        if e > max_value2:
                                            max_value2 = e
                                            LCSW = ss.lowest_common_hypernyms(ss2)
                                        if d is None:
                                            d = 0
                                        if e is None:
                                            e = 0
                                        else :
                                            if d > max_value:
                                                max_value = d
                                            if e > max_value2:
                                                max_value2 = e
                                if max_value == 0:
                                        LCSL = "none"  # LCS Lin
                                if max_value2 == 0:
                                        LCSW = "none"  # LCS WuP
                                if max_value == 1:
                                        LCSL = verb1                                           
                                if max_value2 == 1:
                                        LCSW = verb1

                            if (verb1 in GM.mapping) and (GM.mapping[verb1] == verb2):  # 29 Oct <<<<<<<<<<<<<<<<<<<<<<<
                                    pass
                            else:
                                filewriter.writerow(['V4', verb1, verb2, max_value, max_value2,
                                                     simplifyLCSList(LCSL), simplifyLCSList(LCSW)])
                            e = 0
                            d = 0
                            max_value = 0.0
                            max_value2 = 0.0
                            
                        elif (targetGraph.has_edge(mappingDataTargetItems[y],map[2])):  # mappingDataTargetItems[y]<->x[2] 45 lines up
                            #verb2 = targetGraphEdges[(mappingDataTargetItems[y],map[2])]
                            verb2 = returnEdgesBetweenTheseObjects(mappingDataSourceItems[y], map[1], targetGraph)[0]
                            print("***VERB2", verb2)
                            if verb2 not in commutativeVerbList:
                                continue
                            if verb1 == verb2:
                                max_value = 1
                                max_value2 = 1
                                LCSW = verb1
                                LCSL = verb1
                            else:
                                syns1 = wn.synsets(verb2, pos = 'v')
                                syns2 = wn.synsets(verb1, pos = 'v')
                                for ss in syns1:
                                    for ss2 in syns2:
                                        d = ss.lin_similarity(ss2, semcor_ic)
                                        e = ss.wup_similarity(ss2)
                                        if d < 0.0000000001:
                                            d = 0
                                        if d > max_value:
                                            max_value = d
                                            LCSL = ss.lowest_common_hypernyms(ss2)
                                        if e > max_value2:
                                            max_value2 = e
                                            LCSW = ss.lowest_common_hypernyms(ss2)
                                        if d is None:
                                            d = 0
                                        if e is None:
                                            e = 0

                                        else :
                                            if d > max_value:
                                                max_value = d
                                            if e > max_value2:
                                                max_value2 = e
                                if max_value == 0:
                                        LCSL = "none"
                                if max_value2 == 0:
                                        LCSW = "none"
                                if max_value == 1:
                                        LCSL = verb1
                                if max_value2 == 1:
                                        LCSW = verb1
                                filewriter.writerow(['V5', verb1, verb2, max_value, max_value2,
                                                     simplifyLCSList(LCSL), simplifyLCSList(LCSW)])
                            e = 0
                            d = 0
                            max_value = 0.0
                            max_value2 = 0.0
            except IndexError:
                pass

            try:
                mappingFileReadingData.seek(0) 
                #next(filereader)
                #Calculates average Lin/WuP simialrity for nouns   *** RE-READ ANALOGY FILE
                print("RE-re reading file ", end="  ")
                for line in filereader:
                    if vbse>3:
                        print(1, end="")
                    if (line[0] == 'Type'):  #? Skip the Header of the file
                        print("...CSV()...", end="")
                    elif (line[0][0][0] == 'N'): 
                        nounLinSum += float(line[3])
                        nounWupSum += float(line[4])
                        countNounList +=1
                        if (float(line[3]) == 1):
                            countLinPerfect += 1
                        elif (float(line[3]) == 0):
                            countLinZero += 1
                        if (float(line[4]) == 1):
                            countWupPerfect += 1
                        elif (float(line[4]) == 0):
                            countWupZero +=1
                            
                    elif(line[0][0] == 'V'):
                        verbsLinSum += float(line[3])
                        verbsWupSum += float(line[4])
                        countVerbList += 1
                        if (float(line[3]) == 1):
                            verbLinPerfect +=1
                        elif (float(line[3]) == 0):
                            countVerbLinZero += 1
                        if (float(line[4]) == 1):
                            verbWupPerfect +=1
                        elif (float(line[4]) == 0):
                            countVerbWupZero +=1
            except IndexError:
                pass
            
# GROUNDED INFERENCES
            #generateCWSGInferences(sourceGraph, targetGraph)
            for a,r,b in inferenceList:
                filewriter.writerow(["Inference", a, r, b])
            #stop()          
#Write Merics
            filewriter.writerow(['#Noun Lin==0', countLinZero, 'of', countNounList])
            filewriter.writerow(['#Noun WuP==0', countWupZero, 'of', countNounList])
            if countNounList>0:
                averageLin = nounLinSum/countNounList
                averageWup = nounWupSum/countNounList
            else:
                averageLin = 0
                averageWup = 0 
            filewriter.writerow(['Average Noun Lin ', averageLin])
            filewriter.writerow(['Average Noun Wup ', averageWup])
            filewriter.writerow(['#Noun Lin== 1', countLinPerfect, 'of', countNounList])
            filewriter.writerow(['#Noun WuP== 1', countWupPerfect, 'of', countNounList])

            inferences  = len(inferenceList)
            if inferences > 0:
                print("#### Inferences =", inferences)
            print("  countVerbList=", countVerbList)
            if countVerbList>0:
                if (inferences == 0):
                    AnalogicalSimilarity = (0.5*(verbsWupSum/countVerbList) + 0.2*(nounWupSum/countNounList))
                    print("0 Infs, verbsWupSum countVerbList, nounWupSum: ",
                           round(verbsWupSum,3), round(countVerbList,3), round(nounWupSum,3) )
                else:
                    AnalogicalSimilarity = (0.5*(verbsWupSum/countVerbList) + 0.2*(1-(nounWupSum/countVerbList))
                                            + 0.3 * (math.exp(-1/inferences)))
                print("verbsWupSum countVerbList ", verbsWupSum, countVerbList )

                filewriter.writerow(['#Verb Lin==0', countVerbLinZero, 'of', countVerbList])
                filewriter.writerow(['#Verb Wup==0', countVerbWupZero, 'of', countVerbList])
                if countVerbList>0:
                    averageVerbLin = (verbsLinSum/countVerbList)
                    averageVerbWup = (verbsWupSum/countVerbList)

                else:
                    averageVerbLin = 0
                    averageVerbWup = 0
                filewriter.writerow(['Average Verb Lin ', averageVerbLin])
                filewriter.writerow(['Average Verb Wup ', averageVerbWup])
                filewriter.writerow(['#Verb Lin== 1', verbLinPerfect, 'of', countVerbList])
                filewriter.writerow(['#Verb WuP== 1', verbWupPerfect, 'of', countVerbList])
                filewriter.writerow(['Analogical Similarity', AnalogicalSimilarity])
                print("#b Inference =", inferences, " ", inferenceList)
                print("ANALOGICAL Similarity", AnalogicalSimilarity, "   for",
                      sourceGraph.graph['Graphid'], targetGraph.graph['Graphid'])
                
            print(targetGraph.graph['Graphid'], sourceGraph.graph['Graphid'], 
                     countLinZero, countWupZero, averageLin, averageWup, countLinPerfect, countWupPerfect,
                     countVerbLinZero, countVerbWupZero, averageVerbLin, averageVerbWup, verbLinPerfect, verbWupPerfect, 
                     inferences, countNounList, countVerbList, AnalogicalSimilarity)       
            writeSummaryFileData(targetGraph.graph['Graphid'], sourceGraph.graph['Graphid'], 
                     countLinZero, countWupZero, averageLin, averageWup, countLinPerfect, countWupPerfect,
                     countVerbLinZero, countVerbWupZero, averageVerbLin, averageVerbWup, verbLinPerfect, verbWupPerfect, 
                     inferences, countNounList, countVerbList, AnalogicalSimilarity) #mappedEdges
            print("Summary: ", round(AnalogicalSimilarity,5), end="")
            mappingFileAppendingData.close()
            mappingFileReadingData.close()
            #stop()
#End CSV()



def generateCWSGInferences(tgtGraph, srcGrf): # generateCWSGInferences(sourceGraph, targetGraph)
    global GM
    global inferenceList
    #inverseDic = {}
    #print("\n###INFERENCE ", end="")
    srcEdges = returnEdgesAsList(srcGrf)
    for (subj, obj, reln) in srcEdges:
        #print("CWSG", end=" ")
        s=r=o=0
        if subj in GM.mapping:
            s=1
        if obj in GM.mapping:
            o=1
        if ( (reln in GM.mapping) or (reln in ['assert']) ):  # Aris
            r=1
        if reln in ['assert']:
            print("ASSERTfound", end="")
        subjMap = GM.mapping.get(subj)
        relnMap = GM.mapping.get(reln)
        objMap = GM.mapping.get(obj)
        if not (predExists(subjMap,relnMap,objMap, tgtGraph)): #generate inference
            if (s + r + o) == 2:
                if vbse>3:
                    print(" Score", s+r+o, end=" ")
                #print(" not exists ", relnMap, reln, end="")
                if subjMap == None:   # Generate transferrable symbol
                    subjMap = subj
                    #GM.mapping[subj] = subjMap  # should we add them before evaluating the analogy
                if objMap == None:  
                    objMap = obj
                    #GM.mapping[obj] = objMap
                if relnMap == None:
                    relnMap = reln
                    #GM.mapping[reln] = relnMap
                print(" #INFER(",subj, reln, obj, " => ", subjMap,", ", relnMap,", ", objMap,end=")   ")
                inferenceList = inferenceList + [[subjMap, relnMap, objMap]]
    print("\n", end="")


def writeSummaryFileData(fileName1, fileName2,a,b,c,d,e,f,g,h,i,j,l,m,n,o,p,q): #18 params
    global CSVsummaryFileName
    with open(CSVsummaryFileName, "a+") as csvSummaryFileHandle:
        summaryFilewriter = csv.writer(csvSummaryFileHandle, delimiter=',',
                           quotechar='"', quoting=csv.QUOTE_MINIMAL,  lineterminator = '\n')
        summaryFilewriter.writerow([fileName1,fileName2, a,b,c,d,e,f,g,h,i,j,l,m,n,o,p,q])
    #csvSumryFil.close()


################################################################
################ Run Multiple Analogies ########################
################################################################


def resetAnalogyMetrics():
    global inference
    inference = 0
    global inferenceList
    inferenceList =[]
    global LCSLlist
    LCSLlist = []
    global mappedpairs 
    mappedpairs = []
    global GM
    GM = isomorphvf2CB.MultiDiGraphMatcher(targetGraph, targetGraph)
    #GM = isomorphvf2CB.DiGraphMatcher(targetGraph, targetGraph)
    #global sourceGraph
    global relationMapping
    relationMapping.clear()
    global numberOfTimeOuts
    numberOfTimeOuts = 0
 

def blendWithAllSources(targetFile):  # blendAllSources(targetFile)
    global all_csv_files
    #global CSVPath
    global csvfile
    global targetGraph
    global sourceGraph
    global analogyFileName
    global LCSLlist
    global mappedpairs   
    global nextSourceFile
    global csvSummaryFileHandle
    global analogyCounter
    global max_graph_size
    print("\nExploring Target::", targetFile)
    targetGraph = build_graph_from_csv(targetFile).copy()
    targetGraph.graph['Graphid'] = targetFile
    p1 = targetFile.rfind(".") # filetypeFilter
    if targetGraph.number_of_edges() > max_graph_size:
        prune_peripheral_nodes(targetGraph)
    for nextSourceFile in all_csv_files:
        if nextSourceFile == targetFile: # skip self comparison
            continue
        p2 = nextSourceFile.rfind(".")
        print("\n==================", end=" ")
        print("#",mode,"   ",  targetFile[0:p1],"  <- ", nextSourceFile[0:p2], "=======")
        analogyFileName = targetFile[0:p1] + "__" + nextSourceFile[0:p2] + ".csv"
        resetAnalogyMetrics()
        temp_graph2.clear()
        sourceGraph = build_graph_from_csv(nextSourceFile).copy()
        sourceGraph.graph['Graphid'] = nextSourceFile
        if sourceGraph.number_of_edges() > max_graph_size:
            prune_peripheral_nodes(sourceGraph)
        show_graph_in_FF(sourceGraph)
        #DFS.mappingTest(targetGraph, sourceGraph)
        develop_analogy(targetGraph, sourceGraph)
        print("Source map:", returnMappingRatio(sourceGraph),
              "\tTarget map:", returnMappingRatio(targetGraph))
        if analogyCounter >= run_Limit:
            sys.exit()
        analogyCounter +=1                 #analogyFileName.close()
        #show_graph_in_FF(sourceGraph)      #anyKey = input()
        #stop()


def blendAllFiles():
    global all_csv_files
    global analogyCounter
    global CSVPath
    analogyCounter = 1
    if not os.path.exists(CSVPath):
        os.makedirs(CSVPath)
    writeSummaryFileData("TARGET", "SOURCE", "#Lin=0", "#WuP=0", "LinAvg", "WuPAvg", "#Lin=1", "WuP=1",
                         "#Lin=0", "#WuP=0", "LinAvg", "WuPAvg", "#Lin=1", "WuP=1",
                         "Infs", "#MapCon", "MapRels", "AnaSim")
    for next_target_file in all_csv_files:
        print("================",next_target_file,"================\n")
        if True:
            targetGraph = build_graph_from_csv(next_target_file)  # for Display-only usage
            targetGraph.graph['Graphid'] = next_target_file
            show_graph_in_FF(targetGraph)
        blendWithAllSources(next_target_file)
        #crashAfterOneTarget()
    print("\n", analogyCounter, "analogies explored")



def prune_peripheral_nodes(grf):
    global max_graph_size
    cntr = 0
    print("Graph reduced from ", grf.size(), end="-> ")
    limit = grf.number_of_edges() - max_graph_size
    while grf.number_of_edges() > max_graph_size:
        degree_sequence = sorted([(d, n) for n, d in grf.degree()])
        for degr, lab in degree_sequence:
            print("dud ", end="")
            grf.remove_node(lab)  # possibly Many edges deleted
            cntr +=1
            if (cntr>=limit) or (cntr%5 ==0): # delete nodes in batches of 5
                break
    print(grf.number_of_edges(), end="   ")


#######################################################################
###########################   GUI    ##################################
#######################################################################


def exitApp():
    window.destroy()
    sys.exit()

def retrieve_input():
    print("getting input")
    targetText4 = Entry(window)
    #targetText4.pack()
    targetText4.delete(0, END)
    targetText4.insert(INSERT, "Type text here")
    #sourceText5.delete(0, END)
    inputValue1=targetText4.get("1.0", "end-1c")
    #inputValue2=sourceText5.get("1.0","end-1c")
    #targetText4.set("Mary had a little lamb\nHer Fleece was white as snow.\n")
    #print("inputValue", inputValue)
    #execfile('Text2ROS.py')
    Text2ROS.processAllTextFiles()
    Text2ROS.processDocument(inputValue1)
    Text2ROS.generateOutputCSV("Antonet01 - Four-Canals-Carocci.txt.csv")
    Text2ROS.processAllTextFiles()
    Text2ROS.processDocument(inputValue2)
    Text2ROS.generateOutputCSV("Antonet01 - Lake-Complete-Source-Carocci.txt.csv")
    #targetText4.insert(INSERT, list(sourceGraph.nodes))
    #sourceText5.insert(INSERT, list(targetGraph.nodes))
    return


def ok():
    global sourceGraph
    global targetGraph
    with open(CSVPath + CSVName, 'w+') as analogyCsvfile:
        filewriter = csv.writer(analogyCsvfile, delimiter=',',
                            quotechar='|', quoting=csv.QUOTE_MINIMAL,  lineterminator = '\n')
        filewriter.writerow(['Type', 'Noun1','Noun2', 'Lin', 'Wup', 'LCS Lin', 'LCS Wup'])
    p1 = sourceGraph.graph['Graphid'].find(".")
    p2 = targetGraph.graph['Graphid'].find(".")
    print("####################################")
    print("### ", sourceGraph.graph['Graphid'][0:p1], "  <->", targetGraph.graph['Graphid'][0:p2], " ##")
    print("####################################")

    printEdges(sourceGraph)
    targetText4.insert(INSERT, returnEdges(sourceGraph))     # list(sourceGraph.nodes)
    sourceText5.insert(INSERT, returnEdges(targetGraph))
    develop_analogy(targetGraph, sourceGraph)
    global LCSLlist
    global mappedpairs
    #addRelationsToMapping(sourceGraph, targetGraph)
    CSV()
    analogyCsvfile.close()
    lcsText1.insert(INSERT, LCSLlist)
    inferencesText2.insert(INSERT, inferenceList)
    mappingText3.insert(INSERT, mappedpairs)

def temp():
    window = tkinter.Tk()
    window.title("Cre8blend - GUI")
    lcsText1 = Text(window, height=15, width=30)
    targetLabel = Label(window, text="Input 1", bg="white", fg="black")  # .grid(row=0, sticky=E)
    sourceLabel = Label(window, text="Input 2", bg="white", fg="black")
    L = Label(window, text="Shared - Lowest Common Subsumer", bg="white", fg="black")
    a = Button(window, text="Run Single Analogy", command=ok)  ###
    # b = Button(window, text = "Map ALL sources",command = ok)  ###
    w = Label(window, text="Mapping", bg="white", fg="black")
    mappingText3 = Text(window, height=15, width=35)
    a.pack(expand=True)
    L.pack(expand=True)
    lcsText1.pack(side=TOP)
    scrollbar = Scrollbar(window)
    scrollbar.pack(side=LEFT, fill=Y)
    scrollbar2 = Scrollbar(window)
    scrollbar2.pack(side=RIGHT, fill=Y)
    targetText4 = Text(window, height=20, width=40)
    sourceText5 = Text(window, height=25, width=40)
    targetLabel.pack(side=LEFT, expand=True)
    targetText4.pack(side=LEFT, expand=True)
    sourceLabel.pack(side=RIGHT, expand=True)
    sourceText5.pack(side=RIGHT, expand=True)
    scrollbar.config(command=targetText4.yview)
    scrollbar2.config(command=sourceText5.yview)
    buttonCommit = Button(window, height=1, width=10, text="Make Graph",  ### input one
                      command=lambda: retrieve_input())
    buttonCommit.pack()
    targetText4.config(yscrollcommand=scrollbar.set)
    sourceText5.config(yscrollcommand=scrollbar2.set)
    w.pack()
    mappingText3.pack(expand=True)
    l = Label(window, text="Inference", bg="white", fg="black")
    l.pack(expand=True)
    inferencesText2 = Text(window, height=15, width=20)
    inferencesText2.pack(side = BOTTOM, expand=True)

    #Button(window, text="Quit", bg="white", fg="black", command=exitApp).pack()
    Button(window, text="Quit", bg="white", fg="black", command=exitApp).pack()

#myString = StringVar()
#entry1 = Entry(window, textVariable = myString)
    window.mainloop()


#print(time.ctime())

#CN Elaboration
# CN_file -> CN_dict

def loadConceptNet(CNfileNam):
    #with open(CNfile, 'r') as csvfile:
    #print("in CN", end=" ")
    #csvreader = csv.reader(CNfileNam, delimiter=',', quotechar='|')
    reader = csv.reader(open(CNfileNam, 'r'))  #, errors='replace')
    for row in reader:
        noun1, noun2, verb = row
        try:
            CN_dict[noun1].append((verb, noun2))
            #print(CN_dict[noun1])
        except KeyError:
            CN_dict[noun1] = [(verb,noun2)]

#loadConceptNet(CN_file)


def checkCNConnection(noun1,noun2):
    # Returns true if CN_dictionary has noun1 as key & value (any verb, noun2)
    r = False
    try:
        for pair in CN_dict[noun1]:
            if not r:
                r = noun2 in pair[1]
            #print(pair, r, end="   ")
    except KeyError:
        r = False
    return r
# checkCNConnection('four','4')   checkCNConnection('four','rowing')

def getCNConnections(noun1,noun2):
    # Returns a list of verbs that connect noun1 and noun2 in the ConceptNet data
    connections = []
    for pair in CN_dict[noun1]:
        if noun2 == pair[1]:
            connections.append(pair[0])
    return connections
# getCNConnections('four','4')


def getNodes(graph):
    tempList = []
    for node in Graph_dictionary:
        tempList.append(node)
        for pair in graph[node]:
            tempList.append(pair[1])
    nodes = list(set(tempList))
    return nodes
# getNodes(sourceGraph)


def findMissingConnections(graph):
    # Takes pairs of nodes and uses the checkCNConnection to see if a connection should be added to the graph
    #nodes = getNodes(graph)
    nodes = sourceGraph.nodes()
    # list(graph) is used here to avoid runtime error: dictionary changed size during iteration
    for n1 in nodes:
        for n2 in nodes:
            if n1 != n2:
                if checkCNConnection(n1, n2):
                    for verb in getCNConnections(n1, n2):
                        addConnection(n1, n2, verb)
                if checkCNConnection(n2, n1):
                    for verb in getCNConnections(n2, n1):
                        addConnection(n2, n1, verb)
                        # Checks connection both directions as graph is directed


def addConnection(noun1, noun2, verb):
    # Adds the connection noun1 -> verb -> noun2
    if noun1 in Graph_dictionary:
        if (verb, noun2) not in Graph_dictionary[noun1]:
            Graph_dictionary[noun1].append((verb, noun2))
            print("added-a " + noun1 + " " + verb + " " + noun2)
    else:
        Graph_dictionary[noun1] = [(verb, noun2)]
        print("added-b " + noun1 + " " + verb + " " + noun2)
        # Prints the keys/values of the newly added connection
        

def findNewNodes(graph):
    # Creates a list containing all the current nodes in our graph
    nodes = getNodes(graph)
    # Iterates over groups of three nodes and checks if they share a common connected node using shareCommonNode
    # Change this to four nodes if you wish to increase the requirement
    for n1 in nodes:
        for n2 in nodes:
            for n3 in nodes:
                if n1 != n2 and n2 != n3 and n1 != n3:
                    toAdd0 = shareCommonNode(n1, n2, n3)
                    if toAdd0 != []:
                        # If all three nodes share a common connected node
                        # That node is added along with the relevant connection
                        for node in toAdd0:
                            for verb in getCNConnections(n1, node):
                                if verb not in BannedEdges:
                                    addConnection(n1, node, verb)
                            for verb in getCNConnections(n2, node):
                                if verb not in BannedEdges:
                                    addConnection(n2, node, verb)
                            for verb in getCNConnections(n3, node):
                                if verb not in BannedEdges:
                                    addConnection(n3, node, verb)
    print('')
    for key in CN_dictionary:
        toAdd1 = []
        for pair in CN_dictionary[key]:
            if pair[1] in nodes:
                toAdd1.append(pair[1])
        if len(toAdd1) >= 3:
            # This enforces the restriction of three current nodes, edit if you wish to change the requirement
            for node in toAdd1:
                for verb in getCNConnections(key, node):
                    if verb not in BannedEdges:
                        addConnection(key, node, verb)

def t():
    findMissingConnections(sourceGraph)

#######################################################################################################

#blendAllFiles()


def call_DFS():
    #import DFS
    print()
    nextTargetFile1 = all_csv_files[0]
    temp_graph1 = nx.MultiDiGraph()
    temp_graph1 = build_graph_from_csv(nextTargetFile1)
    nextTargetFile2 = all_csv_files[3]
    print("\nall_csv_files[3]", all_csv_files[3])
    temp_graph2 = nx.MultiDiGraph()
    temp_graph2 = build_graph_from_csv(nextTargetFile2)
    DFS.mappingTest(temp_graph1, temp_graph2)
    print("================End Mapping Test=================")

#import DFS

def testDFS():
    global all_csv_files
    global analogyCounter
    global CSVPath
    analogyCounter = 1
    if not os.path.exists(CSVPath):
        os.makedirs(CSVPath)
    writeSummaryFileData("TARGET", "SOURCE", "#Lin=0", "#WuP=0", "LinAvg", "WuPAvg", "#Lin=1", "WuP=1",
                         "#Lin=0", "#WuP=0", "LinAvg", "WuPAvg", "#Lin=1", "WuP=1",
                         "Infs", "#MapCon", "MapRels", "AnaSim")
    for nextTarget in all_csv_files:
        print("\n================",nextTarget,"================ ")
        targetGraph = build_graph_from_csv(nextTarget)  # for Display-only usage
        targetGraph.graph['Graphid'] = nextTarget
        show_graph_in_FF(targetGraph)
        sourceGraph =  build_graph_from_csv(all_csv_files[2])
        #print("XXXX", targetGraph.nodes(), sourceGraph.nodes())
        show_graph_in_FF(sourceGraph)
        DFS.mappingTest(targetGraph, sourceGraph) #Deterministic Depth First Search DFS
        stop()
    print("\n", analogyCounter, "analogies explored")


blendAllFiles()