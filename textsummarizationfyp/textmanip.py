import nltk
from nltk import sent_tokenize, word_tokenize
import os
import constants as const
nltk.download('punkt')
nltk.download('averaged_perceptron_tagger')


def partOfSpeech(text):
    tokens = nltk.word_tokenize(text)
    tag = nltk.pos_tag(tokens)
    return tag


def getSentences(text_file):
    path = os.path.join(const.DOCS, text_file)
    file = open(path, "r")
    filedata = file.read()
    sentences = sent_tokenize(filedata)
    tokenized_sentences = [word_tokenize(sent) for sent in sentences]
    return tokenized_sentences


def getSentences2(text):
    sentences = sent_tokenize(text)
    tokenized_sentences = [word_tokenize(sent) for sent in sentences]
    return tokenized_sentences


def getAbstract(json_object):
    abstract = ""
    for i in range(len(json_object['abstract'])):
        abstract += json_object['abstract'][i]['text']
    return abstract


def getBody(json_object):
    body = ""
    for i in range(len(json_object['body_text'])):
        body += json_object['body_text'][i]['text']
    return body


def json2txt(json_object, name):
    # Get text to write
    abstract = getAbstract(json_object)
    body = getBody(json_object)
    doc_text = abstract + "\n" + body
    # Open file
    path = os.path.join(const.DOCS, 'text', name)
    if (os.path.exists(path)):
        print('Text document already exists, skipping')
    else:
        f = open(path, 'w+', encoding='utf8')
        f.write(doc_text)
        f.close()
