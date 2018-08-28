import json

import requests

from src.utils.errors import BlupointError


def get_user_domains(token, user, settings):
    url = settings['management_api'] + '/domains/_query'
    headers = {
        'Authorization': 'Bearer {}'.format(token)
    }
    body = {
        'where': {
            'membership_id': user['membership']['_id']
        }
    }

    response = requests.post(url, headers=headers, json=body)

    if response.status_code != 200:
        raise BlupointError(
            err_code="errors.requestError",
            err_msg=json.loads(response.text),
            status_code=response.status_code
        )

    domains = json.loads(response.text)
    return domains['data']['items']


def get_user_by_token(token, settings):
    url = settings['management_api'] + '/me'
    headers = {
        'Authorization': 'Bearer {}'.format(token)
    }

    response = requests.get(url, headers=headers)

    if response.status_code != 201:
        raise BlupointError(
            err_msg="Me Api did not return 201",
            err_code="errors.providedTokenIsExpired",
            status_code="401"
        )

    user = json.loads(response.text)

    return user['user']


def authenticate_user(credentials, settings):
    url = settings['management_api'] + '/tokens'

    response = requests.post(url, json=credentials)

    if response.status_code != 201:
        raise BlupointError(
            err_msg="Username or password is invalid",
            err_code="errors.usernameOrPasswordIsInvalid",
            status_code="401"
        )

    token = json.loads(response.text)

    user = get_user_by_token(token['token'], settings)

    return user, token['token']


def get_domain_by_id(domain_id, token, settings):
    url = settings['management_api'] + '/domains/' + domain_id
    headers = {
        'Authorization': 'Bearer {}'.format(token)
    }

    response = requests.get(url, headers=headers)

    return json.loads(response.text)


def get_content_type_by_id(content_type_id, domain_id, token, settings):
    url = settings['management_api'] + '/domains/' + domain_id + '/content-types/' + content_type_id
    headers = {
        'Authorization': 'Bearer {}'.format(token)
    }

    response = requests.get(url, headers=headers)

    return json.loads(response.text)
