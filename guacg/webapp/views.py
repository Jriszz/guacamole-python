import os
import sqlite3
import subprocess
from flask import render_template, send_from_directory, request
from werkzeug.debug import DebuggedApplication
from .app import create_app
from .services import MachineOperationApi, MachineMangeApi, AppOperationApi, RunningMachine
from .params import (GetVirtualMachine, RunVirtualMachine, VirtualMachineInfo,\
                    RunApplication, CheckMachineState, CheckService, ModifyIp)
from .tools import update_virtualmachine
from .configlogger import loger
WEBAPP_PATH = os.path.abspath(os.path.dirname(__file__))
STATIC_PATH = os.path.join(WEBAPP_PATH, 'static')


app = create_app()


@app.route('/index', methods=['get'])
def index():
    req_data = request.args.to_dict()
    conn = sqlite3.connect("..\\..\\test.db")
    cursor = conn.cursor()

    sql = "drop table if exists machine_info;"
    cursor.execute(sql)
    sql = "create table machine_info(host varchar(30), username varchar(30), password varchar(30))"
    cursor.execute(sql)
    sql = f"insert into machine_info (host, username, password) values (\'{req_data['host']}\', \'{req_data['username']}\', \'{req_data['password']}\')"
    cursor.execute(sql)
    conn.commit()
    return render_template('rdp.html')


@app.route('/static/<string:filename>')
def send_static(filename):
    return send_from_directory(STATIC_PATH, filename)


@app.route('/cd/machine-info', methods=['get'])
def machine_info():
    try:
        req = GetVirtualMachine().init_and_validate()
        machine_api = MachineMangeApi(req.data)
        return machine_api.get()

    except Exception as ex:
        raise ex


@app.route('/cd/machine-take', methods=['get', 'post'])
def machine_take():
    try:

        if request.method == "GET":
            req = RunVirtualMachine().init_and_validate()
            operation_api = MachineOperationApi(req.data)

            return operation_api.get()
        else:
            req = VirtualMachineInfo().init_and_validate()
            operation_api = MachineOperationApi(req.data)
            operation_api.post()

            return operation_api.post()

    except Exception as ex:
        raise ex


@app.route('/cd/app-start', methods=['get', 'post'])
def app_start():
    try:

        if request.method == "GET":
            req = CheckMachineState().init_and_validate()
            operation_api = AppOperationApi(req.data)
            return operation_api.get()
        else:
            req = RunApplication().init_and_validate()
            operation_api = AppOperationApi(req.data)
            return operation_api.post()

    except Exception as ex:
        raise ex


@app.route('/cd/connect-service', methods=['get'])
def connect_services():
    res_dict = dict(msg="请求成功", data=list(), error_code=None)
    req = CheckService.init_and_validate()
    p = subprocess.Popen(f"ping {req.data['ip_address']}", shell=True, stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE)

    output = p.stdout.read().decode('cp936')
    if output.find("无法访问目标主机") >= 0:
        res_dict['data'] = "ip地址无法访问"
        res_dict['error_code'] = 999
    else:
        res_dict['data'] = "ip地址可访问"

    return res_dict


@app.route('/cd/modify-ip', methods=['get'])
def modify_ip():
    res_dict = dict(msg="请求成功", data=list(), error_code=None)
    req = ModifyIp.init_and_validate()
    update_virtualmachine(ip_address=req.data['ip_address'], machine_name=req.data['machine_name'],
                          username=req.data['username'], password=req.data['password'])

    return res_dict


@app.route('/cd/running-machine', methods=['get'])
def get_machine():
    res_dict  = RunningMachine().get()

    return res_dict


def get_webapp_resources(debug=False):
    """
    Return Flask webapp urls dict, to be included in guacg Resources.
    """
    app.debug = debug
    app2 = DebuggedApplication(app)
    return [('^/static/.*$', app2), ('^/.*$', app2)]