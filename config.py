import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'this is a secret string'
    SQLALCHEMY_TRACK_MODIFICATIONS = True  # 设置True 取消警告
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True  # 每次请求结束后都会自动提交数据库中的变动
    BOOTSTRAP_SERVE_LOCAL = True # 使用本地 bootstrap 资源
    FLASKY_ADMIN = os.environ.get('FLASKY_ADMIN') # 配置管理员邮箱
    FLASKY_MAIL_SUBJECT_PREFIX = '[Flasky]'  # 邮件主题前缀
    FLASKY_MAIL_SENDER = 'Flasky Admin <yanwei4682@163.com>'  # 发件人邮箱
    FLASKY_ARTICLES_PER_PAGE = 10
    FLASKY_FOLLOWERS_PER_PAGE = 40
    FLASKY_COMMENTS_PER_PAGE = 20
    MAIL_SERVER = 'smtp.163.com'
    MAIL_PORT = 25
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')

    @staticmethod
    def init_app(app):
        pass


class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
                              'mysql+pymysql://root:4682@localhost:3306/blog_dev'


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URI') or \
                              'mysql+pymysql://root:4682@localhost:3306/blog_test'


class ProductionConfig(Config):
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
                              'mysql+pymysql://root:4682@localhost:3306/blog_prod'


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
