import nltk
from nltk import sent_tokenize, word_tokenize
import json
import os
import constants as const
# For POS Tag
nltk.download('punkt')
nltk.download('averaged_perceptron_tagger')


def getSentences(text_file):
    path = os.path.join(const.doc_path, text_file)
    with open(path, 'r', encoding='utf8') as f:
        text = f.read()
        sentences = sent_tokenize(text)
        tokenized_sentences = [word_tokenize(sent) for sent in sentences]
        return tokenized_sentences


def list_missing():
    # Check json folder for unconverted files
    missing = list()

    for file in os.listdir(const.json_path):
        flag = False
        filename = file.replace('.json', '')

        # Check for json filename in all files in text folder
        for doc_file in os.listdir(const.doc_path):
            # print('Now Searching: {} for {}'.format(doc_file, file))
            # If json name found in the current doc filename, skip to the next json file
            if filename in doc_file:
                flag = True
                break

        if flag == False:
            missing.append(file)
            print('Added ' + file)

    # Return file(s) not yet converted
    return(missing)


def pitac_check(string):
    # Check for and remove speical characters
    pita_chars = [':', ';', "\\", '/', ".",
                  ',', '%', '{', '}', '[', ']', '#', '\"', '?', '(', ')', '-', '*', '$', '&', '£', "\'"]
    for pitac in pita_chars:
        string = string.replace(pitac, '')
    return(string)


def json_convert():
    # Get files not yet converted
    unconverted = list_missing()
    if len(unconverted) == 0:
        print("All files have been converted :D")
        return

    # Go through all missing files and convert them
    for file in os.listdir(const.json_path):
        if file in unconverted:
            print("Found missing Files: {} now converting...".format(file))
            filepath = '{}\\{}'.format(const.json_path, file)

            # Open file and get title for filename
            with open(filepath,) as f:
                # Intialise paths and new filenames. If no title, 1st 5 chars
                print("Now converting {}".format(file))
                data = json.load(f)

            if data['metadata']['title'] == '':
                title = pitac_check(data['body_text'][0]['text'])

                title_file = title[0:20].replace(
                    " ", "_") + "." + file.replace('.json', '') + ".txt"
                abs_file = title[0:20].replace(
                    " ", "_") + "." + file.replace('.json', '') + ".Abs.txt"
            else:
                title_file = pitac_check(data['metadata']['title'][0:20]).replace(
                    " ", "_") + "." + file.replace('.json', '') + ".txt"
                abs_file = pitac_check(data['metadata']['title'][0:20]).replace(
                    " ", "_") + "." + file.replace('.json', '') + ".Abs.txt"

            print("Title: {}".format(title_file))
            print("Abstract File: {}".format(abs_file))
            print("File Original: {}".format(file))
            text_path = "{}\\{}".format(
                const.doc_path, title_file)

            abstract_path = "{}\\{}".format(
                const.doc_path, abs_file)
            abstract = "ABSTRACT. "
            body = "BODY. "

            # Get Abstract
            for i in data['abstract']:
                abstract += i['text']
            abstract += "\n"

            # Get Body
            for i in data['body_text']:
                body += i['text']

            doc = abstract + body
            try:
                # Write abstract to txt file
                with open(abstract_path, 'x', encoding='utf8') as t:
                    t.write(abstract)
                    t.close()
                print("Wrote Abstract to {}".format(abstract_path))
            except OSError:
                print("Error encountered with this file: {} \n".format(abstract_path))
                pass
            try:
                with open(text_path, 'x', encoding='utf8') as t:
                    t.write(doc)
                    t.close()
                print("Wrote Document to {}".format(text_path))
            except OSError:
                print("Error with this file: {} \n".format(text_path))
                pass
    print('Done.')
