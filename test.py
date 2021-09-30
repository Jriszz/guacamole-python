import winrm

username = "uibottest"
password = "UiBot2019"
ipaddress = "192.168.0.221"

if __name__ == "__main__":
    winsession = winrm.Session(f'http://{ipaddress}:5985/wsman', auth=(username, password))
    print(winsession)
    item = ['HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\',
                      'HKEY_LOCAL_MACHINE\\SOFTWARE\\WOW6432Node\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\']

    # ret = winsession.run_cmd( f"REG QUERY  {item[1]} /S /v DisplayName")
    ret = winsession.run_cmd("ipconfig")
    print(ret)