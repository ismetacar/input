import json
import requests
import xmltodict
from flask import session
from requests.auth import HTTPBasicAuth, HTTPDigestAuth

from src.utils.errors import BlupointError


def parse_iha_response(string):
    o = xmltodict.parse(string)
    o = o['rss']['channel']['item'][0]
    return o


def parse_aa_response(string):
    o = json.loads(json.dumps(xmltodict.parse(string)))
    o = o['newsMessage']['itemSet']['newsItem']
    r = {
        'headline': o['contentSet']['inlineXML']['nitf']['body']['body.head']['headline']['hl1'],
        'byline': o['contentSet']['inlineXML']['nitf']['body']['body.head']['byline']['byttl'],
        'abstract': o['contentSet']['inlineXML']['nitf']['body']['body.head']['abstract'],
        'content': o['contentSet']['inlineXML']['nitf']['body']['body.content'],
        'images': o['itemMeta'].get('link', [])
    }

    return r


def parse_dha_response(string):
    o = json.loads(json.dumps(xmltodict.parse(string)))
    o = o['rss']['channel']['item'][0]
    return o


def parse_reuters_response(string):
    o = json.loads(json.dumps(xmltodict.parse(string)))
    o = o['rss']['channel']['item'][0]
    return json.dumps(o)


def parse_ap_response(string):
    o = json.loads(json.dumps(xmltodict.parse(string)))
    o = o['feed']['entry']
    images = o['link']
    _images = []
    for image in images:
        _images.append({
            'href': image['@href']
        })

    r = {
        'item_id': o['id'],
        'title': o['title'],
        'text': o['content']['#text'],
        'byline': o['apcm:ContentMetadata']['apcm:ByLine'][0]['#text'],
        'published': o['published'],
        'updated': o['updated'],
        'keywords': o['apcm:ContentMetadata'].get('apcm:Keywords', []),
        'images': _images

    }

    return r


def make_iha_request(agency, body):
    url = body['input_url'] + '&{}={}&{}={}'.format(
        agency['auth_credential_parameters']['username'],
        body['username'],
        agency['auth_credential_parameters']['password'],
        body['password']
    )

    response = requests.get(url)
    if response.status_code != 200:
        raise BlupointError(
            err_msg="Agency Rss did not return 200",
            err_code="errors.InvalidUsage",
            status_code=response.status_code
        )

    response_json = parse_iha_response(response.text)

    images = []
    response_json = dict(response_json)
    if 'images' in response_json and response_json['images']:
        if isinstance(response_json['images']['image'], dict):
            image = {"link": response_json['images']['image']['#text']}
            images.append(image)
        elif isinstance(response_json['images']['image'], list):
            for image in response_json['images']['image']:
                image = {"link": image['#text']}
                images.append(image)

        response_json['images'] = images

    return json.dumps(response_json)


def make_aa_request(agency, body):
    url = body['input_url'] + '/abone/search'

    data = {
        'end_data': 'NOW',
        'filter_language': 1
    }

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36'
    }

    response = requests.post(url, data=data, headers=headers, auth=HTTPBasicAuth(body['username'], body['password']))

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

    for i in range(0, 10):
        detail_url = body['input_url'] + '/abone/document/' + text_news[10 - i]['id'] + '/newsml29'
        response = requests.get(detail_url, headers=headers, auth=HTTPBasicAuth(body['username'], body['password']))

        if response.status_code == 200:
            break

    response_json = parse_aa_response(response.text)

    images = []
    response_json = dict(response_json)
    if 'images' in response_json and response_json['images']:
        if isinstance(response_json['images'], dict):
            image = {
                "image_id": response_json['images']['@residref'],
                "title": response_json['images']['title']
            }
            images.append(image)
        if isinstance(response_json['images'], list):
            for image in response_json['images']:
                image = {
                    "image_id": image['@residref'],
                    "title": image['title']
                }
                images.append(image)

        response_json['images'] = images

    return json.dumps(response_json)


def make_dha_request(agency, body):
    import urllib.request
    req = urllib.request.Request(body['input_url'])
    with urllib.request.urlopen(req) as response:
        if response.status != 200:
            raise BlupointError(
                err_code="errors.InvalidUsage",
                err_msg="Agency news response is not 200",
                status_code=response.status_code
            )
        response_json = parse_dha_response(response.read().decode())
    return json.dumps(response_json)


def make_ap_request(agency, body):
    url = body['input_url'] + '/AP.Distro.Feed/GetFeed.aspx?idList=31896&idListType=products&maxItems=1'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36'
    }
    response = requests.get(url, headers=headers, auth=HTTPBasicAuth(body['username'], body['password']))

    if response.status_code != 200:
        raise BlupointError(
            err_code="errors.InvalidUsage",
            err_msg="Agency news response is not 200",
            status_code=response.status_code
        )

    response_json = parse_ap_response(response.text)

    return json.dumps(response_json)


def make_reuters_request(agency, body):
    url = body['input_url'] + '&limit=10&maxAge=2h'
    response = requests.post(url, auth=HTTPDigestAuth(body['username'], body['password']))

    if response.status_code != 200:
        raise BlupointError(
            err_code="errors.InvalidUsage",
            err_msg="Agency news response is not 200",
            status_code=response.status_code
        )

    response_json = parse_reuters_response(response.text)
    return response_json


def get_content_types_field_definitions(settings, domain_id, content_type_id):
    url = settings['management_api'] + '/domains/' + domain_id + '/content-types/' + content_type_id
    headers = {
        'Authorization': 'Bearer {}'.format(session['token']),
        'Content-Type': 'application/json'
    }

    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        raise BlupointError(
            err_msg="Error occurred while getting field_definitions for content_type: <{}> in domain: <{}>".format(
                domain_id, content_type_id),
            err_code="errors.internalError",
            status_code=response.status_code
        )

    content_type = json.loads(response.text)
    return content_type.get('field_definitions', None)
