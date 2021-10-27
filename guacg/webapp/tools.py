import math
import re
import requests
from enum import Enum
from .models import VirtualMachineInfo, session
from .state_enums import ResponseEnum
from .configlogger import loger

UNKNOW_STATE = "未知"
WMI_JOB_STATE_RUNNING = 4096
DAY = 86400000
HOUR = 24
ZARO_HOUR = 0


def change_enums(enum_key, enum_class):
    for enum_item in enum_class:
        if enum_key == enum_item.name:
            return enum_item.value

    return enum_key


def get_enable_state(state1: int = '', state2: set = {}, enums: Enum = ''):

    for item in enums:

        if state1 == item.value:

            return item.name

        elif state2 == item.value:
            return item.name

    return UNKNOW_STATE


def calculate_time(running_time: int):
    if running_time:
        running_days = running_time/DAY
        hourstamp, days = math.modf(running_days)
        runing_hours = round(hourstamp * HOUR)
        return int(days), runing_hours
    else:
        return running_time, ZARO_HOUR


def check_machineinfo(table_obj: str = '', machine_name: str = '' , ip_address: str = ''):
        with session() as db:
            query_res = db.query(table_obj).filter(
                table_obj.machine_name == machine_name if machine_name else table_obj.ip_address == ip_address
            ).first()
        if query_res:
            return query_res.ip_address, query_res.username, query_res.passwords
        else:
            return  "","",""

def record_database(table_obj, data):
    with session() as db:
        query_res = db.query(table_obj).filter(
            table_obj.machine_name == data['Name']
        ).first()

    if not query_res:
        temp_machine = dict(machine_name=None, ip_address=None)
        temp_machine['machine_name'] = data['Name']
        temp_machine['ip_address'] = data['ipaddress']
        table_obj.add_one(temp_machine)
    elif not query_res.ip_address and data['ipaddress']:

        temp_machine = dict(ip_address=None)
        query_data = dict(machine_name=None)
        query_data['machine_name'] = data['Name']
        temp_machine['ip_address'] = data['ipaddress']
        table_obj.update_one(query_data, temp_machine)


def check_virtualmachineinfo(host_ip, host_name, host_password, machine_list, VmManager):

    # 查询宿主机下所有虚拟机信息
    vmManager = None
    try:

        vmManager = VmManager(servername=host_ip, username=host_name, password=host_password)
        temp_machine = vmManager.find_all_virtual_machine()

    except Exception as ex:

        loger.error(f"查询所有虚拟机异常: {ex}")
        raise ex

    finally:
        if vmManager:
            vmManager.couninitial_pythoncom()

    # 转化枚举值
    if temp_machine:
        for machine in temp_machine:
            machine['OperationalStatus'] = change_enums(machine['OperationalStatus'], ResponseEnum)
            machine['EnabledState'] = change_enums(machine['EnabledState'], ResponseEnum)
            machine['HealthState'] = change_enums(machine['HealthState'], ResponseEnum)
            # 添加宿主机ip
            machine['HostIp'] = host_ip
            record_database(VirtualMachineInfo, machine)

        machine_list.extend(temp_machine)
    return machine_list


def check_running_virtualmachine(host_ip, host_name, host_password, machine_list, VmManager):

    # 查询宿主机下所有虚拟机信息
    vmManager = None
    try:

        vmManager = VmManager(servername=host_ip, username=host_name, password=host_password)
        temp_machine = vmManager.find_running_virtual_machine()

    except Exception as ex:
        raise ex

    finally:
        if vmManager:
            vmManager.couninitial_pythoncom()

    machine_list.extend(temp_machine)
    return machine_list


def update_virtualmachine(ip_address=None, username=None, password=None, machine_name=None):

    virtual_machine = dict(machine_name=None)
    commit_info = dict(ip_address=None, username=None, passwords=None)
    virtual_machine['machine_name'] = machine_name
    if ip_address:

        commit_info['ip_address'] = ip_address
    else:
        commit_info.pop('ip_address')
    if username:
        commit_info['username'] = username
    else:
        commit_info.pop('username')
    if password:
        commit_info['passwords'] = password
    else:
        commit_info.pop('passwords')

    if commit_info:
        VirtualMachineInfo.update_one(virtual_machine, commit_info)

    host_ip, host_name, host_password = check_machineinfo(table_obj=VirtualMachineInfo, machine_name=machine_name)

    return host_ip, host_name, host_password


def parse_xml(content):

    for item in content:
        if item.find("NetworkAddressIPv4") >= 0:
            m = re.search("((2(5[0-5]|[0-4]\\d))|[0-1]?\\d{1,2})(\\.((2(5[0-5]|[0-4]\\d))|[0-1]?\\d{1,2})){3}", item)
            if m:
                return m.group()

    else:
        return ''


def request_client():
    requests.adapters.DEFAULT_RETRIES = 5  # 增加重连次数
    s = requests.session()
    s.keep_alive = False
    return s
