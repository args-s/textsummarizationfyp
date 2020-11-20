import sys
import json
import os
import constants as const


def run():
    path = os.path.join(
        const.DOCS, '000e43590fdd2e011cfadaa14e6c14f318d11bbb.json')
    with open(path) as x:
        data = json.load(x)

    # Build Abstract of String
    abstract_raw = ""

    for i in range(len(data['abstract'])):
        abstract_raw += data['abstract'][i]['text']

    # Parse Abstract String
