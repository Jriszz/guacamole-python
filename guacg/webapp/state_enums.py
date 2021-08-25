from enum import Enum


class EnableStateEnum(Enum):
    Enable = 2
    Disable = 3
    Shut_Down = 4
    Offline = 6
    Test = 7
    Defer = 8
    Quiesce = 9
    Starting = 10


class HealthStateEnum(Enum):
    OK = 5
    Major_Failure = 20
    Critical_Failure = 25


class OperationalStatusEnum(Enum):
    Creating_Snapshot = (11, 32768)
    Applying_Snapshot = (11, 32769)
    Deleting_Snapshot = (11, 32770)
    Waiting_Start = (11, 32771)
    Merge_Disks = (11, 32772)
    Export_Virtual_Machine = (11, 32773)
    Migrate_Virtual_Machine = (11, 32774)
    Operational_Status_OK = (2,)


class TaskStateEnum(Enum):
    Completed = 0
    TransitionStarted = 4096
    AccessDeined = 32769
    InvalidState = 32775


class ResponseEnum(Enum):
    Enable = '正在运行'
    Disable = '关机'
    Shut_Down = '关机状态'
    Offline = '已保存'
    Test = '测试状态'
    Defer = '延迟状态'
    Quiesce = '静止状态'
    Starting = '正在启动'
    OK = '正常'
    Major_Failure = '主要故障'
    Critical_Failure = '严重故障'
    Creating_Snapshot = '创建快照'
    Applying_Snapshot = '应用快照'
    Deleting_Snapshot = '删除快照'
    Waiting_Start = '正在等待'
    Merge_Disks = '合并磁盘'
    Export_Virtual_Machine = '导出虚拟机'
    Migrate_Virtual_Machine = '迁移虚拟机'
    Operational_Status_OK = '正常运行'
    Completed = '完成'
    TransitionStarted = '任务开始'
    AccessDeined = '拒绝访问'
    InvalidState = '非法状态'


class ApplicationEnum(Enum):
    Browser = ('Google Chrome', 'Firefox', 'IE', 'Microsoft Edge')
    Office = ('Microsoft Excel', 'Microsoft PowerPoint',
              'Microsoft Publisher', 'Microsoft Outlook',
              'Microsoft Word', 'Microsoft Access','Microsoft Office','Microsoft OneNote','Microsoft 365','WPS')
    UiBot = ('UiBot',)