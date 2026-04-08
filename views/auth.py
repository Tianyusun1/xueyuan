from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_user, logout_user, login_required, current_user
from models import User
from extensions import db

# 创建鉴权蓝图
auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    # 如果用户已经登录，直接根据角色送他去对应的后台，防止重复登录
    if current_user.is_authenticated:
        return redirect_based_on_role(current_user)

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        # 数据库查询比对
        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            # 密码正确，在 Session 中记录用户状态
            login_user(user)
            flash(f'欢迎回来，{user.real_name}！', 'success')

            # 核心动作：根据不同角色重定向到不同页面
            return redirect_based_on_role(user)
        else:
            flash('用户名或密码错误，请重试。', 'danger')

    # GET 请求：渲染登录页面
    return render_template('auth/login.html')


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect_based_on_role(current_user)

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        real_name = request.form.get('real_name')

        # 检查用户名是否已被占用
        if User.query.filter_by(username=username).first():
            flash('该用户名已被注册，请换一个。', 'warning')
            return redirect(url_for('auth.register'))

        # 创建新用户（注意：对外开放注册的只能是 'student' 角色）
        # 老师和管理员账号必须由系统后台生成
        new_user = User(username=username, real_name=real_name, role='student')
        new_user.set_password(password)

        db.session.add(new_user)
        db.session.commit()

        flash('注册成功！请登录。', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html')


@auth_bp.route('/logout')
@login_required
def logout():
    """安全退出路由"""
    logout_user()
    flash('您已成功退出登录。', 'info')
    return redirect(url_for('auth.login'))


# --- 辅助函数 ---
def redirect_based_on_role(user):
    """
    智能路由分发中心
    根据用户的 role 字段，将其导向不同的蓝图首页
    """
    if user.is_admin:
        return redirect(url_for('admin.dashboard'))
    elif user.is_teacher:
        return redirect(url_for('teacher.dashboard'))
    elif user.is_student:
        return redirect(url_for('student.dashboard'))
    else:
        # 兜底防护
        logout_user()
        flash('账户角色异常，请联系系统管理员。', 'danger')
        return redirect(url_for('auth.login'))