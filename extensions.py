from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

# 实例化数据库对象 (此时暂不绑定具体的 app)
db = SQLAlchemy()

# 实例化登录管理器，用于处理管理员、教师、学生的会话状态
login_manager = LoginManager()

# 设置登录视图的端点，如果用户未登录尝试访问保护页面，会被强制重定向到这里
login_manager.login_view = 'auth.login'
# 自定义未登录时的闪现消息提示内容和类别
login_manager.login_message = '请先登录以访问该页面。'
login_manager.login_message_category = 'warning'