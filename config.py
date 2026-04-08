import os

# 获取当前项目的绝对路径
BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    # 系统的安全密钥，用于防跨站请求伪造(CSRF)和生成 Session 签名
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'photography-system-super-secret-key-2026'

    # MySQL 数据库配置 (请根据你本地的 MySQL 账号密码进行修改)
    # 格式: mysql+pymysql://用户名:密码@主机地址:端口/数据库名
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
                              'mysql+pymysql://root:123456@127.0.0.1:3306/photography_db?charset=utf8mb4'

    # 关闭 SQLAlchemy 的事件追踪，节约系统内存
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # 摄影作品上传的存储路径
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')

    # 允许上传的图片文件扩展名
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'raw'}

    # 最大上传文件大小：限制为 50MB (考虑到单反原片较大)
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024