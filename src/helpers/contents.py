import base64
import hashlib
import hmac
import json
import logging
import requests
import xmltodict
import os
from requests.auth import HTTPBasicAuth, HTTPDigestAuth
from run import iha_queue, aa_queue, ap_queue, reuters_queue, dha_queue, hha_queue
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

    o = json.loads(json.dumps(xmltodict.parse(response.text)))
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


def get_contents_from_dha(agency, agency_config):
    import urllib.request
    url = agency_config['input_url']
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req) as response:
        if response.status != 200:
            raise BlupointError(
                err_code="errors.InvalidUsage",
                err_msg="Agency news response is not 200",
                status_code=response.status_code
            )
        o = xmltodict.parse(response.read().decode())
        items = o['rss']['channel']['item']
        logger.info("total content count from dha: <{}>".format(len(items)))

    return items


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


def get_contents_from_ap(agency, agency_config):
    url = agency_config['input_url'] + '/AP.Distro.Feed/GetFeed.aspx?idList=31896&idListType=products&maxItems=20'

    response = requests.get(url, auth=HTTPBasicAuth(agency_config['username'], agency_config['password']))

    logger.warning(response.status_code)
    if response.status_code != 200:
        raise BlupointError(
            err_msg="Agency Rss didnt return 200",
            err_code="errors.InvalidUsage",
            status_code=response.status_code
        )

    feeds_json = json.loads(json.dumps(xmltodict.parse(response.text)))

    items = feeds_json['feed'].get('entry', [])

    news = []
    for item in items:
        images = item.get('link')
        r = {
            'item_id': item['id'],
            'title': item['title'],
            'text': item['content']['#text'],
            'updated': item['updated'],
            'published': item['published'],
            'byline': item['apcm:ContentMetadata']['apcm:ByLine'][0]['#text'],
            'keywords': item.get('Keywords'),
            'images': images
        }

        news.append(r)

    logger.info("total content count from ap: <{}>".format(len(news)))
    return news


def get_content_from_hha(agency, agency_config):
    url = agency_config['input_url']
    app_id = agency_config['app_id']
    app_secret = agency_config['app_secret']
    date_response = requests.get('http://apicache.blutv.com.tr/api/date')
    date = date_response.text

    raw = date[1:-1].strip().encode("utf-8")
    key = app_secret.encode('utf-8')
    hashed = hmac.new(key, raw, hashlib.sha1)
    digest = base64.encodebytes(hashed.digest()).decode('utf-8')

    headers = {
        'Authorization': "{}:{}".format(app_id, digest.rstrip()),
        'X-AppId': app_id,
        'X-Amz-Date': date[1:-1]
    }

    response = requests.get(url, headers=headers)

    return json.loads(response.text)


def upload_image_for_iha(agency_name, content, field, asset_fields, asset_url, token, username, password):
    multiple = False
    for asset_field in asset_fields:
        if asset_field['field_id'] == field:
            multiple = asset_field['multiple']

    img = []

    if "media:content" not in content:
        return [] if multiple else {}
    elif type(content["media:content"]) == list:

        for media in content["media:content"]:
            image_url = media['@url']
            image_name = media['@ResimKodu']
            img.append(image_uploader(agency_name, image_url, image_name, asset_url, token, multiple, username, password))
            
        return img
    elif type(content["media:content"]) == dict:
        image_url = content["media:content"]['@url']
        image_name = content["media:content"]['@ResimKodu']
        image = image_uploader(agency_name, image_url, image_name, asset_url, token, multiple, username, password)
        return image


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
            images = {
                'image_id': content['images']['@residref'],
                'image_title': content['images']['@residref']
            }

            if 'picture' in images['image_id']:
                image = image_uploader(agency_name, images['image_id'], images['image_title'],
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
                image = image_uploader(agency_name, image_id, image_title, asset_url, token, multiple, username,
                                       password)

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


def upload_image_for_dha(agency_name, content, field, asset_fields, asset_url, token, username, password):
    content = json.loads(json.dumps(content))
    multiple = False
    for asset_field in asset_fields:
        if asset_field['field_id'] == field:
            multiple = asset_field['multiple']

    if 'photos' not in content:
        return [] if multiple else {}

    if not multiple:
        image = content['photos']
        if image:
            image_url = str(image)
            image_name = os.path.splitext(image_url.split("/")[-1])[0]

            image = image_uploader(agency_name, image_url, image_name, asset_url, token, multiple, username, password)

        return image

    images = []

    if isinstance(content['photos'], dict):
        images_array = [content['photos']]
    elif isinstance(content['photos'], list):
        images_array = content['photos']
    else:
        images_array = []

    for image in images_array:
        try:
            image_url = str(image)
            image_name = os.path.splitext(image_url.split("/")[-1])[0]
            images.append(
                image_uploader(agency_name, image_url, image_name, asset_url, token, multiple, username, password)
            )
        except TypeError as e:
            continue

    return images


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
            if content['images'].get('@url', None):
                return {}

            images = {
                'image_url': content['images']['@url'],
                'image_title': content['images']['@url'].split('tag:reuters.com,')[-1]
            }

        elif isinstance(content['images'], list):
            images = content['images'][0]
            images['image_url'] = images['@url']
            images['image_title'] = images['@url'].split('tag:reuters.com,')[-1]

        image = image_uploader(agency_name, images['image_url'], images['image_title'],
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


def upload_image_for_hha(agency_name, content, field, asset_fields, asset_url, token, username, password):
    multiple = False
    for asset_field in asset_fields:
        if asset_field['field_id'] == field:
            multiple = asset_field['multiple']

    img = []

    if 'Files' not in content:
        return [] if multiple else {}

    for _file in content.get('Files', []):
        image_url = "http://i.hurimg.com/i/hurriyet/100/0x0/{}".format(_file.get('_Id', 'id'))
        image_name = _file.get('FileName', 'filename')
        img.append(image_uploader(agency_name, image_url, image_name, asset_url, token, username, password))

    return img


def upload_image_for_ap(agency_name, content, field, asset_fields, asset_url, token, username, password):
    content = json.loads(json.dumps(content))
    multiple = False
    for asset_field in asset_fields:
        if asset_field['field_id'] == field:
            multiple = asset_field['multiple']

    if 'images' not in content:
        return [] if multiple else {}

    if not multiple:
        if isinstance(content['images'], dict):
            if not content['images']['apcm:Characteristics'].get('@OriginalFileName'):
                return {}

            images = {
                'image_url': content['images']['@href'],
                'image_title': content['images']['apcm:Characteristics']['@OriginalFileName']
            }

        elif isinstance(content['images'], list):
            images = content['images'][0]
            for i in range(1, len(content['images'])):
                if not images['apcm:Characteristics'].get('@OriginalFileName', None):
                    images = content['images'][i]
                break

            if not images:
                return {}

            images['image_url'] = images['@href']
            images['image_title'] = images['apcm:Characteristics']['@OriginalFileName']

        image = image_uploader(agency_name, images['image_url'], images['image_title'],
                               asset_url, token, multiple, username, password)

        return image

    images = []
    if 'images' in content and content['images']:
        if isinstance(content['images'], dict):
            if not content['images']['apcm:Characteristics'].get('@OriginalFileName'):
                return {}

            image = {
                'image_url': content['images']['@href'],
                'image_title': content['images']['apcm:Characteristics'].get('@OriginalFileName')
            }
            images.append(image)

        elif isinstance(content['images'], list):
            for image in content['images']:
                if not image['apcm:Characteristics'].get('@OriginalFileName'):
                    continue
                image_url = image['@href']
                image_title = image['apcm:Characteristics']['@OriginalFileName']

                images.append(image_uploader(
                    agency_name, image_url, image_title, asset_url, token, multiple, username, password)
                )

    return images


def set_iha_queue(content, redis_queue):
    if content['HaberKodu'] not in iha_queue:
        iha_queue.append(content['HaberKodu'])
    else:
        return False

    return True


def set_aa_queue(content, redis_queue):
    logger.warning(content['item_id'])
    if content['item_id'] not in aa_queue:
        aa_queue.append(content['item_id'])
    else:
        return False

    return True


def set_dha_queue(content, redis_queue):
    if content['guid'] not in iha_queue:
        dha_queue.append(content['guid'])
    else:
        return False

    return True


def set_reuters_queue(content, redis_queue):
    if content['link'] not in iha_queue:
        reuters_queue.append(content['link'])
    else:
        return False

    return True


def set_ap_queue(content, redis_queue):
    if content['item_id'] not in ap_queue:
        ap_queue.append(content['item_id'])
    else:
        return False
    return True


def set_hha_queue(content, redis_queue):
    if content['_Id'] not in ap_queue:
        hha_queue.append(content['_Id'])
    else:
        return False
    return True


def image_uploader(agency_name, image_url, image_name, asset_url, token, multiple, username, password):
    if agency_name == 'IHA':
        r = requests.get(image_url, allow_redirects=True)
        open('images/' + image_name + '.jpg', 'wb').write(r.content)

    elif agency_name == 'AA':
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36'
        }
        url = 'http://api.aa.com.tr/abone/document/{}/web'.format(image_url)
        r = requests.get(url, auth=HTTPBasicAuth(username, password), headers=headers, allow_redirects=True)
        logger.warning(str(r.status_code) + '***status******')
        open('images/' + image_name + '.jpg', 'wb').write(r.content)

    elif agency_name == 'Reuters':
        r = requests.get(image_url, allow_redirects=True, auth=HTTPDigestAuth(username, password))
        open('images/' + image_name + '.jpg', 'wb').write(r.content)

    elif agency_name == 'AP':
        r = requests.get(image_url)
        open('images/' + image_name + '.jpg', 'wb').write(r.content)
    elif agency_name == 'DHA':
        r = requests.get(image_url, allow_redirects=True)
        open('images/' + image_name + '.jpg', 'wb').write(r.content)

    files = {'media': (image_name + '.jpg', open('images/' + image_name + '.jpg', 'rb'))}

    headers = {
        'Authorization': 'Bearer {}'.format(token),
    }

    response = requests.post(asset_url, files=files, headers=headers)

    if response.status_code != 200:
        return [] if multiple else {}

    response_json = json.loads(response.text)
    return response_json['data']['items'][0]
