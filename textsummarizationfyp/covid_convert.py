# Read all files in a directory and convert to txt
# Total number: 2328
# Number converted: 428
# Issue I think title is too long
'''
obj[abstract][text]
obj[body].text ???
'''
import os
import json

source_path = "C:\\Users\\killi\\Documents\\pdf_json"
dest_path = "C:\\Users\\killi\\Documents\\covid_text"
missing = list()
os.chdir(source_path)

pita_chars = [':', ';', "\\", '/', ".",
              ',', '%', '{', '}', '[', ']', '#', '\"', '?', '(', ')', '-']

print(len(os.listdir(source_path)))
print(len(os.listdir(dest_path)))
# Iterate through each file in directory and convert all json files to txt


def check_diff():
    for file in os.listdir(source_path):
        check = file.replace(".json", ".txt")

        if not(os.path.exists(os.path.join(dest_path, check))):
            missing.append(file)

    print(missing)


def pitac_check(string):
    for pitac in pita_chars:
        string = string.replace(pitac, '')
    # print(string)
    return(string)


def json2txt():
    for file in os.listdir():
        # Go through all files
        filepath = "{}\\{}".format(source_path, file)

        # Open file and get title for filename
        with open(filepath,) as f:
            # Intialise paths and new filenames. If no title, 1st 5 chars
            print("Now Looking at {}".format(file))
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
                dest_path, title_file)

            abstract_path = "{}\\{}".format(
                dest_path, abs_file)
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
