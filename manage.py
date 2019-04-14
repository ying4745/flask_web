#!/usr/bin/env python3
# -*- coding:utf-8 -*-

import os


COV = None
if os.environ.get('FLASK_COVERAGE'):  # 存在环境变量'FLASK_COVERAGE'则执行
    import coverage
    COV = coverage.coverage(branch=True, include='flask_blog/*')
    # branch=True选项开启分支覆盖分析，检查每个条件语句的 True 分支和 False 分支是否都执测试行了
    # include 选项用来限制程序包中文件的分析范围，不指定会包含虚拟环境等其他一下杂项的检查
    COV.start()

from flask_script import Manager, Shell  # 命令行选项
from flask_migrate import Migrate, MigrateCommand  #

from flask_blog import create_app, db
from flask_blog.models import User,Article, Role, Permission, \
    Follow, Comment, Tag, Category
from flask_blog.auth.forms import RegistrationForm

app = create_app(os.getenv('FLASK_CONFIG') or 'default')
manager = Manager(app)
migrate = Migrate(app, db)

# 做些配置，让 Flask-Script 的 shell 命令自动导入特定的对象
# make_shell_context() 函数注册了程序、数据库实例以及模型，因此这些对象能直接导入 shell
def make_shell_context():
    return dict(app=app, db=db, User=User, Article=Article, Role=Role, Tag=Tag,
                Permission=Permission, Follow=Follow, Comment=Comment, Category=Category)
manager.add_command("shell", Shell(make_context=make_shell_context))
manager.add_command('db', MigrateCommand)

@manager.command  # 装饰器-自定义命令  命令就是函数名
def test(coverage=False):
    """运行单元测试"""
    '''
    附加的命令行参数coverage会作为test()函数的一个bool类型的参数，
    如果命令行附加了该参数，coverage将会等于True
    '''
    if coverage and not os.environ.get('FLASK_COVERAGE'):
        import sys
        os.environ['FLASK_COVERAGE'] = '1'  # 环境变量不存在就添加环境变量
        os.execvp(sys.executable, [sys.executable] + sys.argv)
        # 添加完 重新执行当前文件
    import unittest
    tests = unittest.TestLoader().discover('tests')
    unittest.TextTestRunner(verbosity=2).run(tests)
    if COV:
        COV.stop()
        COV.save()
        print('报告总结：')
        COV.report()
        basedir = os.path.abspath(os.path.dirname(__file__))
        covdir = os.path.join(basedir, 'tmp/coverage')
        COV.html_report(directory=covdir)
        print('HTML version: file: //%s/index.html' % covdir)
        COV.erase()

# 创建管理员账户
@manager.command
def createsuperuser():
    username = input('请输入用户名：')
    email = input('请输入电子邮箱：')
    password = input('请输入密码：')
    password2 = input('再次输入密码：')
    form = RegistrationForm(username=username, email=email, password=password, password2=password2)
    if not form.validate():
        if 'csrf_token' in form.errors.keys() and len(form.errors) == 1:
            user = User(email=email, username=username, password=password)
            user.role = Role.query.filter_by(permissions=0xff).first()
            db.session.add(user)
            db.session.commit()
            print('创建管理账号成功')
        else:
            print(form.errors)
    else:
        print('创建不成功')

if __name__ == '__main__':
    manager.run()
