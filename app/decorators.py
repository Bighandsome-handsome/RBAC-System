# app/decorators.py
'''
from functools import wraps
from flask import abort
from flask_login import current_user

def role_required(role_name):
    """
    A decorator to protect routes that require a specific role.
    If the current user does not have the required role, it aborts with a 403 error.
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated or not current_user.has_role(role_name):
                abort(403)  # Forbidden
            return f(*args, **kwargs)
        return decorated_function
    return decorator
'''
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


# from app.models import db, AuditLog

# ──────────────────────────────────────────────
# 审计日志写入
# ──────────────────────────────────────────────
def write_audit_log(action: str, status: str = "success",
                    resource_id: int = None, detail: str = None):
    """写入一条审计日志，自动获取当前用户和 IP"""
    from app.models import AuditLog
    from app import db
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
    【核心扩展】：若目标资源已被标记为共享（is_shared=True），自动豁免放行。
    """
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            # 1. 前置安全断言：未登录流量直接清退
            if not current_user.is_authenticated:
                return jsonify({"error": "未登录", "code": 401}), 401

            # 延迟导入，防止与 Flask 蓝图加载引发循环导入死锁
            from app.models import Resource

            # 🌐 共享区动态安全豁免逻辑
            
            # 情况 1：针对已有文件的 预览/下载/读取/更名 操作 (路由参数通常为 resource_id)
            resource_id = kwargs.get('resource_id') or request.view_args.get('resource_id')
            if resource_id and any(p in ['file:read', 'file:download', 'file:update'] for p in perm_names):
                target_resource = Resource.query.get(resource_id)
                # 🚀 如果该资源在系统内已被发布为“共享”，且当前处于读/改动作，直接豁免全量 RBAC 校验放行
                if target_resource and target_resource.is_shared:
                    return f(*args, **kwargs)

            # 情况 2：针对往共享文件夹内 上传文件/新建子目录 的写操作 
            # (通常从前端 JSON 报文或 Multipart 附件表单中带上 parent_id)
            parent_id = None
            if request.is_json and request.json:
                parent_id = request.json.get('parent_id')
            elif request.form:
                parent_id = request.form.get('parent_id')
                
            if parent_id and 'file:write' in perm_names:
                parent_folder = Resource.query.get(parent_id)
                # 🚀 只要父级目录被标记为共享，允许系统内的任意激活角色执行向内写入，打破特权黑盒
                if parent_folder and parent_folder.is_shared and parent_folder.is_directory:
                    return f(*args, **kwargs)

            # 3. 原有严格 RBAC 细粒度特权矩阵校验（无共享豁免时触发）
            if not any(current_user.has_permission(p) for p in perm_names):
                # 记录越权拒绝日志到黑匣子
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
