import json

import requests

from src.utils.errors import BlupointError


def get_token(username, password, token_api):
    data = {
        'username': username,
        'password': password
    }

    response = requests.post(token_api, data=json.dumps(data))

    if response.status_code != 201:
        raise BlupointError(
            err_code="",
            err_msg="",
            status_code=response.status_code
        )

    response_json = json.loads(response.text)
    return response_json['token']


def map_fields_by_config(content, config):
    #: mapping for content type like preview
    #: return the prepared content
    return True


def insert_contents(configs):
    for config in configs:
        contents = get_contents_from_agency(config)
        set_contents_to_cms(contents, config)


def get_contents_from_agency(config):
    #: send request to agency and get response
    #: parse response by response type in config
    #: return the contents
    return True


def create_content(content, config):
    #: make post request to cms
    #: firstly get token from management api
    return True


def set_contents_to_cms(contents, config):
    for content in contents:
        prepared_content = map_fields_by_config(content, config)
        content = create_content(content)

    return len(contents)
