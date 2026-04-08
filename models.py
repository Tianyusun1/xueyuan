from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from extensions import db


class User(db.Model, UserMixin):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    real_name = db.Column(db.String(64), nullable=False)
    # 角色定义：'admin' 管理员, 'teacher' 教师, 'student' 学生
    role = db.Column(db.String(20), nullable=False, default='student')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # 关系定义
    # 作为老师：名下的课程
    teaching_courses = db.relationship('Course', backref='teacher', lazy='dynamic')
    # 作为学生：选课记录
    enrollments = db.relationship('Enrollment', backref='student', lazy='dynamic')
    # 作为学生：提交的作品
    assignments = db.relationship('Assignment', backref='student', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def is_admin(self):
        return self.role == 'admin'

    @property
    def is_teacher(self):
        return self.role == 'teacher'

    @property
    def is_student(self):
        return self.role == 'student'


class Course(db.Model):
    __tablename__ = 'courses'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False, default=0.0)  # 用于统计财务流水
    max_students = db.Column(db.Integer, nullable=False, default=30)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # 外键：该课程的授课教师
    teacher_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    # 关系定义
    enrollments = db.relationship('Enrollment', backref='course', lazy='dynamic')
    assignments = db.relationship('Assignment', backref='course', lazy='dynamic')

    @property
    def current_students_count(self):
        """动态计算当前报名人数，用于看板的课程热度排行"""
        return self.enrollments.count()


class Enrollment(db.Model):
    """选课与财务流水表"""
    __tablename__ = 'enrollments'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    amount_paid = db.Column(db.Float, nullable=False)  # 实际支付金额
    enroll_time = db.Column(db.DateTime, default=datetime.utcnow)  # 报名时间，用于做营收折线图


class Assignment(db.Model):
    """学员摄影作品流转表"""
    __tablename__ = 'assignments'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)

    # 作品文件在服务器的相对路径
    file_path = db.Column(db.String(256), nullable=False)
    submit_time = db.Column(db.DateTime, default=datetime.utcnow)  # 提交时间，用于计算学员活跃度

    # 教师评审字段
    score = db.Column(db.Integer)  # 得分 (0-100)
    feedback = db.Column(db.Text)  # 教师评语
    review_time = db.Column(db.DateTime)  # 批改时间

    status = db.Column(db.String(20), default='pending')  # 状态：pending(待批改), graded(已批改)