import json
import os
from collections import deque
from datetime import timedelta, datetime

from flask import flash, session, request, url_for, redirect

from src import create_app, make_celery
from src.utils.errors import BlupointError
from src.utils.json_jelpers import parse_boolean
from src.utils.token import me, extract_token, refresh_token

iha_queue = deque([], 1500)
dha_queue = deque([], 1500)
aa_queue = deque([], 1500)
reuters_queue = deque([], 1500)
ap_queue = deque([], 1500)
hha_queue = deque([], 1500)


def config_settings():
    config_file_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "confs/local.py"))
    with open(config_file_path, 'r') as f:
        settings = json.loads(f.read().split(' = ')[1], object_hook=parse_boolean)
    f.close()
    return settings


settings = config_settings()
app = create_app(settings)

celery = make_celery(app, settings)


@app.before_request
def before_request():
    if request.endpoint == 'healtcheck':
        token = session.get('token', None)
        if not token:
            flash("Please Login to see actions")
            return redirect(url_for('login'))

        decoded_token = extract_token(token)
        token_expire_date = decoded_token['exp']
        if (datetime.fromtimestamp(token_expire_date) - timedelta(minutes=5)).timestamp() < datetime.now().timestamp():
            refresh_api_endpoint = settings['management_api'] + '/tokens/refresh'
            refreshed_token = refresh_token(refresh_api_endpoint, token)
            if not refreshed_token:
                flash("session closed automatically because no action was taken")
                return redirect(url_for('login'))
            session['token'] = refreshed_token['token']

    if request.endpoint not in ['login', 'static', 'logout']:

        token = session.get('token', None)
        if not token:
            flash("Please Login to see actions")
            return redirect(url_for('login'))

        me_api_endpoint = settings['management_api'] + '/me'
        user = me(me_api_endpoint, token)

        if not user:
            flash("Failed to retrieve user information")
            return redirect(url_for('login'))


@app.errorhandler(Exception)
def handle_exceptions(e):
    if isinstance(e, BlupointError):
        error = {
            'err_msg': e.err_msg or 'Internal error occurred',
            'err_code': e.err_code or 'errors.internalError',
            'context': e.context,
            'reason': e.reason
        }

        flash(error['err_msg'], 'error')
        return redirect(url_for('login'))

    else:
        error = {
            'err_msg': str(e),
            'err_code': "errors.internalError"
        }

        flash(error['err_msg'], 'error')
        return redirect(url_for('index'))


if __name__ == '__main__':
    app.run()
