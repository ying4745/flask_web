from flask import Blueprint

main = Blueprint('main', __name__)
# 实例化 Blueprint 类对象可以创建蓝本。构造函数有两个必须指定的参数：
# 蓝本的名字和蓝本所在的包或模块。第二个通常填'__name__'

from . import views, errors
from ..models import Permission


@main.app_context_processor
def inject_permissions():
    return dict(Permission=Permission)
