import winrm
from .configlogger import loger


class ApplicationManager(object):
    """
    应用操作
    :author: 2021/07/01
    :time: 2021.07.01
    """
    def __init__(self, ipaddress: str = '.',username: str = '', password: str = ''):
        try:
            self.winsession = winrm.Session(f'http://{ipaddress}:5985/wsman', auth=(username, password))

        except Exception as ex:
            loger.error(f"创建远程计算机会话异常：{ex}")
            raise ex

    def start_application(self, path: str = ""):
        ret = self.winsession.run_cmd(r"schtasks /query /tn MyTaskName")
        is_task = ret.status_code
        path = repr(path)
        replace_path = path.replace("'", '\\"')
        if is_task:
            self.winsession.run_cmd(rf'schtasks /create /tn MyTaskName /st 01:00  /sc ONCE /tr "{replace_path} /verysilent" /rl HIGHEST')
            ret = self.winsession.run_cmd(r"schtasks /run /tn MyTaskName")
            return ret.status_code,ret.std_out,ret.std_err
        else:
            self.winsession.run_cmd(rf"schtasks /delete /F /tn MyTaskName")
            self.winsession.run_cmd(rf'schtasks /create /tn MyTaskName /st 01:00  /sc ONCE /tr "{replace_path} /verysilent" /rl HIGHEST')
            ret = self.winsession.run_cmd(r"schtasks /run /tn MyTaskName")
            return ret.status_code, ret.std_out, ret.std_err

    def find_application(self):
        check_list = ['HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\',
                      'HKEY_LOCAL_MACHINE\\SOFTWARE\\WOW6432Node\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\']

        app_list2 = list()
        for item in check_list:
            ret = self.winsession.run_cmd( f"REG QUERY  {item} /S /v DisplayName")

            is_error = ret.status_code
            if not is_error:
                content = ret.std_out
                app = content.decode('utf-8')
                app_list = app.splitlines()
                res = filter(lambda x: x.find('HKEY_LOCAL_MACHINE') < 0 and x != '', app_list)

                for item in res:
                    app = item.split('  ')[-1]
                    app_list2.append(app)

        return app_list2[:-2]