# app/__init__.py
'''
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from config import Config
from flask_admin import Admin
from config import Config
from app.files import files_bp
from app.admin import admin_bp
import pymysql
from re import search

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
bcrypt = Bcrypt()
login_manager = LoginManager()
login_manager.login_view = 'main.login' # The route to redirect to for login
login_manager.login_message_category = 'info' # Flash message category

# from app.admin import admin

def create_app(config_class=Config):
    """
    Application factory function.
    Creates and configures the Flask application.
    """
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions with the app
    db.init_app(app)
    migrate.init_app(app, db)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    

    # admin.init_app(app)
    
    # Import and register blueprints
    from app.routes import main as main_blueprint
    app.register_blueprint(main_blueprint)
    app.register_blueprint(files_bp)
    app.register_blueprint(admin_bp)

    return app
def create_database_if_not_exists(app):
    """自动检查并创建 MySQL 数据库"""
    uri = app.config.get('SQLALCHEMY_DATABASE_URI', '')
    match = search(r"mysql\+pymysql://([^:]+):([^@]+)@([^:/]+):?(\d*)/([^?]+)", uri)
    if match:
        user, password, host, port, db_name = match.groups()
        port = int(port) if port else 3306
        
        # 连接到 MySQL 实例本身（先不指定数据库名）
        conn = pymysql.connect(host=host, user=user, password=password, port=port)
        cursor = conn.cursor()
        # 自动创建符合作业要求的 utf8mb4 编码数据库
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name} CHARACTER SET utf8mb4;")
        cursor.close()
        conn.close()
        print(f"数据库 [{db_name}] 检查完毕，确保存在！")
'''
# app/__init__.py
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from flask_admin import Admin
from config import Config
from app.files import files_bp
from app.admin import admin_bp
import pymysql
from re import search

# 🌟 核心修正 1：移除本地声明的 db = SQLAlchemy()
# 我们不再在 __init__.py 顶层创建全新的 db 实例，而是直接从已有的 models.py 引入那个被模型们继承的、真正的 db！
from app.models import db, bcrypt  # 👈 这样模型和应用共享同一个 db 实例

migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = 'main.login' 
login_manager.login_message_category = 'info' 

def create_app(config_class=Config):
    """
    Application factory function.
    Creates and configures the Flask application.
    """
    app = Flask(__name__)
    app.config.from_object(config_class)

    # 自动检查并创建 MySQL 数据库
    create_database_if_not_exists(app)

    # 🌟 核心修正 2：用唯一的 db 实例初始化应用
    db.init_app(app)
    migrate.init_app(app, db)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    
    # 导入并注册蓝图
    from app.routes import main as main_blueprint
    app.register_blueprint(main_blueprint)
    # app.register_blueprint(files_bp)    // changed
    from app.files import files_bp
    app.register_blueprint(files_bp, url_prefix='/api/files')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')

    return app

def create_database_if_not_exists(app):
    """自动检查并创建 MySQL 数据库"""
    uri = app.config.get('SQLALCHEMY_DATABASE_URI', '')
    match = search(r"mysql\+pymysql://([^:]+):([^@]+)@([^:/]+):?(\d*)/([^?]+)", uri)
    if match:
        try:
            user, password, host, port, db_name = match.groups()
            port = int(port) if port else 3306
            conn = pymysql.connect(host=host, user=user, password=password, port=port)
            cursor = conn.cursor()
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name} CHARACTER SET utf8mb4;")
            cursor.close()
            conn.close()
            print(f"📡 数据库 [{db_name}] 检查完毕，确保存在！")
        except Exception as e:
            print(f"⚠️ 自动检查数据库失败 (可能是 SQLite 环境或配置问题): {str(e)}")