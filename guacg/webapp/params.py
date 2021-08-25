from wtforms import Form
from wtforms.validators import Length, DataRequired,Optional
from wtforms.fields import StringField,  IntegerField
from .exceptions import CustomFlaskError
import wtforms_json
from flask import  request
wtforms_json.init()


class JsonForm(Form):

    @classmethod
    def init_and_validate(cls):
        wtforms_json.init()

        if request.method == 'GET':
            form = cls.from_json(request.args.to_dict())
            valid = form.validate()
        else:
            form = cls.from_json(request.get_json())
            valid = form.validate()

        if not valid:

            valid = form.validate()
            if not valid:
                raise CustomFlaskError(msg=form.errors)
            else:
                return form
        return form


class GetEnvironParams(JsonForm):

    page = IntegerField('page', validators = [Length(min=1, max=3)], default=1)
    page_size = IntegerField('page_size', validators = [Length(min=1, max=3)], default=10)
    search_condition = StringField('search_condition', default=None)
    id = IntegerField('id', default=None)


class DelEnvironParams(JsonForm):
    ip_address = StringField('ip_address', validators = [DataRequired(),Length(min=1,max=99)])
    app_name = StringField('app_name', validators = [DataRequired(),Length(min=1,max=99)])
    version_bit = StringField('version_bit', validators = [DataRequired(),Length(min=1,max=99)])
    environ_id = StringField('environ_id', validators = [DataRequired(),Length(min=1,max=99)])


class AddEnvironParams(JsonForm):

    ip_address = StringField('ip_address', validators = [DataRequired()])
    app_name = StringField('app_name', validators = [DataRequired()])
    environ_name = StringField('environ_name', validators = [DataRequired()])
    version_bit = StringField('version_bit', validators = [DataRequired()])
    version_bit = StringField('app_path', validators = [DataRequired()])


class PutEnvironParams(JsonForm):

    environ_id = StringField('environ_id', validators = [DataRequired()])
    ip_address = StringField('ip_address', validators = [DataRequired()])
    app_name = StringField('app_name', validators = [DataRequired()])
    environ_name = StringField('environ_name', validators = [DataRequired()])
    version_bit = StringField('version_bit', validators = [DataRequired()])
    app_path = StringField('app_path', validators = [DataRequired()])


class GetEnvironInfo(JsonForm):

    app_name = StringField('app_name', validators = [DataRequired()])
    environ_name = StringField('environ_name', validators = [DataRequired()])
    version_bit = StringField('version_bit', validators = [DataRequired()])
    app_path = StringField('app_path', validators = [DataRequired()])


class GetVirtualMachine(JsonForm):

    machine_name = StringField('machine_name', validators = [Optional()], default="")


class RunVirtualMachine(JsonForm):

    machine_name = StringField('machine_name', validators = [DataRequired()])
    ip_address = StringField('ip_address', validators = [DataRequired()])
    task_type = IntegerField('task_type', validators = [DataRequired()])


class VirtualMachineInfo(JsonForm):

    machine_name = StringField('machine_name', validators = [DataRequired()])
    username = StringField('username',  default="")
    password = StringField('password',  default="")
    ip_address = StringField('ip_address',  default="")


class RunApplication(JsonForm):

    machine_name = StringField('machine_name', default="")
    path = StringField('path', default="")


class CheckMachineState(JsonForm):

    ip_address = StringField('ip_address', validators = [DataRequired()], default="")
    machine_name = StringField('machine_name', validators = [DataRequired()],  default="")


class CheckService(JsonForm):

    ip_address = StringField('ip_address', validators = [DataRequired()], default="")


class ModifyIp(JsonForm):
    machine_name = StringField('machine_name', validators = [DataRequired()], default="")
    ip_address = StringField('ip_address', validators = [Optional()], default="")
    username = StringField('username', validators=[Optional()], default="")
    password = StringField('password',  validators=[Optional()], default="")
