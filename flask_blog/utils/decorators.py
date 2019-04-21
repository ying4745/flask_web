from functools import wraps
from flask import abort, redirect, url_for
from flask_login import current_user
from flask_blog.models import Permission


# 检查用户权限的自定义装饰器
def permission_required(permission):
    def decorator(f):
        @wraps(f)
        def decorator_function(*args, **kwargs):
            if not current_user.can(permission):
                abort(403)
            return f(*args, **kwargs)

        return decorator_function

    return decorator


# 专门检查管理员权限的装饰器
def admin_required(f):
    return permission_required(Permission.ADMINISTER)(f)


# 检查用户邮箱是否确认的装饰器
def confirmed(f):
    @wraps(f)
    def decorator_function(*args, **kwargs):
        if not current_user.confirmed:
            return redirect(url_for('auth.unconfirmed'))
        return f(*args, **kwargs)

    return decorator_function
