import copy
import json
import logging

import requests

from src.helpers.contents import (
    get_contents_from_iha,
    get_contents_from_reuters,
    get_contents_from_aa,
    get_contents_from_dha,
    set_iha_queue, set_dha_queue, set_aa_queue, set_reuters_queue)
from src.utils.errors import BlupointError

logger = logging.getLogger('Insert Contents...')

GET_CONTENTS = {
    'IHA': get_contents_from_iha,
    'DHA': get_contents_from_dha,
    'AA': get_contents_from_aa,
    'Reuters': get_contents_from_reuters
}

SET_TO_QUEUE = {
    'IHA': set_iha_queue,
    'DHA': set_dha_queue,
    'AA': set_aa_queue,
    'Reuters': set_reuters_queue
}

config_fields = ['_id', 'agency_name', 'input_url', 'domain', 'content_type', 'username', 'password',
                 'cms_username', 'cms_password', 'sync_at', 'path', 'publish', 'membership_id',
                 'username_parameter', 'password_parameter', 'expire_time', 'next_run_time']


def get_token(username, password, token_api):
    data = {
        'username': username,
        'password': password
    }

    response = requests.post(token_api, data=json.dumps(data))

    if response.status_code != 201:
        raise BlupointError(
            err_code="errors.errorOccurredWhileGetToken",
            err_msg="Internal Server Error",
            status_code=response.status_code,
            context={
                'message': response.text
            }
        )

    response_json = json.loads(response.text)
    return response_json['token']


def map_fields_by_config(content, config, integer_fields):
    for field in config_fields:
        config.pop(field, None)

    fields = config.keys()
    cms_content = {}

    for field in fields:
        if not config[field]:
            continue
        if field in integer_fields:
            cms_content[field] = int(content[config[field]])
        else:
            cms_content[field] = content[config[field]]

    return cms_content


def get_agency_contents(config, db):
    agency = db.agency_fields.find_one({
        'name': config['agency_name']
    })

    contents = GET_CONTENTS[agency['name']](agency, config)
    cms_contents = []
    _config = copy.deepcopy(config)
    integer_fields = [x for x in config['field_definitions'] if x['type'] == 'integer']
    _config.pop('field_definitions', None)
    i = 0
    for content in contents:
        if not SET_TO_QUEUE[agency['name']](content):
            i += 1
            continue

        cms_content = {
            'status': 'draft',
            'type': config['content_type']['type'],
            'path': config['path'],
            'base_type': 'content'
        }
        cms_content.update(map_fields_by_config(content, _config, integer_fields))
        cms_contents.append(cms_content)

    return cms_contents


def insert_contents(configs, settings, db):
    for config in configs:
        logger.info("Contents inserting to CMS for configuration: <{}> in domain: <{}>".format(
            config['name'],
            config['domain']['name'])
        )
        token = get_token(config['cms_username'], config['cms_password'], settings['management_api'] + '/tokens')
        cms_contents = get_agency_contents(config, db)
        url = settings['management_api'] + '/domains/{}/contents'.format(config['domain']['_id'])
        headers = {
            'Authorization': 'Bearer {}'.format(token)
        }
        for content in cms_contents:

            response = requests.post(url, headers=headers, data=json.dumps(content))
            if response.status_code != 201:
                continue

            response_json = json.loads(response.text)
            logger.info('content created with id: <{}>'.format(response_json['_id']))
