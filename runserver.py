import os
from flask_blog import create_app, db
from flask_blog.models import User,Article, Role
from flask_script import Manager, Shell  # 命令行选项
from flask_migrate import Migrate, MigrateCommand  # 数据迁移

app = create_app(os.getenv('FLASK_CONFIG') or 'default')
manager = Manager(app)
migrate = Migrate(app, db)

# 做些配置，让 Flask-Script 的 shell 命令自动导入特定的对象
# make_shell_context() 函数注册了程序、数据库实例以及模型，因此这些对象能直接导入 shell
def make_shell_context():
    return dict(app=app, db=db, User=User, Article=Article, Role=Role)
manager.add_command("shell", Shell(make_context=make_shell_context))

manager.add_command('db', MigrateCommand)

if __name__ == '__main__':
    manager.run()
