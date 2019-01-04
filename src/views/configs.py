import datetime
import json
import math
from bson import ObjectId
from flask import render_template, request, url_for, redirect, session, Response
from src.helpers.critial_fields_helper import decrypt_critial_fields, encrypt_critial_fields

from src.helpers import input

from src.helpers.user import (
    get_user_domains,
    get_domain_by_id,
    get_content_type_by_id
)

AGENCY_URL_LOOKUP = {
    'IHA': input.make_iha_request,
    'AA': input.make_aa_request,
    'DHA': input.make_dha_request,
    'Reuters': input.make_reuters_request,
    'AP': input.make_ap_request,
    "HHA": input.make_hha_request
}


def init_view(app, settings):
    @app.route(
        '/configs',
        methods=['GET']
    )
    def configs_index():
        page = int(request.args.get('page', 1))
        page = 1 if page <= 0 else page
        limit = 10
        skip = int(page - 1) * limit

        cur = app.db.configurations.find({
            'membership_id': session['user']['membership']['_id']
        })

        total_count = cur.count()
        cur.skip(int(skip))
        cur.limit(int(limit))
        configs = list(cur)

        page_count = math.ceil(total_count / 10)

        user = session['user']
        asset_service_url = settings['asset_service']
        user_profile_image = user.get('profile_image')
        if user_profile_image:
            user_profile_image = user_profile_image.get('_id', None)

        return render_template('configs.html', configs=configs, total_count=total_count,
                               asset_service_url=asset_service_url, user_profile_image=user_profile_image,
                               page=page, page_count=page_count)

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
            body['membership_id'] = session['user']['membership']['_id']
            body = encrypt_critial_fields(body, settings["salt"])
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

            body['next_run_time'] = datetime.datetime.utcnow()
            body['next_run_time_for_delete'] = datetime.datetime.utcnow()

            field_definitions = get_content_types_field_definitions(settings, body['domain']['_id'],
                                                                    body['content_type']['_id'])
            if field_definitions:
                body['field_definitions'] = field_definitions

            app.db.configurations.save(body)
            return redirect(url_for('index'))

        domains = get_user_domains(session['token'], session['user'], settings)

        agencies = list(app.db.agency_fields.find({}))

        return render_template('config.html', domains=domains, token=session['token'], agencies=agencies,
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
            'membership_id': session['user']['membership']['_id']
        })

        config_detail = decrypt_critial_fields(config_detail, settings['salt'])

        config_detail['_id'] = str(config_detail['_id'])

        domains = get_user_domains(session['token'], session['user'], settings)
        management_api = settings['management_api']
        token = session['token']

        agencies = list(app.db.agency_fields.find({}))

        return render_template('config.html', agency_config=config_detail, domains=domains, agencies=agencies,
                               management_api=management_api, token=token, user_profile_image=user_profile_image,
                               asset_service_url=asset_service_url)

    @app.route('/configs/<config_id>/edit', methods=['GET', 'POST'])
    def config_edit(config_id):

        agency_config = app.db.configurations.find_one({
            '_id': ObjectId(config_id),
            'membership_id': session['user']['membership']['_id']
        })

        fields = app.db.agency_fields.find_one({
            'agency_url': agency_config['input_url']
        })

        if request.method == 'POST':
            body = encrypt_critial_fields(request.form.to_dict(), settings['salt'])
            body['membership_id'] = session['user']['membership']['_id']

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
                'name': body['agency_name']
            })

            field_definitions = get_content_types_field_definitions(settings, domain_id, content_type_id)

            fields = {
                'agency_fields': agency_fields.get('fields', [])
            }

            if field_definitions:
                fields['field_definitions'] = field_definitions

                if body.get('agency_config_id', None):
                    app.db.configurations.find_and_modify(
                        {
                            '_id': ObjectId(body['agency_config_id'])
                        },
                        {
                            '$set': {
                                'field_definitions': fields['field_definitions']
                            }
                        }
                    )

            return Response(json.dumps(fields), mimetype='application/json')

    @app.route(
        '/rss',
        methods=['GET', 'POST']
    )
    def get_agency_rss():
        body = request.form.to_dict()

        agency = app.db.agency_fields.find_one({
            'name': body['agency_name']
        })

        response_json = AGENCY_URL_LOOKUP[agency['name']](agency, body)

        return Response(response_json, mimetype='application/json')
