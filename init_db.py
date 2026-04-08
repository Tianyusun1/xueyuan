import sqlalchemy
from sqlalchemy import create_engine
from app import create_app
from extensions import db
from models import User, Course, Enrollment, Assignment

# 1. 使用工厂模式创建 Flask 应用实例
app = create_app()


def create_database_if_not_exists():
    """
    自动解析配置并创建 MySQL 数据库（如果不存在的话）
    """
    uri = app.config['SQLALCHEMY_DATABASE_URI']

    # 解析数据库连接字符串
    # 格式通常为: mysql+pymysql://root:123456@127.0.0.1:3306/photography_db?charset=utf8mb4
    if 'mysql' in uri:
        try:
            # 将 URI 拆分成 "服务器地址" 和 "数据库名"
            base_uri, db_part = uri.rsplit('/', 1)
            db_name = db_part.split('?')[0]

            print(f"⚙️ 正在连接 MySQL 服务器并检查数据库 '{db_name}'...")

            # 连接到 MySQL 服务器（不指定具体数据库），并设置自动提交
            engine = create_engine(base_uri, isolation_level="AUTOCOMMIT")
            with engine.connect() as conn:
                # 执行原生 SQL 创建数据库
                conn.execute(sqlalchemy.text(
                    f"CREATE DATABASE IF NOT EXISTS {db_name} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
                ))
            print(f"✅ 数据库 '{db_name}' 准备就绪！")
        except Exception as e:
            print(f"⚠️ 自动创建数据库失败，请检查账号密码。错误信息: {e}")


# --- 核心执行流程 ---

# 第一步：强行建库！
create_database_if_not_exists()

# 第二步：推送应用上下文，开始建表！
with app.app_context():
    print("⏳ 正在连接数据库并创建数据表...")
    db.create_all()
    print("✅ 数据库表结构创建成功！")

    # 第三步：检查并初始化超级管理员账号
    print("⏳ 正在检查管理员账号状态...")
    admin = User.query.filter_by(username='admin').first()

    if not admin:
        admin = User(
            username='admin',
            real_name='系统超级管理员',
            role='admin'
        )
        admin.set_password('123456')
        db.session.add(admin)
        db.session.commit()
        print("🎉 初始超级管理员账号创建成功！")
        print("👉 登录账号: admin")
        print("👉 登录密码: 123456")
    else:
        print("⚠️ 超级管理员账号已存在，无需重复创建。")

    print("✨ 数据库初始化流程全部完成，现在可以启动 python app.py 了！")