"""
models.py — 在原有 User/Role 基础上扩展：
  - Permission       权限表（file:read / file:write / file:update / file:delete 等）
  - RolePermission   角色-权限关联表（多对多）
  - Resource         文件/资源表
  - AuditLog         操作审计日志表
"""

from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from flask_bcrypt import Bcrypt

db = SQLAlchemy()
bcrypt = Bcrypt()


# ──────────────────────────────────────────────
# 角色-权限  多对多关联表
# ──────────────────────────────────────────────
role_permissions = db.Table(
    "role_permissions",
    db.Column("role_id",       db.Integer, db.ForeignKey("roles.id"),       primary_key=True),
    db.Column("permission_id", db.Integer, db.ForeignKey("permissions.id"), primary_key=True),
)

# 用户-角色  多对多关联表（原项目可能已有，保留兼容）
user_roles = db.Table(
    "user_roles",
    db.Column("user_id", db.Integer, db.ForeignKey("users.id"), primary_key=True),
    db.Column("role_id",  db.Integer, db.ForeignKey("roles.id"),  primary_key=True),
)


# ──────────────────────────────────────────────
# Permission  权限表
# ──────────────────────────────────────────────
class Permission(db.Model):
    __tablename__ = "permissions"

    id          = db.Column(db.Integer, primary_key=True)
    name        = db.Column(db.String(80),  unique=True, nullable=False)   # e.g. "file:read"
    category    = db.Column(db.String(40),  nullable=False, default="file") # file / admin / system
    description = db.Column(db.String(255), nullable=True)

    def __repr__(self):
        return f"<Permission {self.name}>"


# ──────────────────────────────────────────────
# Role  角色表（扩展为 6 个角色）
# ──────────────────────────────────────────────
class Role(db.Model):
    __tablename__ = "roles"

    id          = db.Column(db.Integer, primary_key=True)
    name        = db.Column(db.String(80),  unique=True, nullable=False)
    description = db.Column(db.String(255), nullable=True)

    # 关联权限
    permissions = db.relationship(
        "Permission", secondary=role_permissions,
        backref=db.backref("roles", lazy="dynamic"), lazy="dynamic"
    )

    def has_permission(self, perm_name: str) -> bool:
        return self.permissions.filter_by(name=perm_name).first() is not None

    def __repr__(self):
        return f"<Role {self.name}>"


# ──────────────────────────────────────────────
# User  用户表
# ──────────────────────────────────────────────
class User(db.Model, UserMixin):
    __tablename__ = "users"

    id           = db.Column(db.Integer, primary_key=True)
    username     = db.Column(db.String(80),  unique=True, nullable=False)
    email        = db.Column(db.String(120), unique=True, nullable=False)
    password     = db.Column(db.String(255), nullable=False)
    is_active    = db.Column(db.Boolean, default=True)
    created_at   = db.Column(db.DateTime, default=datetime.utcnow)

    roles = db.relationship(
        "Role", secondary=user_roles,
        backref=db.backref("users", lazy="dynamic"), lazy="dynamic"
    )

    # ---- 权限检查辅助方法 ----
    def has_permission(self, perm_name: str) -> bool:
        """检查用户所有角色中是否含有该权限"""
        for role in self.roles:
            if role.has_permission(perm_name):
                return True
        return False

    def has_role(self, role_name: str) -> bool:
        return self.roles.filter_by(name=role_name).first() is not None

    def get_all_permissions(self):
        """返回用户拥有的所有权限名称集合"""
        perms = set()
        for role in self.roles:
            for perm in role.permissions:
                perms.add(perm.name)
        return perms

    def set_password(self, raw_password: str):
        self.password = bcrypt.generate_password_hash(raw_password).decode("utf-8")

    def check_password(self, raw_password: str) -> bool:
        return bcrypt.check_password_hash(self.password, raw_password)

    def __repr__(self):
        return f"<User {self.username}>"


# ──────────────────────────────────────────────
# Resource  文件/资源表
# ──────────────────────────────────────────────
class Resource(db.Model):
    __tablename__ = "resources"

    id           = db.Column(db.Integer, primary_key=True)
    name         = db.Column(db.String(255), nullable=False)           # 文件名
    path         = db.Column(db.String(500), nullable=False)           # 存储路径
    size         = db.Column(db.BigInteger, default=0)                 # 字节
    mime_type    = db.Column(db.String(100), nullable=True)
    is_directory = db.Column(db.Boolean, default=False)
    parent_id    = db.Column(db.Integer, db.ForeignKey("resources.id"), nullable=True)
    owner_id     = db.Column(db.Integer, db.ForeignKey("users.id"),     nullable=False)
    created_at   = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at   = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    is_shared = db.Column(db.Boolean, default=False, nullable=False)

    owner    = db.relationship("User",     backref="resources")
    children = db.relationship("Resource", backref=db.backref("parent", remote_side=[id]))

    def to_dict(self):
        return {
            "id":           self.id,
            "name":         self.name,
            "path":         self.path,
            "size":         self.size,
            "mime_type":    self.mime_type,
            "is_directory": self.is_directory,
            "parent_id":    self.parent_id,
            "owner":        self.owner.username if self.owner else None,
            "created_at":   self.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            "updated_at":   self.updated_at.strftime("%Y-%m-%d %H:%M:%S"),
        }

    def __repr__(self):
        return f"<Resource {self.name}>"


# ──────────────────────────────────────────────
# AuditLog  审计日志表
# ──────────────────────────────────────────────
class AuditLog(db.Model):
    __tablename__ = "audit_logs"

    id          = db.Column(db.Integer, primary_key=True)
    user_id     = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)   # 可为空（匿名）
    action      = db.Column(db.String(50),  nullable=False)   # read/write/update/delete/login/logout
    resource_id = db.Column(db.Integer, db.ForeignKey("resources.id"), nullable=True)
    detail      = db.Column(db.String(500), nullable=True)    # 额外说明
    ip_address  = db.Column(db.String(50),  nullable=True)
    status      = db.Column(db.String(20),  nullable=False, default="success")  # success / denied / error
    timestamp   = db.Column(db.DateTime,    default=datetime.utcnow)

    user     = db.relationship("User",     backref="audit_logs")
    resource = db.relationship("Resource", backref="audit_logs")

    def to_dict(self):
        return {
            "id":          self.id,
            "user":        self.user.username if self.user else "anonymous",
            "action":      self.action,
            "resource":    self.resource.name if self.resource else None,
            "detail":      self.detail,
            "ip_address":  self.ip_address,
            "status":      self.status,
            "timestamp":   self.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
        }

    def __repr__(self):
        return f"<AuditLog {self.action} by user_id={self.user_id}>"
