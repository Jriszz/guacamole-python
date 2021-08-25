from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from sqlalchemy import (create_engine, UniqueConstraint,Column,Integer,String,DateTime,JSON,Text,SmallInteger)
from sqlalchemy.orm import sessionmaker,scoped_session
from contextlib import contextmanager
from .configlogger import loger
__all__ = ["create_cursor", "EnvironConfig", "VirtualMachineInfo", "PackageRecord"]

# 初始化数据库连接

MYSQL_DB_CONNECT_STRING = "mysql+pymysql://uibot:uibot2020@192.168.0.111:3306/ferrymen?charset=utf8"
engine = create_engine(MYSQL_DB_CONNECT_STRING, echo=False, pool_size=250, max_overflow=50, pool_recycle=300)
Base = declarative_base(engine)
Session = scoped_session(sessionmaker(autocommit=False,
                                         autoflush=False,
                                         bind=engine,
                                         expire_on_commit=True))


# 创建会话对象
@contextmanager
def session(): #生成器函数
    try:
        session = Session()
        session.expire_on_commit = False
        yield session
    except Exception as ex:
        session.rollback()
        raise ex

    finally:
        session.close()


def create_cursor():
    engine = create_engine(
        "mysql+pymysql://nudt:nudt@192.168.0.61:3306/uibot_rpa?charset=utf8",
        max_overflow=0,  # 超过连接池大小外最多创建的连接
        pool_size=5,  # 连接池大小
        pool_timeout=30,  # 池中没有线程最多等待的时间，否则报错
        pool_recycle=-1,  # 多久之后对线程池中的线程进行一次连接的回收（重置）
    )

    conn = engine.raw_connection()
    cursor = conn.cursor()
    return cursor


class BaseTable(object):

    # 单个对象
    def sing_to_dict(self):
        return {c.name: getattr(self, c.name, None) for c in self.__table__.columns}

        # 多个对象

    def double_to_dict(self):
        """
        :return: result
        """

        return {
            key: str(getattr(self, key))
            if getattr(self, key)
            else {key: getattr(self, key)}
            for key in self.__mapper__.c.keys()
        }

    @classmethod
    def add_one(cls, obj):
        with session() as db:
            db.add(cls(**obj))
            db.flush()
            db.commit()

    @classmethod
    def update_one(cls, column_obj: dict, obj: dict):
        try:
            with session() as db:
                db.query(cls).filter_by(**column_obj).update(obj)
                db.commit()

        except Exception as ex:
            loger.error("更新数据异常: ", ex)
            raise ex


class EnvironConfig(Base, BaseTable):
    """环境配置"""

    __tablename__ = "environ_config"
    id = Column(Integer, nullable=False, primary_key=True, comment="id值")
    environ_name = Column(String(250), comment="测试环境")
    ip_address = Column(String(250), comment="ip地址")
    app_name = Column(String(250), comment="应用名称")
    update_time = Column(
        DateTime, default=datetime.now, onupdate=datetime.now, comment="修改时间"
    )
    author = Column(String(250), comment="安装人")
    create_time = Column(DateTime, default=datetime.now, comment="创建时间")
    app_path = Column(String(250), comment="应用路径")
    version_bit = Column(String(250), comment="应用位数")


class VirtualMachineInfo(Base, BaseTable):

    """虚拟机基本信息"""
    __tablename__ = "virtualmachine_info"
    id = Column(Integer, nullable=False, primary_key=True, comment="id值")
    machine_name = Column(String(250), comment="虚拟机名称")
    ip_address = Column(String(50), comment="虚拟机ip地址")
    username = Column(String(250), comment="虚拟机管理员用户名", default='administrator')
    passwords = Column(String(250), comment="虚拟机管理员密码", default="UiBot2019")
    machine_type = Column(String(50), comment="虚拟机类型", default='vm')


class PackageRecord(Base):
    """CI打包记录"""
    __tablename__ = "package_record"
    app_name = Column(String(128), nullable=False,  primary_key=True, comment="安装包名称")
    release_desc = Column(Text(), comment="发布描述")
    package = Column(String(16), nullable=False, comment="被测软件")
    edition = Column(String(16), nullable=False, comment="被测软件版本")
    version = Column(String(16), nullable=False, comment="被测软件版本号")
    arch = Column(String(8), nullable=False, comment="被测软件平台架构类型")
    language = Column(String(16), nullable=False, comment="语言包")
    channel = Column(String(32), nullable=False, comment="渠道")
    sign = Column(String(8), comment="签名")
    md5 = Column(String(32), nullable=False, comment="安装包md5")
    version_title = Column(String(32), nullable=False, comment="版本名称")
    fingerprint_k = Column(String(32), nullable=False, comment="版本指纹KEY")
    fingerprint_v = Column(JSON, nullable=False, comment="版本指纹VALUE")
    branch = Column(JSON, comment="版本分支信息")
    params = Column(JSON, comment="打包参数")
    source = Column(String(16), comment="来源")
    is_beta = Column(String(16), comment="是否beta版")
    is_release = Column(
        SmallInteger,
        nullable=False,
        default=0,
        comment="是否发布，第1位代表是否发布OSS，第2位代表是否创建tag，第3位代表已被补丁替代",
    )
    release_data = Column(JSON, comment="git release发布信息")
    release_result = Column(JSON, comment="git release发布结果")
    download_url = Column(Text(), nullable=False, comment="内网下载地址")
    fingerprint_url = Column(Text(), nullable=False, comment="内网版本地址")
    oss_download_url = Column(Text(), comment="外网下载地址")
    pdb_url = Column(Text(), comment="pdb文件下载地址")
    ip_address = Column(String(64), nullable=False, comment="IP地址")
    mac_address = Column(String(64), comment="MAC地址")
    patch_status = Column(
        SmallInteger,
        nullable=False,
        default=0,
        comment="补丁状态：0b0000不存在补丁，0b0001正在开补丁中，ob0010补丁创建成功未关闭，ob0100补丁已发布",
    )
    patch_name = Column(String(64), comment="补丁版本名称")
    patch_creator = Column(String(16), comment="补丁创建人")
    patch_id = Column(Integer, comment="补丁主键id")
    patch_branches = Column(JSON, comment="补丁分支信息")

    __table_args__ = (UniqueConstraint("version_title", "fingerprint_k"),)