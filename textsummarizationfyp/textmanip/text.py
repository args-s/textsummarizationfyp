import os
import textsummarizationfyp.constants as const
import nltk
from nltk import sent_tokenize, word_tokenize


def getSentences(text_file):
    path = os.path.join(const.doc_path, text_file)
    with open(path, 'r', encoding='utf8') as f:
        text = f.read()
        sentences = sent_tokenize(text)
        tokenized_sentences = [word_tokenize(sent) for sent in sentences]
        return tokenized_sentences