import json
import logging

import requests
import xmltodict
from requests.auth import HTTPBasicAuth, HTTPDigestAuth

from run import iha_queue, aa_queue
from src.utils.errors import BlupointError

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
        try:
            o = json.loads(json.dumps(xmltodict.parse(response.text)))
            o = o['newsMessage']['itemSet']['newsItem']
            r = {
                'item_id': item['id'],
                'headline': o['contentSet']['inlineXML']['nitf']['body']['body.head']['headline']['hl1'],
                'byline': o['contentSet']['inlineXML']['nitf']['body']['body.head']['byline']['byttl'],
                'abstract': o['contentSet']['inlineXML']['nitf']['body']['body.head']['abstract'],
                'content': o['contentSet']['inlineXML']['nitf']['body']['body.content'],
                'images': o['itemMeta'].get('link', [])
            }
        except Exception as e:
            logger.warning(str(e))

        news.append(r)

    logger.info(
        "total content count from aa: <{}> for domain: <{}>".format(len(text_news), agency_config['domain']['_id'])
    )
    logger.info("received text news: <{}> for domain: <{}>".format(len(text_news) - i, agency_config['domain']['_id']))
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

    for new in news:
        new['images'] = new.get('media:group', {}).get('media:content', [])

    return news


def upload_image_for_iha(agency_name, content, field, asset_fields, asset_url, token, username, password):
    content = json.loads(json.dumps(content))

    multiple = False
    for asset_field in asset_fields:
        if asset_field['field_id'] == field:
            multiple = asset_field['multiple']

    if 'images' not in content:
        return [] if multiple else {}

    if not multiple:
        image = content['images'].get('image', {})
        if image:
            image_url = image['#text']
            image_name = image['@ResimKodu']
            image = image_uploader(agency_name, image_url, image_name, asset_url, token, multiple)
        return image

    images = []

    if isinstance(content['images'], dict):
        images_array = [content['images']['image']]
    elif isinstance(content['images'], list):
        images_array = content['images']
    else:
        images_array = []

    for image in images_array:
        try:
            image_url = image['#text']
            image_name = image['@ResimKodu']
            images.append(image_uploader(agency_name, image_url, image_name, asset_url, token, multiple))
        except TypeError as e:
            continue

    return images


def upload_image_for_aa(agency_name, content, field, asset_fields, asset_url, token, username, password):
    content = json.loads(json.dumps(content))
    multiple = False
    for asset_field in asset_fields:
        if asset_field['field_id'] == field:
            multiple = asset_field['multiple']

    if 'images' not in content:
        return [] if multiple else {}

    if not multiple:
        if isinstance(content['images'], dict):
            image = {
                'image_id': content['images']['@residref'],
                'image_title': content['images']['@residref']
            }

            if 'picture' in image['image_id']:
                image = image_uploader(agency_name, image['image_id'], image['image_title'],
                                       asset_url, token, multiple, username, password)
            else:
                return {}

            return image

        elif isinstance(content['images'], list):
            logger.warning(content['images'])
            image = content['images'][0] if content['images'] else {}

            if image:
                image_id = image['@residref']
                image_title = image['title']
                image = image_uploader(agency_name, image_id, image_title, asset_url, token, multiple, username, password)

            return image

    images = []
    if 'images' in content and content['images']:

        if isinstance(content['images'], dict):
            image = {
                'image_id': content['images']['@residref'],
                'image_title': content['images']['title']
            }
            images.append(image)

        elif isinstance(content['images'], list):
            for image in content['images']:
                image_id = image['@residref']
                image_title = image['@residref']

                images.append(image_uploader(
                    agency_name, image_id, image_title, asset_url, token, multiple, username, password)
                )

    return images


def upload_image_for_dha():
    pass


def upload_image_for_reuters(agency_name, content, field, asset_fields, asset_url, token, username, password):
    content = json.loads(json.dumps(content))
    multiple = False
    for asset_field in asset_fields:
        if asset_field['field_id'] == field:
            multiple = asset_field['multiple']

    if 'images' not in content:
        return [] if multiple else {}

    if not multiple:
        if isinstance(content['images'], dict):
            image = {
                'image_url': content['images']['@url'],
                'image_title': content['images']['@url'].split('tag:reuters.com,')[-1]
            }

        elif isinstance(content['images'], list):
            image = content['images'][0]
            image['image_url'] = image['@url']
            image['image_title'] = image['@url'].split('tag:reuters.com,')[-1]

        image = image_uploader(agency_name, image['image_url'], image['image_title'],
                               asset_url, token, multiple, username, password)
        return image

    images = []
    if 'images' in content and content['images']:

        if isinstance(content['images'], dict):
            image = {
                'image_url': content['images']['@url'],
                'image_title': content['images']['@url'].split('tag:reuters.com,')[-1]
            }
            images.append(image)

        elif isinstance(content['images'], list):
            for image in content['images']:
                image_url = image['@url']
                image_title = image['@url'].split('tag:reuters.com,')[-1]

                images.append(image_uploader(
                    agency_name, image_url, image_title, asset_url, token, multiple, username, password)
                )

    return images


def set_iha_queue(content):
    if content['HaberKodu'] not in iha_queue:
        iha_queue.append(content['HaberKodu'])
    else:
        return False

    return True


def set_aa_queue(content):
    logger.warning(content['item_id'])
    if content['item_id'] not in aa_queue:
        iha_queue.append(content['item_id'])
    else:
        return False

    return True


def set_dha_queue(content):
    pass


def set_reuters_queue(content):
    if content['link'] not in iha_queue:
        iha_queue.append(content['link'])
    else:
        return False

    return True


def image_uploader(agency_name, image_url, image_name, asset_url, token, multiple, username, password):
    if agency_name == 'IHA':
        r = requests.get(image_url, allow_redirects=True)
        open(image_name + '.jpg', 'wb').write(r.content)

    elif agency_name == 'AA':
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36'
        }
        url = 'http://api.aa.com.tr/abone/document/{}/web'.format(image_url)
        r = requests.get(url, auth=HTTPBasicAuth(username, password), headers=headers, allow_redirects=True)
        logger.warning(str(r.status_code) + '***status******')
        open(image_name + '.jpg', 'wb').write(r.content)

    elif agency_name == 'Reuters':
        r = requests.get(image_url, allow_redirects=True, auth=HTTPDigestAuth(username, password))
        open(image_name + '.jpg', 'wb').write(r.content)

    files = {'media': (image_name + '.jpg', open(image_name + '.jpg', 'rb'))}
    headers = {
        'Authorization': 'Bearer {}'.format(token),
    }
    response = requests.post(asset_url, files=files, headers=headers)

    if response.status_code != 200:
        return [] if multiple else {}

    response_json = json.loads(response.text)
    return response_json['data']['items'][0]
