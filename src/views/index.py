from flask import render_template, session


def init_view(app, settings):
    @app.route('/')
    @app.route('/index')
    def index():
        user = session['user']
        asset_service_url = settings['asset_service']
        user_profile_image = user.get('profile_image')
        if user_profile_image:
            user_profile_image = user_profile_image.get('_id', None)

        return render_template('index.html', user=user, asset_service_url=asset_service_url,
                               user_profile_image=user_profile_image)
