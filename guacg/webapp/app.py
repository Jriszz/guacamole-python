import json
from flask import Flask,jsonify
from .exceptions import CustomFlaskError


def create_app():
    """An application factory, as explained here: http://flask.pocoo.org/docs/patterns/appfactories/.

    :param config_object: The configuration object to use.
    """
    app = Flask(__name__.split('.')[0])
    app.secret_key = "secret_key"
    register_errorhandlers(app)
    register_after_request(app)
    return app


def register_errorhandlers(app):
    """Register error handlers."""
    @app.errorhandler(CustomFlaskError)
    def handler_flask_error(error):
        response = jsonify(error.to_dict())
        response.status_code = 200
        return response


def register_after_request(app):
    @app.after_request
    def cors(response):
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Method'] = '*'
        response.headers['Access-Control-Allow-Headers'] = 'x-requested-with,content-type'
        response.headers["Cache-Control"] = "no-cache"
        return response