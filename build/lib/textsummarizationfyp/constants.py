import os

# Project Paths
ROOT = os.path.dirname(os.path.abspath(__file__))

# Document Paths
DOCS = os.path.join(ROOT, 'docs')
TEXT = os.path.join(DOCS, 'text')
GRAPHS = os.path.join(DOCS, 'csv')

# covid_convert.py
json_path = os.path.join(DOCS, 'json')
doc_path = os.path.join(DOCS, 'text')
summarys = os.path.join(DOCS, 'summarys')
# Doc Sets
PRONOUNS = ["all", "another", "any", "anybody", "anyone", "anything", "as", "aught", "both", "each",
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
