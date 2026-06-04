# seed.py — 回归标准干净的独立脚本
import sys
from app import create_app
from app.models import db, User, Role, Permission

# 1. 14条核心权限定义
PERMISSIONS = [
    ("file:read",      "file",   "读取文件内容"),
    ("file:write",     "file",   "上传/新建文件"),
    ("file:update",    "file",   "修改/重命名文件"),
    ("file:delete",    "file",   "删除文件"),
    ("file:download",  "file",   "下载文件"),
    ("folder:create",  "file",   "新建文件夹"),
    ("folder:delete",  "file",   "删除文件夹"),
    ("user:view",      "admin",  "查看用户列表"),
    ("user:create",    "admin",  "创建新用户"),
    ("user:edit",      "admin",  "编辑用户信息"),
    ("user:delete",    "admin",  "删除用户"),
    ("role:manage",    "admin",  "管理角色与权限"),
    ("audit:view",     "system", "查看审计日志"),
    ("audit:export",   "system", "导出审计日志"),
]

# 2. 6个角色权限映射
ROLE_PERMISSIONS = {
    "SuperAdmin": [p[0] for p in PERMISSIONS],
    "Admin": [
        "file:read", "file:write", "file:update",
        "folder:create", "folder:delete",
        "user:view", "user:create", "user:edit", "audit:view",
    ],
    "Manager": [
        "file:read","user:view", "user:create", "user:edit", "audit:view",
    ],
    "Operator": [
        "file:read", "file:write", "file:download", "folder:create",
    ],
    "Auditor": [
        "file:read", "file:download", "audit:view", "audit:export",
    ],
    "Guest": [
        "file:read",
    ],
}

ROLE_DESCRIPTIONS = {
    "SuperAdmin": "系统超级管理员，拥有全部权限",
    "Admin":      "系统管理员，管理用户和文件",
    "Manager":    "部门经理，可读写更新文件，不可删除",
    "Operator":   "操作员，可上传和读取文件",
    "Auditor":    "审计员，只读文件并可查看操作日志",
    "Guest":      "访客，仅可读取公开文件",
}

# 3. 6组黄金测试账号
TEST_USERS = [
    {"username": "superadmin", "email": "superadmin@example.com", "password": "Super@123", "role": "SuperAdmin"},
    {"username": "admin",      "email": "admin@example.com",      "password": "Admin@123", "role": "Admin"},
    {"username": "manager",    "email": "manager@example.com",    "password": "Mgr@1234",  "role": "Manager"},
    {"username": "operator",   "email": "operator@example.com",   "password": "Ops@1234",  "role": "Operator"},
    {"username": "auditor",    "email": "auditor@example.com",    "password": "Aud@1234",  "role": "Auditor"},
    {"username": "guest",      "email": "guest@example.com",      "password": "Guest@123", "role": "Guest"},
]


def run_seed(app):
    with app.app_context():
        print("🏗️ 正在检测并全量构建本地数据库表结构...")
        # 此时 db.create_all() 绝对能在同一个物理数据库上百分之百成功建表！
        db.create_all()
        print("✅ 数据库表结构准备就绪！")
        
        print("🔧 正在初始化 14 条核心权限...")
        perm_map = {}
        for name, category, desc in PERMISSIONS:
            p = Permission.query.filter_by(name=name).first()
            if not p:
                p = Permission(name=name, category=category, description=desc)
                db.session.add(p)
            perm_map[name] = p
        db.session.flush()

        print("🎭 正在创建 6 大系统角色并动态绑定多对多权限...")
        role_map = {}
        for role_name, perm_names in ROLE_PERMISSIONS.items():
            r = Role.query.filter_by(name=role_name).first()
            if not r:
                r = Role(name=role_name, description=ROLE_DESCRIPTIONS[role_name])
                db.session.add(r)
            
            # 清空并重新通过多对多关系绑定
            r.permissions = []
            for pname in perm_names:
                r.permissions.append(perm_map[pname])
            role_map[role_name] = r
        db.session.flush()

        print("👤 正在填充 6 组安全隔离的测试用户...")
        for u_data in TEST_USERS:
            u = User.query.filter_by(username=u_data["username"]).first()
            if not u:
                u = User(username=u_data["username"], email=u_data["email"])
                u.set_password(u_data["password"]) # 使用 models.py 内部集成的 bcrypt 加密
                
                # 完美对接 models.py 的 roles 关联属性
                u.roles.append(role_map[u_data["role"]])
                db.session.add(u)
                print(f"  -> 账户 [{u_data['username']}] 刷入成功，角色: {u_data['role']}")
            else:
                print(f"  -> 账户 [{u_data['username']}] 已存在，跳过。")

        # 安全提交事务
        db.session.commit()
        print("\n 恭喜！全量 RBAC 初始数据完美注入成功！")
        print("--------------------------------------------------")
        for u in TEST_USERS:
            print(f" 账号: {u['username']:12s} | 密码: {u['password']:12s} | 角色: [{u['role']}]")


if __name__ == "__main__":
    flask_app = create_app()
    run_seed(flask_app)