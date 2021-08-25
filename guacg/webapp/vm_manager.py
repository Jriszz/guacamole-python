import wmi
import copy
import pythoncom
from .configlogger import loger
from .tools import calculate_time, get_enable_state, parse_xml,check_machineinfo
from wmi import _wmi_object, _wmi_namespace
from .models import VirtualMachineInfo,session
from .state_enums import EnableStateEnum, HealthStateEnum, OperationalStatusEnum


class VmManager(object):
    """
    虚拟机管理
    :author:zz
    :time: 2021.06.01
    """

    def __init__(self, servername: str = '.', namespace: str = r"root\virtualization\v2",
                 username: str = '', password: str = ''):
        try:
            pythoncom.CoInitialize()
            connection = wmi.connect_server(server=servername, namespace=namespace, user=username, password=password)

            self.wmiServerConnection = wmi.WMI(wmi=connection)

        except Exception as ex:
            loger.error(f"连接宿主机异常：{ex}")
            raise ex

    def create_virtual_machine(self, virtual_name: str = '新建虚拟机', vhd_file: str = "",
                               iso_image: str = "", memory_amount: int = 4096, cpu_amount: int = 4):
        try:

            vm_management = self.wmiServerConnection.Msvm_VirtualSystemManagementService()[0]
            vm_setdata = self.wmiServerConnection.Msvm_VirtualSystemSettingData()[0]
            vm_setdata.ElementName = virtual_name
            vm_management.DefineSystem(ResourceSettings=[],
                                             ReferenceConfiguration=None,
                                             SystemSettings=vm_setdata.GetText_(1))

            vm = self.wmiServerConnection.Msvm_ComputerSystem(ElementName=virtual_name)[0]
            # get settings
            vm_settings = vm.associators(
                wmi_result_class='Msvm_VirtualSystemSettingData')
            vm_setting = vm_settings[0]
            mem_setting = vm_setting.associators(
                wmi_result_class='Msvm_MemorySettingData')[0]
            cpu_settings = vm_setting.associators(
                wmi_result_class='Msvm_ProcessorSettingData')[0]
            rasds = vm_setting.associators(
                wmi_result_class='MSVM_ResourceAllocationSettingData')

            self._set_memory(memory_amount, vm_management, mem_setting)
            self._set_cpus(cpu_amount, cpu_settings, vm_management)
            if vhd_file:
                self._create_vhd(vm=vm, conn=self.wmiServerConnection, path=vhd_file)
                ####
                self._add_vhd(vhd_file, iso_image, self.wmiServerConnection, rasds, vm_management, vm)
            else:
                pass
        except Exception as ex:
            pass

    def run_operation(self, task_type: int = 0, machine_name: str = ''):

        system = self.wmiServerConnection.Msvm_ComputerSystem(Name= machine_name)[0]

        task_job = system.RequestStateChange(task_type)

        return task_job[1]

    def find_applicaiton(self):

        applications = self.wmiServerConnection.Win32_ShortcutFile()
        return applications

    def find_one_virtual_machine(self, elementname):
        system_list = self.wmiServerConnection.Msvm_ComputerSystem(Name=elementname)
        machine_state = ''
        if system_list:
            machine_state = get_enable_state(state1=system_list[0].EnabledState, enums=EnableStateEnum)
        return machine_state

    def find_all_virtual_machine(self):

        system_abstract = dict(ElementName=None, EnabledState=None, HealthState=None,
                               Name=None, Day=None, Hour=None, InstallDate=None,
                               ipaddress=None, username=None, password=None)

        all_virtual_machine_info = list()
        system_list = self.wmiServerConnection.Msvm_ComputerSystem()
        network_configure = self._get_all_networkconfigure(self.wmiServerConnection)

        if system_list:
            for machine in system_list[1:]:
                temp_dict = copy.copy(system_abstract)
                temp_dict['ElementName'] = machine.ElementName
                temp_dict['OperationalStatus'] = get_enable_state(state2=machine.OperationalStatus, enums= OperationalStatusEnum)
                temp_dict['EnabledState'] = get_enable_state(state1=machine.EnabledState, enums=EnableStateEnum)
                temp_dict['HealthState'] = get_enable_state(state1=machine.HealthState, enums=HealthStateEnum)
                temp_dict['Name'] = machine.Name
                temp_dict['ipaddress'] = self._get_address(network_configure, machine.Name)


                # 查注册表
                if not temp_dict['ipaddress'] and temp_dict['EnabledState'] == 'Enable':

                    temp_dict['ipaddress'] = self.get_address2(machine_name=machine.name)

                if temp_dict['ipaddress']:

                    with session() as db:
                        ip_res = db.query(VirtualMachineInfo.ip_address).filter(VirtualMachineInfo.machine_name == temp_dict['Name']).first()

                    if ip_res[0] != temp_dict['ipaddress']:
                        VirtualMachineInfo.update_one({"machine_name": temp_dict['Name']}, {"ip_address": temp_dict['ipaddress']})

                # 查数据库
                if not temp_dict['ipaddress']:

                    temp_dict['ipaddress'], _, _ = check_machineinfo(table_obj=VirtualMachineInfo, machine_name=temp_dict['Name'])

                _, temp_dict['username'], temp_dict['password'] = check_machineinfo(table_obj=VirtualMachineInfo, machine_name=temp_dict['Name'])

                temp_dict['Day'], temp_dict['Hour'] = calculate_time(running_time=int(machine.OnTimeInMilliseconds))
                temp_dict['InstallDate'] = machine.InstallDate[0:8]

                all_virtual_machine_info.append(temp_dict)

            return all_virtual_machine_info
        else:
            return system_list

    def find_running_virtual_machine(self):

        system_abstract = dict(ElementName=None, Name=None, ipaddress=None)
        system_list = list()
        all_virtual_machine_info = list()
        try:
            system_list = self.wmiServerConnection.Msvm_ComputerSystem(EnabledState= 2)
        except Exception as ex:
            loger.error("查询正在运行虚拟机失败", ex)

        network_configure = self._get_all_networkconfigure(self.wmiServerConnection)

        if system_list:
            for machine in system_list[1:]:
                temp_dict = copy.copy(system_abstract)
                temp_dict['ElementName'] = machine.ElementName
                temp_dict['Name'] = machine.Name
                temp_dict['ipaddress'] = self._get_address(network_configure, machine.Name)

                # 查注册表
                if not temp_dict['ipaddress']:

                    temp_dict['ipaddress'] = self.get_address2(machine_name=machine.name)

                # 查数据库
                if not temp_dict['ipaddress']:

                    temp_dict['ipaddress'], _, _ = check_machineinfo(table_obj=VirtualMachineInfo, machine_name=temp_dict['Name'])

                if temp_dict['ipaddress']:
                    all_virtual_machine_info.append(temp_dict)

            return all_virtual_machine_info
        else:
            return system_list

    @staticmethod
    def _get_all_networkconfigure(conn):

        return conn.Msvm_GuestNetworkAdapterConfiguration()

    @staticmethod
    def _get_address(network_configure: list = [], machine_name: str = ''):
        # 获取虚拟机ip地址

        for configure in network_configure:

            if configure.InstanceID.find(machine_name) >= 0 and configure.IPAddresses:
                ipaddress = configure.IPAddresses[0]
                return ipaddress

        return ''

    def get_address2(self, machine_name: str = ''):

        vmSystem = self.wmiServerConnection.Msvm_ComputerSystem(Name= machine_name)[0]
        vmSystemdevice = vmSystem.associators(wmi_association_class='Msvm_SystemDevice',
                                            wmi_result_class='Msvm_KvpExchangeComponent')

        if vmSystemdevice:
            xml_content = vmSystemdevice[0].GuestIntrinsicExchangeItems

            if xml_content:
                ip_address = parse_xml(xml_content)
                return ip_address

        return ''

    @staticmethod
    def _create_other_connection(servername: str = '.', namespace: str = r"root\virtualization\v2",
                                username: str = '', password: str = ''):

        connection = wmi.connect_server(server=servername, namespace=namespace, user=username, password=password)

        return wmi.WMI(wmi=connection)

    @staticmethod
    def _set_memory(memory_mb: int = 4096,  hyperv_management: _wmi_object = '', mem_setting: _wmi_object = ''):
        mem = memory_mb
        mem_setting.VirtualQuantity = mem
        mem_setting.Reservation = mem
        mem_setting.Limit = mem
        hyperv_management.ModifyResourceSettings(ResourceSettings=[mem_setting.GetText_(1)])

    @staticmethod
    def _set_cpus(self, vcpus: str = '', cpu_settings: _wmi_object = '', hyperv_management: _wmi_object = ''):
        vcpus = str(vcpus)
        cpu_settings.VirtualQuantity = vcpus
        cpu_settings.Reservation = vcpus
        cpu_settings.Limit = 100000  # static assignment to 100%
        hyperv_management.ModifyResourceSettings(ResourceSettings=[cpu_settings.GetText_(1)])

    @staticmethod
    def _create_vhd(conn: _wmi_namespace = '', path: str = '', element_name: str = 'vhdx',
                    caption_name: str = 'new_vhdx', disk_type: int = 3, formats: int = 3,
                    maxintersize: int = 42949672960,physicalsector: int = 4096, logicalsector: int = 512):

        vm_image_manage = conn.Msvm_ImageManagementService()[0]
        disk_set_data = conn.Msvm_VirtualHardDiskSettingData.new()
        disk_set_data.BlockSize = 0
        disk_set_data.MaxInternalSize = maxintersize
        disk_set_data.Caption = caption_name
        disk_set_data.Path = path
        disk_set_data.Type = disk_type
        disk_set_data.ElementName = element_name
        disk_set_data.Format = formats
        disk_set_data.PhysicalSectorSize = physicalsector
        disk_set_data.LogicalSectorSize = logicalsector
        vm_image_manage.CreateVirtualHardDisk(disk_set_data.GetText_(1))

    def _add_vhd(self, vhdfile: str = '', dvdfile: str = '', conn: _wmi_namespace = '', rasds: _wmi_object = '', \
                 hyperv_management: _wmi_object = '', vm: _wmi_object = ''):

        ide_controller = [r for r in rasds
                          if r.ResourceSubType == 'Microsoft:Hyper-V:Emulated IDE Controller' and r.Address == "0"][0]
        ide2_controller = [r for r in rasds
                           if r.ResourceSubType == 'Microsoft:Hyper-V:Emulated IDE Controller' and r.Address == "1"][0]
        # create hard disk
        '''
        '''
        hard_disk_default = conn.query(
            "SELECT * FROM Msvm_ResourceAllocationSettingData \
            WHERE ResourceSubType LIKE 'Microsoft:Hyper-V:Synthetic Disk Drive'\
            AND InstanceID LIKE '%Default%'")[0]
        disk_drive = self._clone_wmi_obj(conn,
                                         'Msvm_ResourceAllocationSettingData', hard_disk_default)
        disk_drive.Parent = ide_controller.path_()
        disk_drive.Address = 0
        disk_drive.AddressOnParent = 0
        res_xml = [disk_drive.GetText_(1)]
        job_path, new_resources, _ = hyperv_management.AddResourceSettings(vm.path_(), res_xml)
        hard_disk_drive_path = new_resources[0]

        # create the dvd disk

        dvd_disk_default = conn.query(
            "SELECT * FROM Msvm_ResourceAllocationSettingData \
            WHERE ResourceSubType LIKE 'Microsoft:Hyper-V:Synthetic DVD Drive'\
            AND InstanceID LIKE '%Default%'")[0]
        dvd_disk_drive = self._clone_wmi_obj(conn,
                                             'Msvm_ResourceAllocationSettingData', dvd_disk_default)
        dvd_disk_drive.Parent = ide2_controller.path_()
        dvd_disk_drive.Address = 0
        dvd_disk_drive.AddressOnParent = 1
        res_xml = [dvd_disk_drive.GetText_(1)]
        job_path, new_resources, _ = hyperv_management.AddResourceSettings(vm.path_(), res_xml)

        dvd_disk_drive_path = new_resources[0]
        '''
        # Find the default VHD disk object.
        '''
        vhd_default = conn.query(
            "SELECT * FROM Msvm_StorageAllocationSettingData \
            WHERE ResourceSubType = 'Microsoft:Hyper-V:Virtual Hard Disk' AND \
            InstanceID LIKE '%%\\Default' ")[0]
        # Clone the default and point it to the image file.
        vhd_disk = self._clone_wmi_obj(conn,
                                       'Msvm_StorageAllocationSettingData', vhd_default)

        vhd_disk.Parent = hard_disk_drive_path
        vhd_disk.HostResource = [vhdfile]
        hyperv_management.AddResourceSettings(vm.path_(), [vhd_disk.GetText_(1)])

        # install the default DVD disk object
        dvd_default = conn.query(
            "SELECT * FROM Msvm_StorageAllocationSettingData \
            WHERE ResourceSubType = 'Microsoft:Hyper-V:Virtual CD/DVD Disk' AND \
            InstanceID LIKE '%%\\Default' ")[0]
        # Clone the default and point it to the image file.
        dvd_disk = self._clone_wmi_obj(conn,
                                       'Msvm_StorageAllocationSettingData', dvd_default)

        dvd_disk.Parent = dvd_disk_drive_path
        dvd_disk.HostResource = [dvdfile]
        hyperv_management.AddResourceSettings(vm.path_(), [dvd_disk.GetText_(1)])

    @staticmethod
    def _clone_wmi_obj(conn: _wmi_namespace = '', wmi_class: str = '', wmi_obj: _wmi_object = ''):
        """Clone a WMI object"""
        cl = getattr(conn, wmi_class)  # get the class
        newinst = cl.new()
        # Copy the properties from the original.
        for prop in wmi_obj._properties:
            newinst.Properties_.Item(prop).Value = \
                wmi_obj.Properties_.Item(prop).Value
        return newinst

    def wait_for_job(self,  concreteJob: str = ''):
        pass
        # instance_id = concreteJob[0].split('=')[1]
        # job_list = self.wmiServerConnection.Msvm_StorageJob()
        # for job in job_list:
        #     if job.InstanceID == instance_id:
        #         print(job.JobState, job.ErrorDescription, job.GetErrorEx())
        # return job

    @staticmethod
    def couninitial_pythoncom():

        pythoncom.CoUninitialize()