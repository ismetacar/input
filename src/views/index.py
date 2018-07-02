from flask import redirect, url_for


def init_view(app, settings):
    @app.route('/')
    @app.route('/index')
    def index():
        return redirect(url_for('jobs'))