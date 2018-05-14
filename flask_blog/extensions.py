from flask_moment import Moment
from flask_login import LoginManager
from flask_mail import Mail
from flask_admin import Admin, AdminIndexView

moment = Moment()
mail = Mail()
flask_admin = Admin(name="后台管理",
                    index_view=AdminIndexView(
                        name='首页',
                        template='admin/custom.html',
                        url='/admin'
                        )
                    )

login_manager = LoginManager()
login_manager.session_protection = 'strong'
login_manager.login_view = 'auth.login'
login_manager.login_message = '请登录后再访问'