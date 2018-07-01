import json
import logging
from pprint import pprint

import requests
import xmltodict
from requests.auth import HTTPBasicAuth, HTTPDigestAuth

from src.utils.errors import BlupointError
from run import iha_queue, dha_queue, aa_queue, reuters_queue

logger = logging.getLogger('contents')


def get_contents_from_iha(agency, agency_config):
    url = agency_config['input_url'] + '&{}={}&{}={}'.format(
        agency['auth_credential_parameters']['username'],
        agency_config['username'],
        agency['auth_credential_parameters']['password'],
        agency_config['password']
    )

    response = requests.get(url)
    if response.status_code != 200:
        raise BlupointError(
            err_msg="Agency Rss did not return 200",
            err_code="errors.InvalidUsage",
            status_code=response.status_code
        )

    o = xmltodict.parse(response.text)
    items = o['rss']['channel']['item']
    logger.info("total content count from iha: <{}>".format(len(items)))

    return items


def get_contents_from_aa(agency, agency_config):
    url = agency_config['input_url'] + '/abone/search'

    data = {
        'end_data': 'NOW',
        'filter_language': 1
    }

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36'
    }

    response = requests.post(url, data=data, headers=headers,
                             auth=HTTPBasicAuth(agency_config['username'], agency_config['password']))

    if response.status_code != 200:
        raise BlupointError(
            err_msg="Agency rss did not return 200",
            err_code="errors.InvalidUsage",
            status_code=response.status_code
        )

    feeds_json = json.loads(response.text)
    items = feeds_json['data']['result']

    text_news = []

    for item in items:
        if item['type'] == 'text':
            text_news.append(item)

    news = []
    i = 0
    for item in text_news:
        detail_url = agency_config['input_url'] + '/abone/document/' + item['id'] + '/newsml29'
        response = requests.get(detail_url, headers=headers,
                                auth=HTTPBasicAuth(agency_config['username'], agency_config['password']))

        if response.status_code != 200:
            i += 1
            continue

        logger.info('response item id: <{}>'.format(item['id']))
        o = json.loads(json.dumps(xmltodict.parse(response.text)))
        o = o['newsMessage']['itemSet']['newsItem']['contentSet']['inlineXML']['nitf']['body']
        r = {
            'item_id': item['id'],
            'headline': o['body.head']['headline']['hl1'],
            'byline': o['body.head']['byline']['byttl'],
            'abstract': o['body.head']['abstract'],
            'content': o['body.content']
        }

        news.append(r)

    logger.info("total content count from aa: <{}>".format(len(text_news)))
    logger.info("received text news: {}".format(len(text_news) - i))
    return news


def get_contents_from_dha(agency_config, agency):
    pass


def get_contents_from_reuters(agency, agency_config):
    url = agency_config['input_url'] + '&limit=10&maxAge=2h'
    response = requests.post(url, auth=HTTPDigestAuth(agency_config['username'], agency_config['password']))

    if response.status_code != 200:
        raise BlupointError(
            err_code="errors.InvalidUsage",
            err_msg="Agency news response is not 200",
            status_code=response.status_code
        )

    o = json.loads(json.dumps(xmltodict.parse(response.text)))
    news = o['rss']['channel']['item']
    return news


def set_iha_queue(content):
    if content['HaberKodu'] not in iha_queue:
        iha_queue.append(content['HaberKodu'])
    else:
        return False

    return True


def set_dha_queue(content):
    pass


def set_aa_queue(content):
    if content['item_id'] not in aa_queue:
        iha_queue.append(content['item_id'])
    else:
        return False

    return True


def set_reuters_queue(content):
    if content['link'] not in iha_queue:
        iha_queue.append(content['link'])
    else:
        return False

    return True
