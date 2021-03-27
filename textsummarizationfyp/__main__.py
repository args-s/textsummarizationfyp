import os
import constants as const
from textsummarizationfyp import project
from textsummarizationfyp.textmanip import json_convert

if __name__ == '__main__':

    # Make
    print('Looking for unconverted files...')
    json_convert()

    # Go through graphs to create summaries
    for doc in os.listdir(const.TEXT):
        # Get 3 word summaries and sentecnes containing key phrase
        project.make_summaries(doc)
