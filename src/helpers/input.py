import json

import xmltodict


def parse_response_text(string):
    o = xmltodict.parse(string)
    return json.dumps(o)
