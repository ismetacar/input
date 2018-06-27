import json

import xmltodict


def parse_iha_response(string):
    o = xmltodict.parse(string)
    o = o['rss']['channel']['item'][0]
    return json.dumps(o)


def parse_aa_response(string):
    o = xmltodict.parse(string)
    o = o['rss']['channel']['item'][0]
    return json.dumps(o)


def prepare_iha_url(agency, body):
    url = body['input_url'] + '&{}={}&{}={}'.format(
        agency['auth_credential_parameters']['username'],
        body['username'],
        agency['auth_credential_parameters']['password'],
        body['password']
    )

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36'
    }

    return url, headers


def prepare_aa_url(agency, body):
    url = body['input_url']
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36'
    }

    return url, headers


def prepare_dha_url(agency, body):
    pass


def prepare_reuters_url(agency, body):
    pass
