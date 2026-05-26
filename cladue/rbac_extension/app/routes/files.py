"""
routes/files.py — 文件操作路由

GET    /api/files/              列出文件（需 file:read）
POST   /api/files/upload        上传文件（需 file:write）
GET    /api/files/<id>/download 下载文件（需 file:download）
PUT    /api/files/<id>          重命名/移动（需 file:update）
DELETE /api/files/<id>          删除文件（需 file:delete）
POST   /api/files/folder        新建文件夹（需 folder:create）
"""

import os
from datetime import datetime
from flask import Blueprint, request, jsonify, send_from_directory, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from app.models.models import db, Resource, AuditLog
from app.decorators import require_permission, write_audit_log

files_bp = Blueprint("files", __name__, url_prefix="/api/files")

ALLOWED_EXTENSIONS = {
    "txt", "pdf", "png", "jpg", "jpeg", "gif", "bmp",
    "doc", "docx", "xls", "xlsx", "ppt", "pptx",
    "zip", "tar", "gz", "csv", "json", "xml", "md",
}


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def get_upload_dir() -> str:
    d = current_app.config.get("UPLOAD_FOLDER", "uploads")
    os.makedirs(d, exist_ok=True)
    return d


# ── 列出文件 ──────────────────────────────────
@files_bp.route("/", methods=["GET"])
@login_required
@require_permission("file:read")
def list_files():
    parent_id = request.args.get("parent_id", type=int)   # None = 根目录
    resources = Resource.query.filter_by(parent_id=parent_id).all()

    write_audit_log(action="file:read", detail=f"列出目录 parent_id={parent_id}")
    return jsonify({
        "code": 200,
        "data": [r.to_dict() for r in resources],
        "permissions": list(current_user.get_all_permissions()),
    })


# ── 上传文件 ──────────────────────────────────
@files_bp.route("/upload", methods=["POST"])
@login_required
@require_permission("file:write")
def upload_file():
    if "file" not in request.files:
        return jsonify({"error": "未选择文件", "code": 400}), 400

    f = request.files["file"]
    parent_id = request.form.get("parent_id", type=int)

    if f.filename == "":
        return jsonify({"error": "文件名为空", "code": 400}), 400

    if not allowed_file(f.filename):
        return jsonify({"error": "不允许的文件类型", "code": 400}), 400

    filename  = secure_filename(f.filename)
    save_path = os.path.join(get_upload_dir(), filename)
    f.save(save_path)

    resource = Resource(
        name         = filename,
        path         = save_path,
        size         = os.path.getsize(save_path),
        mime_type    = f.content_type,
        is_directory = False,
        parent_id    = parent_id,
        owner_id     = current_user.id,
    )
    db.session.add(resource)
    db.session.commit()

    write_audit_log(action="file:write", resource_id=resource.id,
                    detail=f"上传文件 {filename}")
    return jsonify({"code": 200, "data": resource.to_dict()})


# ── 下载文件 ──────────────────────────────────
@files_bp.route("/<int:resource_id>/download", methods=["GET"])
@login_required
@require_permission("file:download")
def download_file(resource_id):
    resource = Resource.query.get_or_404(resource_id)
    if resource.is_directory:
        return jsonify({"error": "不能下载文件夹", "code": 400}), 400

    write_audit_log(action="file:download", resource_id=resource_id,
                    detail=f"下载 {resource.name}")
    directory = os.path.dirname(resource.path)
    return send_from_directory(directory, resource.name, as_attachment=True)


# ── 重命名/更新文件 ───────────────────────────
@files_bp.route("/<int:resource_id>", methods=["PUT"])
@login_required
@require_permission("file:update")
def update_file(resource_id):
    resource = Resource.query.get_or_404(resource_id)
    data = request.get_json() or {}

    old_name = resource.name
    if "name" in data:
        resource.name = data["name"]
    if "parent_id" in data:
        resource.parent_id = data["parent_id"]
    resource.updated_at = datetime.utcnow()

    db.session.commit()
    write_audit_log(action="file:update", resource_id=resource_id,
                    detail=f"重命名 {old_name} → {resource.name}")
    return jsonify({"code": 200, "data": resource.to_dict()})


# ── 删除文件 ──────────────────────────────────
@files_bp.route("/<int:resource_id>", methods=["DELETE"])
@login_required
@require_permission("file:delete")
def delete_file(resource_id):
    resource = Resource.query.get_or_404(resource_id)
    name = resource.name

    # 如果是目录，递归删除子资源
    if resource.is_directory:
        _recursive_delete(resource)
    else:
        if os.path.exists(resource.path):
            os.remove(resource.path)

    db.session.delete(resource)
    db.session.commit()

    write_audit_log(action="file:delete", detail=f"删除 {name}")
    return jsonify({"code": 200, "message": f"已删除 {name}"})


def _recursive_delete(resource: Resource):
    for child in resource.children:
        if child.is_directory:
            _recursive_delete(child)
        else:
            if os.path.exists(child.path):
                os.remove(child.path)
        db.session.delete(child)


# ── 新建文件夹 ────────────────────────────────
@files_bp.route("/folder", methods=["POST"])
@login_required
@require_permission("folder:create")
def create_folder():
    data = request.get_json() or {}
    name = data.get("name", "").strip()
    parent_id = data.get("parent_id")

    if not name:
        return jsonify({"error": "文件夹名不能为空", "code": 400}), 400

    folder = Resource(
        name         = name,
        path         = "",
        is_directory = True,
        parent_id    = parent_id,
        owner_id     = current_user.id,
    )
    db.session.add(folder)
    db.session.commit()

    write_audit_log(action="folder:create", resource_id=folder.id,
                    detail=f"新建文件夹 {name}")
    return jsonify({"code": 200, "data": folder.to_dict()})
