import json

import requests
from bson import ObjectId
from flask import render_template, request, url_for, redirect, session, Response

from src.helpers.user import get_user_domains, get_domain_by_id, get_content_type_by_id


def init_view(app, settings):
    @app.route(
        '/configs',
        methods=['GET']
    )
    def configs_index():
        configs = list(app.db.configurations.find({
            'membership_id': session['user']['membership_id']
        }))

        user = session['user']
        asset_service_url = settings['asset_service']
        user_profile_image = user.get('profile_image')
        if user_profile_image:
            user_profile_image = user_profile_image.get('_id', None)

        return render_template('configs.html', configs=configs, asset_service_url=asset_service_url,
                               user_profile_image=user_profile_image)

    @app.route(
        '/configs/create',
        methods=['GET', 'POST']
    )
    def configs_create():
        user = session['user']
        asset_service_url = settings['asset_service']
        user_profile_image = user.get('profile_image')

        if user_profile_image:
            user_profile_image = user_profile_image.get('_id', None)
        if request.method == 'POST':
            body = request.form.to_dict()
            body['membership_id'] = session['user']['membership_id']
            domain = get_domain_by_id(body['domain'], session['token'], settings)
            content_type = get_content_type_by_id(body['content_type'], body['domain'], session['token'], settings)
            body['domain'] = {
                '_id': body['domain'],
                'name': domain['name']
            }

            body['content_type'] = {
                '_id': body['content_type'],
                'name': content_type['name'],
                'type': content_type['type']
            }

            app.db.configurations.save(body)
            return redirect(url_for('index'))

        domains = get_user_domains(session['token'], session['user'], settings)

        return render_template('config.html', domains=domains, token=session['token'],
                               management_api=settings['management_api'], agency_config=None,
                               asset_service_url=asset_service_url, user_profile_image=user_profile_image)

    @app.route(
        '/configs/<config_id>',
        methods=['GET']
    )
    def config(config_id):
        user = session['user']
        asset_service_url = settings['asset_service']
        user_profile_image = user.get('profile_image')
        if user_profile_image:
            user_profile_image = user_profile_image.get('_id', None)
        config_detail = app.db.configurations.find_one({
            '_id': ObjectId(config_id),
            'membership_id': session['user']['membership_id']
        })

        fields = app.db.agency_fields.find_one({
            'agency_url': config_detail['input_url']
        })

        config_detail['_id'] = str(config_detail['_id'])

        domains = get_user_domains(session['token'], session['user'], settings)
        management_api = settings['management_api']
        token = session['token']

        return render_template('config.html', agency_config=config_detail, domains=domains,
                               management_api=management_api, token=token, user_profile_image=user_profile_image,
                               asset_service_url=asset_service_url, fields=fields['fields'])

    @app.route('/configs/<config_id>/edit', methods=['GET', 'POST'])
    def config_edit(config_id):

        agency_config = app.db.configurations.find_one({
            '_id': ObjectId(config_id),
            'membership_id': session['user']['membership_id']
        })

        fields = app.db.agency_fields.find_one({
            'agency_url': agency_config['input_url']
        })

        if request.method == 'POST':
            body = request.form.to_dict()
            body['membership_id'] = session['user']['membership_id']
            domain = get_domain_by_id(body['domain'], session['token'], settings)
            content_type = get_content_type_by_id(body['content_type'], body['domain'], session['token'], settings)
            body['domain'] = {
                '_id': body['domain'],
                'name': domain['name']
            }

            body['content_type'] = {
                '_id': body['content_type'],
                'name': content_type['name'],
                'type': content_type['type']
            }

            agency_config.update(body)
            app.db.configurations.update({'_id': agency_config['_id']}, agency_config)

            return redirect(url_for('config', config_id=str(agency_config['_id'])))

        domains = get_user_domains(session['token'], session['user'], settings)

        return render_template('config.html', agency_config=agency_config, domains=domains,
                               management_api=settings['management_api'], fields=fields['fields'])

    @app.route(
        '/configs/<config_id>/delete',
        methods=['GET']
    )
    def config_delete(config_id):
        app.db.configurations.remove({
            '_id': ObjectId(config_id)
        })

        return redirect('configs')

    @app.route(
        '/configs/mapping',
        methods=['GET', 'POST']
    )
    def mapping():

        if request.method == 'POST':

            body = request.form.to_dict()
            content_type_id = body['content_type_id']
            domain_id = body['domain_id']
            agency_fields = app.db.agency_fields.find_one({
                'name': body['agency']
            })

            url = settings['management_api'] + '/domains/' + domain_id + '/content-types/' + content_type_id
            headers = {
                'Authorization': 'Bearer {}'.format(session['token']),
                'Content-Type': 'application/json'
            }

            response = requests.get(url, headers=headers)

            fields = {}
            if response.status_code == 200:
                content_type = json.loads(response.text)

                fields['field_definitions'] = content_type.get('field_definitions', [])
                fields['agency_fields'] = agency_fields.get('fields', [])

            return Response(json.dumps(fields), mimetype='application/json')
