import os
import click
from flask import Flask, render_template, redirect, url_for
from config import Config
from extensions import db, login_manager
from models import User, Course, Enrollment, Assignment  # 导入模型，确保建表时能识别到

def create_app(config_class=Config):
    """
    应用工厂函数：组装整个 Flask 应用
    """
    app = Flask(__name__)
    # 1. 导入配置
    app.config.from_object(config_class)

    # 2. 绑定扩展引擎 (将独立实例与当前的 app 绑定)
    db.init_app(app)
    login_manager.init_app(app)

    # 3. 配置 Flask-Login 的用户加载逻辑
    @login_manager.user_loader
    def load_user(user_id):
        # 每次用户请求时，通过 session 中的 user_id 去数据库查出当前用户对象
        return User.query.get(int(user_id))

    # 4. 注册蓝图 Blueprints (路由控制器)
    # 注意：这里的视图文件我们马上就会写，先在这里把坑位占好
    from views.auth import auth_bp
    from views.admin import admin_bp
    from views.teacher import teacher_bp
    from views.student import student_bp

    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(teacher_bp, url_prefix='/teacher')
    app.register_blueprint(student_bp, url_prefix='/student')

    # 5. 注入全局模板变量 (方便在 HTML 里直接使用)
    @app.context_processor
    def inject_globals():
        return {'sys_name': '光影视觉·摄影学员管理系统'}

    # 6. 注册自定义 CLI 命令：初始化数据库
    # 用法：在终端运行 flask init-db
    @app.cli.command("init-db")
    def init_db():
        """初始化数据库并创建默认超级管理员"""
        db.create_all()
        click.echo("✅ 数据库表已成功创建！")

        # 检查是否已经存在 admin 账号
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(username='admin', real_name='系统超级管理员', role='admin')
            admin.set_password('123456')  # 默认密码
            db.session.add(admin)
            db.session.commit()
            click.echo("✅ 初始管理员账号已生成！账号: admin / 密码: 123456")
        else:
            click.echo("⚠️ 管理员账号已存在，无需重复创建。")

    # 7. 全局错误处理页面
    @app.errorhandler(403)
    def forbidden(e):
        return render_template('errors/403.html'), 403

    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('errors/404.html'), 404

    # 8. 根路由拦截
    @app.route('/')
    def index():
        # 用户访问首页时，直接重定向到登录页面
        return redirect(url_for('auth.login'))

    return app

# 启动脚本
if __name__ == '__main__':
    app = create_app()
    # 确保上传文件夹存在
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    # 启动应用
    app.run(debug=True, port=5000)