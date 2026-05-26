"""
decorators.py — 权限检查装饰器 & 审计日志工具

用法示例：
    @require_permission("file:delete")
    def delete_file(resource_id):
        ...

    @require_role("Admin", "SuperAdmin")
    def admin_panel():
        ...
"""

from functools import wraps
from flask import request, jsonify, abort
from flask_login import current_user

from app.models.models import db, AuditLog


# ──────────────────────────────────────────────
# 审计日志写入
# ──────────────────────────────────────────────
def write_audit_log(action: str, status: str = "success",
                    resource_id: int = None, detail: str = None):
    """写入一条审计日志，自动获取当前用户和 IP"""
    log = AuditLog(
        user_id     = current_user.id if current_user.is_authenticated else None,
        action      = action,
        resource_id = resource_id,
        detail      = detail,
        ip_address  = request.remote_addr,
        status      = status,
    )
    db.session.add(log)
    db.session.commit()


# ──────────────────────────────────────────────
# 权限装饰器
# ──────────────────────────────────────────────
def require_permission(*perm_names: str):
    """
    要求当前登录用户拥有 perm_names 中的【任一】权限。
    未登录 → 401；无权限 → 403，并写入 denied 审计日志。
    """
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if not current_user.is_authenticated:
                return jsonify({"error": "未登录", "code": 401}), 401

            if not any(current_user.has_permission(p) for p in perm_names):
                # 记录拒绝日志
                write_audit_log(
                    action  = f.__name__,
                    status  = "denied",
                    detail  = f"需要权限: {', '.join(perm_names)}",
                )
                return jsonify({"error": "权限不足", "code": 403}), 403

            return f(*args, **kwargs)
        return wrapper
    return decorator


def require_all_permissions(*perm_names: str):
    """
    要求当前登录用户拥有 perm_names 中的【所有】权限。
    """
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if not current_user.is_authenticated:
                return jsonify({"error": "未登录", "code": 401}), 401

            missing = [p for p in perm_names if not current_user.has_permission(p)]
            if missing:
                write_audit_log(
                    action = f.__name__,
                    status = "denied",
                    detail = f"缺少权限: {', '.join(missing)}",
                )
                return jsonify({"error": "权限不足", "code": 403}), 403

            return f(*args, **kwargs)
        return wrapper
    return decorator


def require_role(*role_names: str):
    """
    要求当前登录用户拥有 role_names 中的【任一】角色。
    """
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if not current_user.is_authenticated:
                return jsonify({"error": "未登录", "code": 401}), 401

            if not any(current_user.has_role(r) for r in role_names):
                write_audit_log(
                    action = f.__name__,
                    status = "denied",
                    detail = f"需要角色: {', '.join(role_names)}",
                )
                return jsonify({"error": "角色权限不足", "code": 403}), 403

            return f(*args, **kwargs)
        return wrapper
    return decorator
