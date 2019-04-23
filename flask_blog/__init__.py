import os

from flask import Flask
from config import config
import flask_whooshalchemyplus
from flask_uploads import configure_uploads, patch_request_class

from .extensions import moment, mail, login_manager, flask_admin, avatar, \
    cache, assets_env, main_js, article_js
from .models import db, User, Article, Comment, Tag, Category
from . import admin  # 必须先导入上面的


flask_admin.add_view(admin.UserView(User, db.session, name='用户管理'))
flask_admin.add_view(admin.ArticleView(Article, db.session, name='文章管理'))
flask_admin.add_view(admin.CommentView(Comment, db.session, name='评论管理'))
flask_admin.add_view(admin.TagView(Tag, db.session, name='标签管理'))
flask_admin.add_view(admin.CategoryView(Category, db.session, name='分类管理'))
flask_admin.add_view(admin.StaticFileAdmin(
    os.path.join(os.path.dirname(__file__), 'static'), '/static', name='文件管理'))
flask_admin.add_view(admin.CustomView(name='返回网站'))


def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    app.config.from_object('setting')
    # config[config_name].init_app(app)  # 调用 init_app() 可以完成初始化过程

    db.init_app(app)
    moment.init_app(app)
    mail.init_app(app)
    login_manager.init_app(app)
    flask_admin.init_app(app)
    flask_whooshalchemyplus.init_app(app)

    # 上传文件
    configure_uploads(app, avatar)
    patch_request_class(app, 6*1024*1024)  # 限制上传大小 6M

    cache.init_app(app)  # 缓存

    assets_env.init_app(app)  # 压缩css/js
    # assets_env.register('main_css', main_css)
    assets_env.register('main_js', main_js)
    assets_env.register('article_js', article_js)

    from .main import main as main_blueprint  # 注册蓝本
    app.register_blueprint(main_blueprint)

    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint, url_prefix='/auth')  # 附加路由前缀/auth

    return app
