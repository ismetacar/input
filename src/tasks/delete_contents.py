import json
import logging

import requests

from src.tasks.insert_contents import get_token
from src.utils.errors import BlupointError

logger = logging.getLogger('Delete contents...')


def get_contents_to_be_deleted(token, config, api):
    url = api + '/domains/' + config['domain']['_id'] + '/contents/_query'
    data = {
        'where': {
            'path': config['path'],
            'status': 'draft',
            'sys.created_by': config['cms_username'],
            'sys.published_version': {
                '$exists': False
            }
        },
        'select': {
            '_id': 1
        }
    }

    headers = {
        'Authorization': 'Bearer {}'.format(token),
        'Content-Type': 'application/json'
    }

    response = requests.post(url, data=json.dumps(data), headers=headers)
    if response.status_code != 200:
        raise BlupointError(
            err_code="",
            err_msg="",
            status_code=response.status_code
        )

    response_json = json.loads(response.text)
    logger.info('<{}> contents found for deleting.'.format(response_json['data']['count']))

    return response_json['data']['items']


def delete_contents(contents, token, domain_id, api):
    url = api + '/domains/' + domain_id + '/contents/'
    headers = {
        'Authorization': 'Bearer {}'.format(token)
    }
    for content in contents:
        url += content['_id']
        response = requests.delete(url, headers=headers)

        if response.status_code != 204:
            raise BlupointError(
                err_msg="Error occurred while deleting content",
                err_code="error.internalError",
                status_code=response.status_code
            )

        logger.info("Content <{}> deleted.".format(content['_id']))


def remove_contents_from_cms(configs, settings):
    for config in configs:
        logger.info("Contents deleting for configuration: <{}> in domain: <{}>".format(
            config['name'],
            config['domain']['name'])
        )

        token = get_token(config['csm_username'], config['cms_password'], settings['management_api'] + '/tokens')
        contents = get_contents_to_be_deleted(token, config, settings['management_api'])
        delete_contents(contents, token, config['domain']['id'], settings['management_api'])
