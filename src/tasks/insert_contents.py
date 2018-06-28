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


def insert_contents(contents):
    pass