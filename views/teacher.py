from datetime import datetime
from flask import Blueprint, render_template, request, flash, redirect, url_for, abort
from flask_login import login_required, current_user
from models import Course, Enrollment, Assignment, User
from extensions import db
from utils.decorators import teacher_required

# 创建教师蓝图
teacher_bp = Blueprint('teacher', __name__)


# 全局拦截：强制要求登录且必须是教师角色（或管理员巡查）
@teacher_bp.before_request
@login_required
@teacher_required
def require_teacher():
    pass


@teacher_bp.route('/dashboard')
def dashboard():
    """教师专属数据看板"""
    # 获取当前登录的老师名下的所有课程
    my_courses = Course.query.filter_by(teacher_id=current_user.id).order_by(Course.created_at.desc()).all()

    # 统计该老师名下，所有待批改的作业总数
    course_ids = [c.id for c in my_courses]
    pending_count = 0
    if course_ids:
        pending_count = Assignment.query.filter(
            Assignment.course_id.in_(course_ids),
            Assignment.status == 'pending'
        ).count()

    return render_template('teacher/dashboard.html', courses=my_courses, pending_count=pending_count)


@teacher_bp.route('/course/<int:course_id>/assignments')
def manage_assignments(course_id):
    """查看某门课程下的所有学员作品"""
    course = Course.query.get_or_404(course_id)

    # 【安全防范】越权校验：只能看自己的课
    if course.teacher_id != current_user.id and not current_user.is_admin:
        abort(403)

    # 获取该课程的所有作业，按提交时间倒序（最新的在最上面）
    assignments = Assignment.query.filter_by(course_id=course_id).order_by(Assignment.submit_time.desc()).all()

    return render_template('teacher/assignments.html', course=course, assignments=assignments)


@teacher_bp.route('/grade/<int:assignment_id>', methods=['POST'])
def grade_assignment(assignment_id):
    """批改学员作品（打分与写评语）"""
    assignment = Assignment.query.get_or_404(assignment_id)

    # 【安全防范】越权校验
    if assignment.course.teacher_id != current_user.id and not current_user.is_admin:
        abort(403)

    # 获取前端表单传过来的分数和评语
    score = request.form.get('score', type=int)
    feedback = request.form.get('feedback')

    # 更新数据库状态
    assignment.score = score
    assignment.feedback = feedback
    assignment.status = 'graded'
    assignment.review_time = datetime.utcnow()

    db.session.commit()
    flash('✅ 作品批改完成，分数已录入系统！', 'success')

    # 批改完后，重定向回该课程的作业列表页
    return redirect(url_for('teacher.manage_assignments', course_id=assignment.course_id))