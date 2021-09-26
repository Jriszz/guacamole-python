import os, sys
from flask import Flask,jsonify
from .exceptions import CustomFlaskError
from .extensions import cache

def create_app():
    """An application factory, as explained here: http://flask.pocoo.org/docs/patterns/appfactories/.

    :param config_object: The configuration object to use.
    """
    if getattr(sys, 'frozen', False):
        template_folder = os.path.join(sys._MEIPASS, 'templates')
        static_folder = os.path.join(sys._MEIPASS, 'static')
        app = Flask(__name__.split('.')[0], template_folder=template_folder,static_folder=static_folder)
    else:
        app = Flask(__name__.split('.')[0])

    app.secret_key = "secret_key"
    register_errorhandlers(app)
    register_after_request(app)
    register_extensions(app)
    return app


def register_errorhandlers(app):
    """Register error handlers."""
    @app.errorhandler(CustomFlaskError)
    def handler_flask_error(error):
        response = jsonify(error.to_dict())
        response.status_code = 200
        return response


def register_extensions(app):
    """Register Flask extensions."""
    cache.init_app(app)


def register_after_request(app):
    @app.after_request
    def cors(response):
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Method'] = '*'
        response.headers['Access-Control-Allow-Headers'] = 'x-requested-with,content-type'
        response.headers["Cache-Control"] = "no-cache"
        return response