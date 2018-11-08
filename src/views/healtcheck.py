from flask import Response


def init_view(app, settings):
    @app.route('/healtcheck')
    def healtcheck():
        return Response(response=None, status=200)
