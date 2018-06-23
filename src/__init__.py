from flask import Flask
from pymongo import MongoClient


def create_app(settings):
    app = Flask(__name__, template_folder='../templates', static_folder='../static')
    app.secret_key = settings['secret']
    app.db = MongoClient(settings['mongo_connection_string']).get_database(settings['default_database'])

    from src.views.auth import init_view
    init_view(app, settings)

    from src.views.index import init_view
    init_view(app, settings)

    from src.views.configs import init_view
    init_view(app, settings)
    return app
