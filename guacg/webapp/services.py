from flask import request
from sqlalchemy import desc, and_
from .models import session
from .configlogger import loger
from .tools import request_client
from . import params
from .vm_manager import VmManager
from .application_manager import ApplicationManager
from .tools import (check_machineinfo, check_virtualmachineinfo,
                    change_enums, get_enable_state,update_virtualmachine,check_running_virtualmachine)
from .models import EnvironConfig, create_cursor, VirtualMachineInfo,PackageRecord
from .state_enums import TaskStateEnum, ResponseEnum, ApplicationEnum
from itertools import zip_longest

UNKNOW_STATE = "未知"


class EnvironConfigApi(object):
    """
    环境配置
    :author:zz
    :time: 2020.11.02
    """

    def get(self):
        """
        查询配置
        """
        require_data = params.get_environ_params()

        search_condition = require_data.get("search_condition", None)
        environ_id = require_data.get("id", None)
        merge_tuple = ("value",)
        res_dict = dict(config_list=[], total=None, app_path_option=[])

        if environ_id:
            res = EnvironConfig.query.filter(EnvironConfig.id == environ_id).first()

            res_dict["config_list"].append(res.sing_to_dict())

        else:
            if search_condition:
                res = (
                    EnvironConfig.query.filter(
                        EnvironConfig.ip_address.like(f"{search_condition}%")
                    )
                    .order_by(desc(EnvironConfig.create_time))
                    .paginate(require_data["page"], require_data["page_size"], False)
                )

                res_total = res.total

            else:
                res = EnvironConfig.query.order_by(
                    desc(EnvironConfig.create_time)
                ).paginate(require_data["page"], require_data["page_size"], False)
                res_total = res.total

            for item in res.items:
                res_dict["config_list"].append(item.sing_to_dict())

            res_dict["total"] = res_total
        # 查询worker状态
        try:
            cursor = create_cursor()

            for item in res_dict["config_list"]:

                    cursor.execute(
                        f"select worker_state from tbl_worker where last_login_ip = '{item['ip_address']}'"
                    )
                    result = cursor.fetchall()
                    if result:
                        item["worker_state"] = result[0][0]
        except Exception as ex:
            for item in res_dict["config_list"]:
                item['worker_state'] = UNKNOW_STATE

        # 查询下载地址
        app_path_res = (
            db.session.query(PackageRecord.download_url)
            .order_by(desc(PackageRecord.create_time))
            .all()
        )

        for item in app_path_res:
            ele = {key: value for key, value in zip(merge_tuple, item)}
            res_dict["app_path_option"].append(ele)

        return res_dict

    def delete(self):
        """卸载远程creator,worker"""
        req_data = params.del_environ_params()
        uninstall_app_path = req_data["app_name"]
        ip_addr = req_data["ip_address"]

        return self.remote_control(
            ip_addr, "uninstall", uninstall_app_path, req_data, "delete"
        )

    def post(self):
        """先查询该环境是否已经安装了其他版本的creator，有的话，先通知用户是否覆盖安装creator，没有的话，就远程安装远程creator，worker"""
        base_version = 530
        http_info = "http://"
        replace_info = ("http://192.168.0.5:8800/", "//192.168.0.5/share/")
        res_dict = dict(msg=None, data=None, error_code=None)
        req_data = params.add_environ_params()
        install_app_path = req_data["app_path"]
        ip_addr = req_data["ip_address"]
        app_name_list = req_data["app_name"].split("_")
        version_num = app_name_list[1].replace(".", "")

        # 判断路径
        exist_http = install_app_path.find(http_info)

        if exist_http != -1:
            install_app_path = install_app_path.replace(
                replace_info[0], replace_info[1]
            )

        if int(version_num) >= base_version:
            res = EnvironConfig.query.filter(
                and_(
                    EnvironConfig.ip_address == ip_addr,
                    EnvironConfig.app_name == req_data["app_name"],
                    EnvironConfig.version_bit == req_data["version_bit"],
                )
            ).first()
        else:
            res = EnvironConfig.query.filter(
                and_(
                    EnvironConfig.ip_address == ip_addr,
                    EnvironConfig.app_name.like(f"{app_name_list[0]}%"),
                    EnvironConfig.version_bit == req_data["version_bit"],
                )
            ).first()

        if res:
            res_dict["msg"] = f"{res.app_name}_{req_data['version_bit']}已安装，是否覆盖安装"
            res_dict["error_code"] = -1
            res_dict["data"] = res.id
            return res_dict
        else:
            return self.remote_control(
                ip_addr, "install", install_app_path, req_data, "post"
            )

    def put(self):
        req_data = params.put_environ_params()
        install_app_path = req_data["app_path"]
        ip_addr = req_data["ip_address"]
        http_info = "http://"
        replace_info = ("http://192.168.0.5:8800/", "//192.168.0.5/share/")

        # 判断路径
        exist_http = install_app_path.find(http_info)

        if exist_http != -1:
            install_app_path = install_app_path.replace(
                replace_info[0], replace_info[1]
            )

        return self.remote_control(
            ip_addr, "install", install_app_path, req_data, "put"
        )

    @staticmethod
    def remote_control(ip_addr, task_type, app_path, req_data, operate_type):
        res_dict = dict(msg=None, data=None, error_code=None)
        req_dict = dict(task_type=None, app_path=None, version_bit=None)
        req_dict["task_type"] = task_type
        req_dict["app_path"] = app_path
        req_dict["version_bit"] = req_data.get("version_bit", None)

        affix_url = ("http://", ":5053/orders")
        # 远程安装
        req_url = "".join((affix_url[0], ip_addr, affix_url[1]))
        s = request_client()
        res = s.get(req_url, params=req_dict)

        if res.status_code == 200:
            install_res = res.json()
            install_res_code = install_res["resp_code"]

            if install_res_code == "90000":

                if operate_type == "put":
                    commit_data = req_data.copy()
                    commit_data.pop("environ_id")
                    EnvironConfig.query.filter(
                        EnvironConfig.id == req_data["environ_id"]
                    ).update(commit_data)

                elif operate_type == "post":

                    EnvironConfig.add_one(req_data)
                else:
                    EnvironConfig.query.filter(
                        EnvironConfig.id == req_data["environ_id"]
                    ).delete()

                res_dict["msg"] = "请求成功"

                return res_dict

            else:
                res_dict["msg"] = install_res["resp_desc"]
                res_dict["error_code"] = -1
                return res_dict

        else:
            res_dict["msg"] = res.text
            res_dict["error_code"] = res.status_code
            return res_dict


class RePortEnvironInfoApi(object):
    def __init__(self):
        self.base_version = 530

    def get(self):
        """
        查询worker信息
        """
        worker_name_list = []
        response_dict = dict(worker_list=None)
        BIT_64 = "64位"
        ip_addr = request.remote_addr

        res = (
            EnvironConfig.query.filter(
                and_(
                    EnvironConfig.app_name.like("Worker%"),
                    EnvironConfig.ip_address == ip_addr,
                )
            )
            .order_by(desc(EnvironConfig.create_time))
            .all()
        )

        for item in res:
            app_name_list = item.app_name.split("_")
            version_num = app_name_list[1].replace(".", "")

            if int(version_num) >= self.base_version:
                if item.version_bit == BIT_64:
                    worker_name = f"UiBot Worker {app_name_list[1]} (x64)"
                else:
                    worker_name = f"UiBot Worker {app_name_list[1]}"
            else:
                if item.version_bit == BIT_64:
                    worker_name = f"UiBot Worker (x64)"
                else:
                    worker_name = f"UiBot Worker"

            worker_name_list.append(worker_name)

        response_dict["worker_list"] = worker_name_list
        return response_dict

    def post(self):
        """
        记录安装信息
        """
        req_data = params.get_environ_info()
        ip_addr = request.remote_addr
        req_data["ip_address"] = ip_addr
        app_name_list = req_data["app_name"].split("_")
        version_num = app_name_list[1].replace(".", "")

        if int(version_num) >= self.base_version:
            res = EnvironConfig.query.filter(
                and_(
                    EnvironConfig.ip_address == ip_addr,
                    EnvironConfig.app_name == req_data["app_name"],
                    EnvironConfig.version_bit == req_data["version_bit"],
                )
            ).first()

        else:
            res = EnvironConfig.query.filter(
                and_(
                    EnvironConfig.ip_address == ip_addr,
                    EnvironConfig.app_name.like(f"{app_name_list[0]}%"),
                    EnvironConfig.version_bit == req_data["version_bit"],
                )
            ).first()

        if res:
            # 修改信息
            if res.environ_name:
                req_data.pop("environ_name")

            EnvironConfig.query.filter(EnvironConfig.id == res.id).update(req_data)

        else:

            EnvironConfig.add_one(req_data)


class RefreshApi(object):
    """刷新worker状态"""

    def get(self):
        res_dict = dict(msg="请求成功", data=None, error_code=None)
        ip_address = request.args.get("ip_address")
        req_url = f"http://{ip_address}:5053/refresh"
        loger.info(f"目标机器Worker刷新地址：{req_url}")
        # 创建
        s = request_client()

        res = s.get(req_url)
        utils.format_output(res, level="debug")
        if res.status_code == 200:

            refresh_res = res.json()
            res_code = refresh_res["resp_code"]

            if res_code == "90000":
                return res_dict
            else:
                res_dict["msg"] = refresh_res["resp_desc"]
                res_dict["error_code"] = -1
                return res_dict
        else:
            res_dict["msg"] = res.text
            res_dict["error_code"] = res.status_code
            return res_dict


class MachineMangeApi(object):
    """虚拟机管理"""

    def __init__(self, data):
        self.data =  data

    def get(self):
        """
        查询虚拟机
        """
        require_data = self.data
        res_dict = dict(msg="请求成功", data=dict(), error_code=None)
        machine_list = list()
        host_list = list()
        temp_list = list()
        machine_name = require_data['machine_name']

        try:
            if not machine_name:
                # 查全部
                with session() as db:
                    environ_res = db.query(VirtualMachineInfo).filter(VirtualMachineInfo.machine_type == 'host').all()

                for environ_item in environ_res:
                    host_ip = environ_item.ip_address
                    host_name = environ_item.username
                    host_password = environ_item.passwords
                    host_machinename = environ_item.machine_name
                    try:
                        machine_list = check_virtualmachineinfo(host_ip, host_name, host_password, machine_list, VmManager)
                        temp_list.extend(machine_list)
                    except Exception as ex:
                        loger.error(ex)

                    host_machine = dict(type='host', ipaddress=None, username=None, passwords=None, Name=None)
                    host_machine['ipaddress'] = host_ip
                    host_machine['username'] = host_name
                    host_machine['passwords'] = host_password
                    host_machine['Name'] = host_machinename
                    host_list.append(host_machine)

                res_dict['data']["virtual_machine"] = temp_list
                res_dict['data']['host_machine'] = host_list

                return res_dict

            else:
                # 查单台
                ip_address, username, password = check_machineinfo(VirtualMachineInfo, machine_name)


                try:
                    machine_list = check_virtualmachineinfo(ip_address, username, password, machine_list, VmManager)

                except Exception as ex:
                    loger.error(ex)
                    res_dict['msg'] = "无法连接宿主机，检查宿主机是否正常运行"
                    res_dict['error_code'] = 999

                res_dict['data']["virtual_machine"] = machine_list

                return res_dict

        except Exception as ex:
            loger.error(f"虚拟机查询异常：{ex}")

        finally:
            VmManager.couninitial_pythoncom()


class MachineOperationApi(object):
    """
    远程计算机操作
    """
    def __init__(self, data):
        self.data =  data

    def get(self):
        """
        操作虚拟机
        """
        res_dict = dict(msg="请求成功", data=dict(), error_code=None)
        try:
            require_data = self.data
            ip_address = require_data['ip_address']
            machine_name = require_data['machine_name']
            task_type = require_data['task_type']
            host_ip, host_name, host_password = check_machineinfo(table_obj=VirtualMachineInfo, ip_address=ip_address)
            vmManager = VmManager(servername=host_ip, username=host_name, password=host_password)

            task_result = vmManager.run_operation(task_type, machine_name)
            task_state = get_enable_state(state1=task_result, enums=TaskStateEnum)
            res_dict['data'] = change_enums(task_state, ResponseEnum)
        except Exception as ex:
            loger.error(f"虚拟机查询异常：{ex}")
            res_dict['msg'] = "无法连接宿主机，检查宿主机是否正常运行"
            res_dict['error_code'] = 999

        finally:

            VmManager.couninitial_pythoncom()

        return res_dict

    def post(self):
        """
        获取应用
        """
        res_dict = dict(msg="请求成功", data=list(), error_code=None)
        try:
            require_data = self.data
            machine_name = require_data['machine_name']
            ip_address = require_data['ip_address']
            username = require_data['username']
            password = require_data['password']

            host_ip, host_name, host_password = update_virtualmachine(ip_address=ip_address, username=username,
                                                                     password=password, machine_name=machine_name)

            # ip地址不存在
            if not host_ip:
                # 逻辑待补充
                pass
            app = ApplicationManager(ipaddress=host_ip, username=host_name, password=host_password)
            app_list = app.find_application()
            temp_list = list()
            office_list = list()
            browser_list = list()
            uibot_list = list()
            other_list = list()
            if app_list:
                for item in app_list:

                    count = 0
                    for office in ApplicationEnum.Office.value:
                        if item.find(office) >= 0:
                            office_list.append(item)
                            count = count + 1
                            break
                    for browser in ApplicationEnum.Browser.value:
                        if item.find(browser) >= 0:
                            browser_list.append(item)
                            count = count + 1
                            break

                    for uibot in ApplicationEnum.UiBot.value:
                        if item.find(uibot) >= 0:
                            uibot_list.append(item)
                            count = count + 1
                            break

                    if not count:
                        other_list.append(item)

                for office, browser, uibot, other in zip_longest(office_list,browser_list,uibot_list,other_list):
                    application = dict(browser='', office='', uibot='', other='')
                    application['browser'] = browser
                    application['office'] = office
                    application['uibot'] = uibot
                    application['other'] = other
                    temp_list.append(application)

                res_dict['data'] = temp_list

        except Exception as ex:
            raise ex
            loger.error(f"虚拟机查询异常：{ex}")
            res_dict['msg'] = str(ex)
            res_dict['error_code'] = 999

        return res_dict


class AppOperationApi(object):

    """
    应用管理
    """
    def __init__(self, data):
        self.data =  data

    def get(self):
        """
        查询机器状态
        """

        res_dict = dict(msg="请求成功", data=list(), error_code=None)
        try:
            require_data = self.data
            ip_address = require_data['ip_address']
            machine_name = require_data['machine_name']
            host_ip, host_name, host_password = check_machineinfo(table_obj=VirtualMachineInfo, ip_address=ip_address)
            vmManager = VmManager(servername=host_ip, username=host_name, password=host_password)
            task_state = vmManager.find_one_virtual_machine(elementname=machine_name)
            if task_state:
                res_dict['data'] = change_enums(task_state, ResponseEnum)
            else:
                raise task_state
            # 获取单个虚拟机信息

        except Exception as ex:
            loger.error(f"查询状态异常：{ex}")
            res_dict['msg'] = str(ex)
            res_dict['error_code'] = 999

        return res_dict

    def post(self):

        res_dict = dict(msg="请求成功", data=list(), error_code=None)
        try:
            require_data = self.data
            machine_name = require_data['machine_name']
            path = require_data['path']
            # 获取单个虚拟机信息
            host_ip, host_name, host_password = check_machineinfo(table_obj=VirtualMachineInfo, machine_name=machine_name)

            app_manage = ApplicationManager(ipaddress=host_ip, username=host_name, password=host_password)
            status_code, std_out, std_err = app_manage.start_application(path=path)

            if status_code:
                res_dict['msg'] = str(std_err)
                res_dict['error_code'] = 999

        except Exception as ex:
            loger.error(f"启动程序异常：{ex}")
            res_dict['msg'] = str(ex)
            res_dict['error_code'] = 999

        return res_dict


class RunningMachine(object):

    """
    查询正在运行的虚拟机
    """

    def get(self):
        """
        查询机器状态
        """

        res_dict = dict(msg="请求成功", data=dict(), error_code=None)
        temp_list = []
        machine_list = list()
        try:

            with session() as db:
                environ_res = db.query(VirtualMachineInfo).filter(VirtualMachineInfo.machine_type == 'host').all()

            for environ_item in environ_res:
                host_ip = environ_item.ip_address
                host_name = environ_item.username
                host_password = environ_item.passwords

                try:
                    machine_list = check_running_virtualmachine(host_ip, host_name, host_password, machine_list, VmManager)
                    temp_list.extend(machine_list)
                except Exception as ex:
                    loger.error("查询正在运行的虚拟机失败", ex)

            res_dict['data']["virtual_machine"] = temp_list

            return res_dict

        except Exception as ex:
            loger.error(f"查询状态异常：{ex}")
            res_dict['msg'] = str(ex)
            res_dict['error_code'] = 999

        return res_dict