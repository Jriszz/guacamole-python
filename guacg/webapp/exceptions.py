"""自定义异常类"""
# coding = utf-8
from flask import json
from werkzeug.exceptions import HTTPException


__all__ = [
    "HTTPException",
    "APIException",
    "DBExceptionException",
    "ParameterException",
    "UnAuthorizedException",
    "AuthFailedException",
    "PermissionDeniedException",
    "NotFoundException",
    "SiteAuthFailedException",
    "StatusMisMatchingException",
]


class APIException(HTTPException):

    def __init__(self, msg=None, code=None, error_code=None):
        """Receive custom parameters, override the method of __init__ """
        if msg:
            self.msg = msg
        if code:
            self.code = code
        if error_code:
            self.error_code = error_code
        super(APIException, self).__init__(msg, None)

    def get_body(self, environ=None):
        body = dict(msg=self.msg, error_code=self.error_code, data=None)
        text = json.dumps(body)
        return text

    def get_headers(self, environ=None):
        """Get a list of headers."""
        return [("Content-Type", "application/json")]


class DBExceptionException(APIException):
    code = 200
    msg = "参数错误"
    error_code = 1000


class ParameterException(APIException):
    code = 200
    msg = "参数错误"
    error_code = 1000


class UnAuthorizedException(APIException):
    """未认证"""

    code = 200
    error_code = 1005
    msg = "当前会话未认证"


class AuthFailedException(APIException):
    """认证失败"""

    code = 200
    error_code = 1005
    msg = "认证失败"


class SiteAuthFailedException(APIException):
    """来源站点不合法"""

    code = 200
    error_code = 1007
    msg = "来源站点不合法"


class PermissionDeniedException(APIException):
    """权限不足"""

    code = 200
    error_code = 1006
    msg = "权限不足，操作被拒绝"


class NotFoundException(APIException):
    code = 200
    msg = "找不到资源"
    error_code = 1002


class StatusMisMatchingException(APIException):
    """实体对象状态不符合操作要求"""

    code = 200
    msg = "找不到资源"
    error_code = 1008


class CustomFlaskError(Exception):
    '''
        :param resp_code 错误返回码
        :param resp_desc 错误描述
        :param payload 详细错误

    '''
    __slots__ = ('code','error_code','msg')

    def __init__(self,code=200, error_code=999, msg=None):
        self.code = code
        self.error_code = error_code
        self.msg = msg

    def to_dict(self):
        temp_dict = dict()
        temp_dict['code'] = self.code
        temp_dict['error_code'] = self.error_code
        if self.msg is not None:
            temp_dict['msg'] = self.msg
        return temp_dict