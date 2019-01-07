import json
import jwt
import requests


def refresh_token(api_endpoint, token):
    payload = {
        'token': token
    }

    response = requests.post(api_endpoint, data=json.dumps(payload))

    if response.status_code != 200:
        return False
    response_json = json.loads(response.text)

    return response_json


def me_user(api_endpoint, token):

    headers = {
        'Authorization': 'Bearer {}'.format(token)
    }

    response = requests.get(api_endpoint, headers=headers)

    if response.status_code != 201:
        return False

    response_json = json.loads(response.text)

    return response_json


def extract_token(token, alg='HS256'):
    return jwt.decode(token, algorithms=alg, verify=False)
