import json
from flask import Flask,jsonify,request
from .configlogger import loger
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
        if 300 <= response.status_code < 400:
            return response
        if not response.is_json:
            return response
        data = response.json
        if isinstance(data, dict) and "error_code" in data and "msg" in data:
            return response
        if isinstance(data, dict) and "data" not in data and "error_code" not in data and "msg" not in data:
            data = {"data": data}
        if not isinstance(data, dict):
            data = {"data": data}
        if "error_code" not in data:
            data["error_code"] = 0
        if "msg" not in data:
            func = app.view_functions.get(request.endpoint)
            # print(f"func:{getattr(func, 'view_class')}")
            if func:
                if hasattr(func, "view_class"):
                    desc = (
                        getattr(getattr(func, "view_class"), request.method.lower())
                            .__doc__.strip()
                            .split("\n")[0]
                    )
                else:
                    desc = func.__doc__.strip().split("\n")[0]
            else:
                desc = "找不到请求视图，404"

            data["msg"] = f"{desc}成功"
        # 将规范化后的值重新赋给response对象
        response.data = json.dumps(data, ensure_ascii=False)
        loger.info(
            f"Request: method={request.method} path={request.path},endpoint={request.endpoint},desc={data['msg']}"
        )
        return response