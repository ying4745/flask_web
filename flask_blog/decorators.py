from functools import wraps
from flask import abort
from flask_login import current_user
from .models import Permission

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