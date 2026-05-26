# app/admin.py
'''
from flask_admin import Admin, AdminIndexView
from flask_admin.contrib.sqla import ModelView
from flask_login import current_user
from flask import redirect, url_for
from app import db
from app.models import User, Role
from wtforms import PasswordField 


class MyAdminIndexView(AdminIndexView):
    """
    Custom AdminIndexView to enforce role-based access.
    """
    def is_accessible(self):
        # Only allow users with the 'Admin' role to access the admin dashboard
        return current_user.is_authenticated and current_user.has_role('Admin')

    def inaccessible_callback(self, name, **kwargs):
        # Redirect non-admin users to the main dashboard
        return redirect(url_for('main.dashboard'))

class UserAdminView(ModelView):
    """
    Custom ModelView for the User model.
    """
    # Don't display the password hash in the list view
    column_exclude_list = ('password_hash',)

    #use a custom form that includes a passwordfield
    form_extra_fields = {
        'password': PasswordField('New Password')
    }
    # Don't allow password hash to be edited directly
    form_excluded_columns = ('password_hash',)

    def on_model_change(self, form, model, is_created):
        """
        This method is called when a model is created or updated.
        We use it to hash the password before saving it to the database.
        """
        if form.password.data:
            model.set_password(form.password.data)
    
    def is_accessible(self):
        return current_user.is_authenticated and current_user.has_role('Admin')
    
    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('main.dashboard'))

# Initialize the Admin interface with the custom index view
admin = Admin(name='Admin Dashboard', template_mode='bootstrap3', index_view=MyAdminIndexView())

# Add views for your models to the admin interface
admin.add_view(UserAdminView(User, db.session))
admin.add_view(ModelView(Role, db.session))

'''

"""
routes/admin.py — 审计日志查看 & 角色/权限管理接口

GET  /api/admin/audit          查看审计日志（需 audit:view）
GET  /api/admin/audit/export   导出日志 CSV（需 audit:export）
GET  /api/admin/roles          列出角色（需 role:manage）
POST /api/admin/roles          新建角色（需 role:manage）
PUT  /api/admin/roles/<id>     更新角色权限（需 role:manage）
GET  /api/admin/users          列出用户（需 user:view）
PUT  /api/admin/users/<id>     更改用户角色（需 user:edit）
"""

import csv
import io
from flask import Blueprint, request, jsonify, Response
from flask_login import login_required

from app.models import db, AuditLog, Role, Permission, User
from app.decorators import require_permission, write_audit_log

admin_bp = Blueprint("admin", __name__, url_prefix="/api/admin")


# ── 审计日志列表 ──────────────────────────────
@admin_bp.route("/audit", methods=["GET"])
@login_required
@require_permission("audit:view")
def get_audit_logs():
    page     = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 50, type=int)
    action   = request.args.get("action")
    status   = request.args.get("status")
    user_id  = request.args.get("user_id", type=int)

    query = AuditLog.query.order_by(AuditLog.timestamp.desc())
    if action:
        query = query.filter_by(action=action)
    if status:
        query = query.filter_by(status=status)
    if user_id:
        query = query.filter_by(user_id=user_id)

    paginated = query.paginate(page=page, per_page=per_page, error_out=False)
    return jsonify({
        "code":  200,
        "data":  [log.to_dict() for log in paginated.items],
        "total": paginated.total,
        "pages": paginated.pages,
        "page":  page,
    })


# ── 导出审计日志 CSV ──────────────────────────
@admin_bp.route("/audit/export", methods=["GET"])
@login_required
@require_permission("audit:export")
def export_audit_logs():
    logs = AuditLog.query.order_by(AuditLog.timestamp.desc()).limit(5000).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "用户", "操作", "资源", "详情", "IP", "状态", "时间"])
    for log in logs:
        writer.writerow([
            log.id,
            log.user.username if log.user else "anonymous",
            log.action,
            log.resource.name if log.resource else "",
            log.detail or "",
            log.ip_address or "",
            log.status,
            log.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
        ])

    write_audit_log(action="audit:export", detail="导出审计日志 CSV")
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=audit_logs.csv"},
    )


# ── 角色列表 ──────────────────────────────────
@admin_bp.route("/roles", methods=["GET"])
@login_required
@require_permission("role:manage")
def get_roles():
    roles = Role.query.all()
    return jsonify({
        "code": 200,
        "data": [{
            "id":          r.id,
            "name":        r.name,
            "description": r.description,
            "permissions": [p.name for p in r.permissions],
            "user_count":  r.users.count(),
        } for r in roles],
    })


# ── 新建角色 ──────────────────────────────────
@admin_bp.route("/roles", methods=["POST"])
@login_required
@require_permission("role:manage")
def create_role():
    data = request.get_json() or {}
    name = data.get("name", "").strip()
    if not name:
        return jsonify({"error": "角色名不能为空", "code": 400}), 400
    if Role.query.filter_by(name=name).first():
        return jsonify({"error": "角色名已存在", "code": 400}), 400

    role = Role(name=name, description=data.get("description", ""))
    perm_names = data.get("permissions", [])
    for pname in perm_names:
        p = Permission.query.filter_by(name=pname).first()
        if p:
            role.permissions.append(p)
    db.session.add(role)
    db.session.commit()

    write_audit_log(action="role:manage", detail=f"新建角色 {name}")
    return jsonify({"code": 200, "data": {"id": role.id, "name": role.name}})


# ── 更新角色权限 ──────────────────────────────
@admin_bp.route("/roles/<int:role_id>", methods=["PUT"])
@login_required
@require_permission("role:manage")
def update_role(role_id):
    role = Role.query.get_or_404(role_id)
    data = request.get_json() or {}

    if "description" in data:
        role.description = data["description"]
    if "permissions" in data:
        role.permissions = []
        for pname in data["permissions"]:
            p = Permission.query.filter_by(name=pname).first()
            if p:
                role.permissions.append(p)
    db.session.commit()

    write_audit_log(action="role:manage", detail=f"更新角色 {role.name} 权限")
    return jsonify({"code": 200, "message": "更新成功"})


# ── 用户列表 ──────────────────────────────────
@admin_bp.route("/users", methods=["GET"])
@login_required
@require_permission("user:view")
def get_users():
    users = User.query.all()
    return jsonify({
        "code": 200,
        "data": [{
            "id":         u.id,
            "username":   u.username,
            "email":      u.email,
            "is_active":  u.is_active,
            "roles":      [r.name for r in u.roles],
            "created_at": u.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        } for u in users],
    })


# ── 更改用户角色 ──────────────────────────────
@admin_bp.route("/users/<int:user_id>", methods=["PUT"])
@login_required
@require_permission("user:edit")
def update_user(user_id):
    user = User.query.get_or_404(user_id)
    data = request.get_json() or {}

    if "roles" in data:
        user.roles = []
        for rname in data["roles"]:
            r = Role.query.filter_by(name=rname).first()
            if r:
                user.roles.append(r)
    if "is_active" in data:
        user.is_active = bool(data["is_active"])
    db.session.commit()

    write_audit_log(action="user:edit", detail=f"更改用户 {user.username} 角色")
    return jsonify({"code": 200, "message": "用户更新成功"})


# ── 权限列表（辅助接口）────────────────────────
@admin_bp.route("/permissions", methods=["GET"])
@login_required
@require_permission("role:manage")
def get_permissions():
    from itertools import groupby
    perms = Permission.query.order_by(Permission.category, Permission.name).all()
    grouped = {}
    for p in perms:
        grouped.setdefault(p.category, []).append({
            "id": p.id, "name": p.name, "description": p.description
        })
    return jsonify({"code": 200, "data": grouped})

