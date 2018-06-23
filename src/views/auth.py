from flask import request, render_template, flash, url_for, redirect, session

from src.helpers.user import authenticate_user
from src.utils.errors import BlupointError


def init_view(app, settings):
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            credentials = {
                'username': request.form['username'],
                'password': request.form['password']
            }

            try:
                user, token = authenticate_user(credentials, settings)
                session['user'] = user
                session['token'] = token

            except BlupointError as e:
                flash(str(e.err_msg), 'error')
                return redirect(url_for('login'))

            session.pop('_flashes', None)
            return redirect(url_for('index'))

        return render_template('login.html')

    @app.route('/logout')
    def logout():
        session.pop('user', None)
        session.pop('token', None)
        session.pop('domains', None)
        session.pop('content_types', None)

        return render_template('login.html')
