from flask import request, session, render_template
from pymongo import DESCENDING


def init_view(app, settings):
    @app.route('/jobs', methods=['GET'])
    def jobs():
        limit = request.args.get('limit')
        skip = request.args.get('skip')

        jobs = app.db.job_executions.find({}).sort("_id", DESCENDING)

        if skip:
            jobs.skip(int(skip))

        if not limit or limit > 500:
            limit = 500
            jobs.limit(int(limit))

        items = list(jobs)

        user = session['user']
        asset_service_url = settings['asset_service']
        user_profile_image = user.get('profile_image')
        if user_profile_image:
            user_profile_image = user_profile_image.get('_id', None)

        return render_template('jobs.html', user=user, items=items, asset_service_url=asset_service_url,
                               user_profile_image=user_profile_image)
