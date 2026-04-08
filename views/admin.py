from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required
from sqlalchemy import func
from models import User, Course, Enrollment, Assignment
from extensions import db
from utils.decorators import admin_required

# 创建管理员蓝图
admin_bp = Blueprint('admin', __name__)


# 这是一个极其好用的钩子函数：
# 它会拦截所有发往 /admin/... 的请求，强制进行登录和管理员权限校验
# 这样你就不用在下面的每一个路由函数上都写一遍 @login_required 和 @admin_required 了
@admin_bp.before_request
@login_required
@admin_required
def require_admin():
    pass


@admin_bp.route('/dashboard')
def dashboard():
    """管理员动态数据看板"""
    # 1. 核心指标统计
    total_students = User.query.filter_by(role='student').count()
    total_teachers = User.query.filter_by(role='teacher').count()
    total_courses = Course.query.count()

    # 计算总营收 (通过 sqlalchemy 的 func.sum)
    revenue_result = db.session.query(func.sum(Enrollment.amount_paid)).scalar()
    total_revenue = revenue_result if revenue_result else 0.0

    # 2. 课程热度排行 (取报名人数最多的前 5 门课)
    # 通过联表查询并按报名人数降序排列
    popular_courses = db.session.query(
        Course.title,
        func.count(Enrollment.id).label('student_count')
    ).outerjoin(Enrollment).group_by(Course.id).order_by(db.text('student_count DESC')).limit(5).all()

    # 3. 待处理任务 (全校还有多少份作品没批改)
    pending_assignments = Assignment.query.filter_by(status='pending').count()

    return render_template('admin/dashboard.html',
                           total_students=total_students,
                           total_teachers=total_teachers,
                           total_courses=total_courses,
                           total_revenue=total_revenue,
                           popular_courses=popular_courses,
                           pending_assignments=pending_assignments)


@admin_bp.route('/courses', methods=['GET', 'POST'])
def manage_courses():
    """课程管理与发布"""
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        price = request.form.get('price', type=float)
        max_students = request.form.get('max_students', type=int)
        teacher_id = request.form.get('teacher_id', type=int)

        new_course = Course(
            title=title,
            description=description,
            price=price,
            max_students=max_students,
            teacher_id=teacher_id
        )
        db.session.add(new_course)
        db.session.commit()
        flash(f'课程《{title}》发布成功！', 'success')
        return redirect(url_for('admin.manage_courses'))

    # GET 请求：获取所有课程和所有教师列表（用于下拉菜单）
    courses = Course.query.order_by(Course.created_at.desc()).all()
    teachers = User.query.filter_by(role='teacher').all()

    return render_template('admin/courses.html', courses=courses, teachers=teachers)


@admin_bp.route('/teachers', methods=['GET', 'POST'])
def manage_teachers():
    """师资库管理（分配教师账号）"""
    if request.method == 'POST':
        username = request.form.get('username')
        real_name = request.form.get('real_name')
        password = request.form.get('password')

        if User.query.filter_by(username=username).first():
            flash('该登录账号已存在，请更换！', 'warning')
        else:
            new_teacher = User(username=username, real_name=real_name, role='teacher')
            new_teacher.set_password(password)
            db.session.add(new_teacher)
            db.session.commit()
            flash(f'教师账号 {real_name} 分配成功！', 'success')

        return redirect(url_for('admin.manage_teachers'))

    # GET 请求：展示所有教师
    teachers = User.query.filter_by(role='teacher').order_by(User.created_at.desc()).all()
    return render_template('admin/teachers.html', teachers=teachers)