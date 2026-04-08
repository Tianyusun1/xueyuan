from functools import wraps
from flask import abort, flash, redirect, url_for
from flask_login import current_user

def admin_required(f):
    """
    管理员权限拦截器
    用法: 在路由函数上方加上 @admin_required (必须放在 @login_required 之下)
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 如果用户未登录，或者不是管理员，拒绝访问
        if not current_user.is_authenticated or not current_user.is_admin:
            # 也可以选择 flash 提示并重定向到首页：
            # flash('越权访问拦截：您需要管理员权限才能执行此操作！', 'danger')
            # return redirect(url_for('auth.login'))
            abort(403) # 403 Forbidden 更加标准和硬核
        return f(*args, **kwargs)
    return decorated_function

def teacher_required(f):
    """
    教师权限拦截器
    注：有时管理员也需要能查看教师的页面，所以这里允许 admin 或 teacher 访问
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not (current_user.is_teacher or current_user.is_admin):
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

def student_required(f):
    """
    学生权限拦截器
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_student:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function