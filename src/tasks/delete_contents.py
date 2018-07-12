import datetime
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
            'path': config['path'] + '/',
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
    logger.info(data)
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


def delete_contents(contents, token, domain_id, api, job_execution_id, agency_name, db):
    headers = {
        'Authorization': 'Bearer {}'.format(token)
    }
    successfully_completed = 0
    unsuccessfully_completed = 0
    meta = []
    for content in contents:
        url = api + '/domains/' + domain_id + '/contents/' + content['_id']
        response = requests.delete(url, headers=headers)

        if response.status_code != 204:
            unsuccessfully_completed += 1
            meta.append(json.loads(response.text))
            continue

        successfully_completed += 1
        logger.info("Content <{}> deleted. Agency: <{}>. Domain: {}".format(content['_id'], agency_name, domain_id))

        db.job_executions.find_and_modify(
            {
                '_id': job_execution_id
            },
            {
                '$set': {
                    'total_content_count': len(contents),
                    'successfully_completed_content': successfully_completed,
                    'unsuccessfully_completed': unsuccessfully_completed,
                    'meta': meta
                }
            }
        )

    db.job_executions.find_and_modify(
        {
            '_id': job_execution_id
        },
        {
            '$set': {
                'sys.finished_at': datetime.datetime.utcnow(),
                'status': 'finished'
            }
        }
    )


def create_job_execution(job_type, agency_name, content_type, domain, membership_id, db):
    job_execution = {
        'type': job_type,
        'status': 'started',
        'agency': agency_name,
        'successfully_completed_content': 0,
        'unsuccessfully_completed': 0,
        'total_content_count': 0,
        'content_type': content_type,
        'domain': domain,
        'membership_id': membership_id,
        'result': {},
        'meta': [],
        'sys': {
            'started_at': datetime.datetime.utcnow()
        },
        'error': {}
    }

    return db.job_executions.save(job_execution)


def remove_contents_from_cms(configs, settings, db, redis_queue):
    for config in configs:
        logger.info("Contents deleting for configuration: <{}> in domain: <{}>".format(
            config['agency_name'],
            config['domain']['name'])
        )
        token = get_token(config['cms_username'], config['cms_password'], settings['management_api'] + '/tokens')
        contents = get_contents_to_be_deleted(token, config, settings['management_api'])
        job_execution_id = create_job_execution('remove', config['agency_name'], config['content_type'],
                                                config['domain'], config['membership_id'], db)

        delete_contents(contents, token, config['domain']['_id'],
                        settings['management_api'], job_execution_id, config['agency_name'], db)
