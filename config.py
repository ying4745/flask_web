import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'this is a secret string'

    SQLALCHEMY_TRACK_MODIFICATIONS = True  # 设置True 取消警告
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True  # 每次请求结束后都会自动提交数据库中的变动
    # BOOTSTRAP_SERVE_LOCAL = True # 使用本地 bootstrap 资源

    # 邮件发送配置
    MAIL_SERVER = 'smtp.qq.com'
    MAIL_PORT = 465
    MAIL_USE_TLS = False
    MAIL_USE_SSL = True
    MAIL_USERNAME = os.environ.get('DEV_DATABASE_URL')
    MAIL_PASSWORD = os.environ.get('DEV_DATABASE_URL')

    # reids缓存配置
    CACHE_TYPE = "redis"
    CACHE_REDIS_HOST = "127.0.0.1"
    CACHE_REDIS_PORT = 6379
    CACHE_REDIS_DB = 4


    # @staticmethod
    # def init_app(app):
    #     pass


class DevelopmentConfig(Config):
    # 开发模式
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
                              'mysql+pymysql://root:root@localhost:3306/blog_dev_new'


class TestingConfig(Config):
    #  测试模式
    TESTING = True
    pass


class ProductionConfig(Config):
    # 生产模式
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
