import os
import uuid
from datetime import datetime
from werkzeug.utils import secure_filename
from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app, abort
from flask_login import login_required, current_user
from models import Course, Enrollment, Assignment
from extensions import db
from utils.decorators import student_required

# 创建学员蓝图
student_bp = Blueprint('student', __name__)


# 全局拦截：强制要求登录且必须是学员角色
@student_bp.before_request
@login_required
@student_required
def require_student():
    pass


# --- 辅助函数：检查文件格式 ---
def allowed_file(filename):
    """验证上传的文件是否为允许的图片格式"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']


@student_bp.route('/dashboard')
def dashboard():
    """学员个人中心（看板）"""
    # 获取我已经报名的课程
    enrollments = Enrollment.query.filter_by(student_id=current_user.id).order_by(Enrollment.enroll_time.desc()).all()
    # 获取我最近提交的摄影作品
    recent_assignments = Assignment.query.filter_by(student_id=current_user.id).order_by(
        Assignment.submit_time.desc()).limit(5).all()

    return render_template('student/dashboard.html', enrollments=enrollments, assignments=recent_assignments)


@student_bp.route('/courses')
def course_market():
    """选课大厅（浏览全站课程）"""
    # 查找所有老师已分配的课程
    courses = Course.query.filter(Course.teacher_id.isnot(None)).order_by(Course.created_at.desc()).all()
    # 查出当前学员已经报名的课程 ID 列表，用于在前端把按钮变成“已报名”
    enrolled_course_ids = [e.course_id for e in current_user.enrollments]

    return render_template('student/market.html', courses=courses, enrolled_course_ids=enrolled_course_ids)


@student_bp.route('/enroll/<int:course_id>', methods=['POST'])
def enroll_course(course_id):
    """模拟支付与选课逻辑"""
    course = Course.query.get_or_404(course_id)

    # 1. 检查是否已经报名过
    if Enrollment.query.filter_by(student_id=current_user.id, course_id=course_id).first():
        flash('您已经报名过该课程，无需重复缴费。', 'warning')
        return redirect(url_for('student.course_market'))

    # 2. 检查课程是否满员
    if course.current_students_count >= course.max_students:
        flash('抱歉，该课程名额已满！', 'danger')
        return redirect(url_for('student.course_market'))

    # 3. 模拟支付成功，生成选课订单
    new_enrollment = Enrollment(
        student_id=current_user.id,
        course_id=course.id,
        amount_paid=course.price
    )
    db.session.add(new_enrollment)
    db.session.commit()

    flash(f'🎉 支付成功！您已正式加入《{course.title}》课程。', 'success')
    return redirect(url_for('student.dashboard'))


@student_bp.route('/course/<int:course_id>/workspace', methods=['GET', 'POST'])
def workspace(course_id):
    """学习空间与作品上传中心"""
    # 验证该学生是否真的报了这门课
    enrollment = Enrollment.query.filter_by(student_id=current_user.id, course_id=course_id).first()
    if not enrollment:
        abort(403)  # 没交钱别想看

    course = Course.query.get_or_404(course_id)

    # --- 核心逻辑：处理摄影作品上传 ---
    if request.method == 'POST':
        if 'photo' not in request.files:
            flash('没有选择文件', 'danger')
            return redirect(request.url)

        file = request.files['photo']
        if file.filename == '':
            flash('没有选择文件', 'danger')
            return redirect(request.url)

        if file and allowed_file(file.filename):
            # 1. 安全化文件名
            original_filename = secure_filename(file.filename)
            # 2. 生成唯一标识符重命名文件，防止多个学员上传同名文件(如 DSC001.jpg)导致覆盖
            unique_filename = f"{uuid.uuid4().hex}_{original_filename}"
            # 3. 构建保存的绝对路径
            save_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)

            # 4. 保存文件到硬盘
            file.save(save_path)

            # 5. 将相对路径写入数据库
            relative_path = f"static/uploads/{unique_filename}"
            new_assignment = Assignment(
                student_id=current_user.id,
                course_id=course.id,
                file_path=relative_path
            )
            db.session.add(new_assignment)
            db.session.commit()

            flash('📸 摄影作品上传成功！请等待导师批改。', 'success')
            return redirect(url_for('student.workspace', course_id=course.id))
        else:
            flash('仅支持上传 JPG, PNG, GIF, RAW 等图片格式！', 'danger')

    # GET 请求：获取学员在这门课提交过的所有历史作品及成绩
    my_assignments = Assignment.query.filter_by(
        student_id=current_user.id, course_id=course.id
    ).order_by(Assignment.submit_time.desc()).all()

    return render_template('student/workspace.html', course=course, assignments=my_assignments)