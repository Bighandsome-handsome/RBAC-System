"""
seed.py — 初始化数据库：6 个角色 + 14 条权限 + 测试用户

运行方式：
    python seed.py

六个角色说明：
  SuperAdmin  — 系统超管，拥有全部权限
  Admin       — 管理员，可管理用户和文件
  Manager     — 部门经理，可读写更新文件，不可删除
  Operator    — 操作员，可读写文件
  Auditor     — 审计员，只读文件 + 可查看日志
  Guest       — 访客，仅可读取公开文件
"""

from app import create_app
from app.models.models import db, User, Role, Permission

PERMISSIONS = [
    # 文件操作
    ("file:read",      "file",   "读取文件内容"),
    ("file:write",     "file",   "上传/新建文件"),
    ("file:update",    "file",   "修改/重命名文件"),
    ("file:delete",    "file",   "删除文件"),
    ("file:download",  "file",   "下载文件"),
    ("folder:create",  "file",   "新建文件夹"),
    ("folder:delete",  "file",   "删除文件夹"),
    # 用户管理
    ("user:view",      "admin",  "查看用户列表"),
    ("user:create",    "admin",  "创建新用户"),
    ("user:edit",      "admin",  "编辑用户信息"),
    ("user:delete",    "admin",  "删除用户"),
    ("role:manage",    "admin",  "管理角色与权限"),
    # 审计
    ("audit:view",     "system", "查看审计日志"),
    ("audit:export",   "system", "导出审计日志"),
]

# 角色 → 权限名列表
ROLE_PERMISSIONS = {
    "SuperAdmin": [p[0] for p in PERMISSIONS],  # 全部
    "Admin": [
        "file:read", "file:write", "file:update", "file:delete",
        "file:download", "folder:create", "folder:delete",
        "user:view", "user:create", "user:edit",
        "audit:view",
    ],
    "Manager": [
        "file:read", "file:write", "file:update", "file:download",
        "folder:create", "user:view", "audit:view",
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

TEST_USERS = [
    {"username": "superadmin", "email": "superadmin@example.com", "password": "Super@123", "role": "SuperAdmin"},
    {"username": "admin",      "email": "admin@example.com",      "password": "Admin@123", "role": "Admin"},
    {"username": "manager",    "email": "manager@example.com",    "password": "Mgr@1234",  "role": "Manager"},
    {"username": "operator",   "email": "operator@example.com",   "password": "Ops@1234",  "role": "Operator"},
    {"username": "auditor",    "email": "auditor@example.com",    "password": "Aud@1234",  "role": "Auditor"},
    {"username": "guest",      "email": "guest@example.com",      "password": "Guest@123", "role": "Guest"},
]


def seed():
    app = create_app()
    with app.app_context():
        print("🔧 创建权限...")
        perm_map = {}
        for name, category, desc in PERMISSIONS:
            p = Permission.query.filter_by(name=name).first()
            if not p:
                p = Permission(name=name, category=category, description=desc)
                db.session.add(p)
            perm_map[name] = p
        db.session.flush()

        print("🎭 创建角色并分配权限...")
        role_map = {}
        for role_name, perm_names in ROLE_PERMISSIONS.items():
            r = Role.query.filter_by(name=role_name).first()
            if not r:
                r = Role(name=role_name, description=ROLE_DESCRIPTIONS[role_name])
                db.session.add(r)
            # 清空旧权限再重新分配
            r.permissions = []
            for pname in perm_names:
                r.permissions.append(perm_map[pname])
            role_map[role_name] = r
        db.session.flush()

        print("👤 创建测试用户...")
        for u_data in TEST_USERS:
            u = User.query.filter_by(username=u_data["username"]).first()
            if not u:
                u = User(username=u_data["username"], email=u_data["email"])
                u.set_password(u_data["password"])
                u.roles.append(role_map[u_data["role"]])
                db.session.add(u)
                print(f"   ✅ {u_data['username']} ({u_data['role']})")
            else:
                print(f"   ⚠️  {u_data['username']} 已存在，跳过")

        db.session.commit()
        print("\n✨ 初始化完成！")
        print("\n默认账号（请部署前修改密码）：")
        for u in TEST_USERS:
            print(f"  {u['username']:12s} / {u['password']:12s}  [{u['role']}]")


if __name__ == "__main__":
    seed()
