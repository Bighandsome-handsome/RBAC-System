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
from flask import Blueprint, send_from_directory, jsonify, make_response
from app.models import db, Resource, AuditLog
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


# # ── 下载文件 ──────────────────────────────────
# @files_bp.route("/<int:resource_id>/download", methods=["GET"])
# @login_required
# @require_permission("file:download")
# def download_file(resource_id):
#     resource = Resource.query.get_or_404(resource_id)
#     if resource.is_directory:
#         return jsonify({"error": "不能下载文件夹", "code": 400}), 400

#     write_audit_log(action="file:download", resource_id=resource_id,
#                     detail=f"下载 {resource.name}")
#     directory = os.path.dirname(resource.path)
#     return send_from_directory(directory, resource.name, as_attachment=True)

# @files_bp.route("/<int:resource_id>/download", methods=["GET"])
# @login_required
# @require_permission("file:download") # 确保只有有下载权的人能进来
# def download_file(resource_id):
#     resource = Resource.query.get(resource_id)
    
#     if not resource:
#         print(f"\n 下载失败警报: 前端尝试下载 ID 为 {resource_id} 的文件，但数据库查无此人！")
#         all_ids = [r.id for r in Resource.query.all()]
#         print(f"💡 当前数据库 resource 表中真正存在的有效 ID 列表为: {all_ids}")
#         return jsonify({"error": f"数据库找不到该文件记录，无法下载", "code": 404}), 404

#     if resource.is_directory:
#         return jsonify({"error": "不能下载文件夹", "code": 400}), 400

#     # 转换为绝对路径读取
#     abs_path = os.path.abspath(resource.path)
#     directory = os.path.dirname(abs_path)
#     real_filename = os.path.basename(abs_path)

#     if not os.path.exists(abs_path):
#         print(f" 下载失败：数据库有记录，但服务器磁盘找不到物理文件: {abs_path}")
#         return jsonify({"error": "物理文件丢失", "code": 404}), 404

#     print(f"💾【开始下载】: 正在把文件【{real_filename}】作为附件推送到浏览器...")
    
#     # 🌟 as_attachment=True 会强行让浏览器弹出“另存为”保存框，而不是在网页里打开
#     return send_from_directory(directory, real_filename, as_attachment=True)


# # ── 重命名/更新文件 ───────────────────────────
# @files_bp.route("/<int:resource_id>", methods=["PUT"])
# @login_required
# @require_permission("file:update")
# def update_file(resource_id):
#     resource = Resource.query.get_or_404(resource_id)
#     data = request.get_json() or {}

#     old_name = resource.name
#     if "name" in data:
#         resource.name = data["name"]
#     if "parent_id" in data:
#         resource.parent_id = data["parent_id"]
#     resource.updated_at = datetime.utcnow()

#     db.session.commit()
#     write_audit_log(action="file:update", resource_id=resource_id,
#                     detail=f"重命名 {old_name} → {resource.name}")
#     return jsonify({"code": 200, "data": resource.to_dict()})

@files_bp.route("/<int:resource_id>", methods=["PUT"])
@login_required
@require_permission("file:update")
def update_file(resource_id):
    resource = Resource.query.get_or_404(resource_id)
    data = request.get_json() or {}

    old_name = resource.name
    
    if "name" in data:
        new_name = data["name"].strip()
        if new_name and new_name != old_name:
            # 1. 只有非空且发生改变时才处理
            # 拿到原文件的绝对物理路径
            old_abs_path = os.path.abspath(resource.path)
            
            # 2. 计算新文件的绝对物理路径（基于当前的 UPLOAD_FOLDER 配置，或者是旧路径的同级目录）
            upload_dir = get_upload_dir()
            new_abs_path = os.path.abspath(os.path.join(upload_dir, new_name))
            
            # 3. 联动修改服务器硬盘上的真实物理文件名
            if os.path.exists(old_abs_path):
                try:
                    os.rename(old_abs_path, new_abs_path)
                    print(f"[硬盘同步成功]: 物理文件已更名 {old_abs_path} -> {new_abs_path}")
                except Exception as e:
                    print(f"[硬盘改名失败]: {str(e)}")
                    return jsonify({"error": f"服务器文件更名失败: {str(e)}", "code": 500}), 500
            
            # 4. 同步将新名字和【绝对路径】写回数据库，死死焊死
            resource.name = new_name
            resource.path = new_abs_path

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

# ── 在线预览文件（允许 Guest 网页阅读，但不提供下载标头） ─────────────────
# @files_bp.route("/<int:resource_id>/preview", methods=["GET"])
# @login_required
# @require_permission("file:read") # 🌟 Guest 拥有 file:read，所以可以通过此检查！
# def preview_file(resource_id):
#     resource = Resource.query.get_or_404(resource_id)
#     if resource.is_directory:
#         return jsonify({"error": "不能预览文件夹", "code": 400}), 400

#     directory = os.path.dirname(resource.path)
    
#     # 不加 as_attachment=True，浏览器收到后会自动在网页内打开预览（如PDF、图片、TXT）
#     return send_from_directory(directory, resource.name, as_attachment=False)
# def preview_file(resource_id):
#     resource = Resource.query.get(resource_id)
#     if not resource:
#         return jsonify({"error": "找不到文件记录", "code": 404}), 404
        
#     if resource.is_directory:
#         return jsonify({"error": "不能预览文件夹", "code": 400}), 400

#     abs_path = os.path.abspath(resource.path)
#     directory = os.path.dirname(abs_path)
    
#     real_filename = os.path.basename(abs_path)

#     print(f"【真正外发: 目标目录: {directory} | 真实文件名: {real_filename}")

#     if not os.path.exists(abs_path):
#         print(f"物理文件不存在: {abs_path}")
#         return jsonify({"error": "物理文件丢失", "code": 404}), 404

#     # 🌟 核心修正3：为了防止本地网络环境干扰，显式在响应头中标记为不下载、支持内联预览
#     from flask import make_response
#     try:
#         response = make_response(send_from_directory(directory, real_filename, as_attachment=False))
#         # 强行给浏览器注入内联 PDF 的 Content-Type 声明
#         if real_filename.lower().endswith('.pdf'):
#             response.headers['Content-Type'] = 'application/pdf'
#         return response
#     except Exception as e:
#         print(f"发送流异常: {str(e)}")
#         return jsonify({"error": "构建文件流失败", "code": 500}), 500

@files_bp.route("/<int:resource_id>/preview", methods=["GET"])
@login_required
@require_permission("file:read") # 🌟 Guest 拥有 file:read，Admin 同样拥有
def preview_file(resource_id):
    resource = Resource.query.get(resource_id)
    if not resource:
        return jsonify({"error": "找不到文件记录", "code": 404}), 404
        
    if resource.is_directory:
        return jsonify({"error": "不能预览文件夹", "code": 400}), 400

    abs_path = os.path.abspath(resource.path)
    directory = os.path.dirname(abs_path)
    real_filename = os.path.basename(abs_path)

    print(f"【真正外发】: 目标目录: {directory} | 真实文件名: {real_filename}")

    if not os.path.exists(abs_path):
        print(f"物理文件不存在: {abs_path}")
        return jsonify({"error": "物理文件丢失", "code": 404}), 404

    try:
        # as_attachment=False 告诉浏览器这是内联预览
        response = make_response(send_from_directory(directory, real_filename, as_attachment=False))
        
        # 根据文件类型注入标准的 Content-Type 声明
        if real_filename.lower().endswith('.pdf'):
            response.headers['Content-Type'] = 'application/pdf'
            # 🌟【硬核加固】：在 HTTP 响应头中注入安全响应头，告诉支持该标准的浏览器不要展示下载/另存为按钮
            response.headers['Content-Disposition'] = f'inline; filename="{real_filename}"'
        elif real_filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
            response.headers['Content-Type'] = 'image/jpeg'
        elif real_filename.lower().endswith(('.txt', '.md')):
            response.headers['Content-Type'] = 'text/plain; charset=utf-8'
            
        return response
    except Exception as e:
        print(f"发送流异常: {str(e)}")
        return jsonify({"error": "构建文件流失败", "code": 500}), 500

@files_bp.route("/<int:resource_id>/download", methods=["GET"])
@login_required
# ❌ 注意：这里不要加 @require_permission 装饰器了！
def download_file(resource_id):
    resource = Resource.query.get(resource_id)

    if not resource:
        return jsonify({"error": "数据库找不到该文件记录", "code": 404}), 404

    if resource.is_directory:
        return jsonify({"error": "不能下载文件夹", "code": 400}), 400

    # 🌟 核心修改：动态权限豁免逻辑
    # 规则：如果是共享文件，直接放行；如果非共享，必须强制校验 file:download 权限
    if not resource.is_shared and not current_user.has_permission("file:download"):
        write_audit_log(
            action="file:download", 
            resource_id=resource_id,
            status="denied", 
            detail="权限不足：请求下载非共享资产"
        )
        return jsonify({"error": "权限不足：该文件不在共享区，需要下载权限", "code": 403}), 403

    # 物理文件提取逻辑
    abs_path = os.path.abspath(resource.path)
    directory = os.path.dirname(abs_path)
    real_filename = os.path.basename(abs_path)

    if not os.path.exists(abs_path):
        return jsonify({"error": "物理文件丢失", "code": 404}), 404

    # 记录成功下载日志
    log_detail = f"下载了{'共享' if resource.is_shared else '私有'}文件 {real_filename}"
    write_audit_log(action="file:download", resource_id=resource_id, detail=log_detail)
    
    return send_from_directory(directory, real_filename, as_attachment=True)

# ── 在线编辑：保存文件内容 ─────────────────────
EDITABLE_EXTENSIONS = {".txt", ".md", ".csv", ".json", ".xml"}

@files_bp.route("/<int:resource_id>/content", methods=["PUT"])
@login_required
@require_permission("file:write")
def save_file_content(resource_id):
    """
    在线编辑保存接口
    PUT /api/files/<id>/content
    Body: { "content": "文件新内容" }
    需要 file:write 权限
    """
    resource = Resource.query.get(resource_id)
    if not resource:
        return jsonify({"error": "文件不存在", "code": 404}), 404
    if resource.is_directory:
        return jsonify({"error": "不能编辑文件夹", "code": 400}), 400

    # 只允许编辑文本类文件
    _, ext = os.path.splitext(resource.name.lower())
    if ext not in EDITABLE_EXTENSIONS:
        return jsonify({"error": f"不支持在线编辑 {ext} 类型文件", "code": 400}), 400

    data = request.get_json()
    if data is None or "content" not in data:
        return jsonify({"error": "请求体缺少 content 字段", "code": 400}), 400

    abs_path = os.path.abspath(resource.path)
    if not os.path.exists(abs_path):
        return jsonify({"error": "物理文件丢失", "code": 404}), 404

    try:
        with open(abs_path, "w", encoding="utf-8") as fobj:
            fobj.write(data["content"])

        resource.size = os.path.getsize(abs_path)
        resource.updated_at = datetime.utcnow()
        from app.models import db
        db.session.commit()

        write_audit_log(
            action="file:write",
            resource_id=resource_id,
            detail=f"在线编辑保存 {resource.name}"
        )
        return jsonify({"code": 200, "message": "保存成功"})

    except Exception as e:
        return jsonify({"error": f"写入失败: {str(e)}", "code": 500}), 500

@files_bp.route('/shared', methods=['GET'])
@login_required
def get_shared_files():
    """
    任何登录用户均可调用的共享主界面数据源网关。
    层级化拉取处于共享态（is_shared=True）的资产拓扑树。
    """
    parent_id = request.args.get('parent_id', type=int)
    
    # 过滤出所有显式开启共享的资源
    query = Resource.query.filter_by(is_shared=True)
    
    if parent_id:
        # 如果传入了父节点，说明前端正在共享文件夹内部进行深度纵向钻取（Drill-down）
        query = query.filter_by(parent_id=parent_id)
    else:
        query = query.filter_by(parent_id=None)
        
    resources = query.all()
    
    # 将模型数组序列化为标准 JSON 格式热推送给前端看板
    return jsonify({
        "code": 200,
        "data": [r.to_dict() for r in resources]
    })


@files_bp.route('/<int:resource_id>/share', methods=['PUT'])
@login_required
@require_permission('file:update')  # 要求主体必须有文件更新特权
def toggle_file_share(resource_id):
    """
    【辅助控制端点】：用于在主界面右键或菜单中，一键开启/关闭某个文件的共享状态
    """
    resource = Resource.query.get_or_404(resource_id)
    data = request.get_json() or {}
    
    # 动态切换布尔值状态位
    is_shared = bool(data.get('is_shared', True))
    resource.is_shared = is_shared
    db.session.commit()
    
    status_str = "发布共享" if is_shared else "取消共享"
    write_audit_log(action="file:share", detail=f"对资产 [{resource.name}] 执行 {status_str}")
    
    return jsonify({
        "code": 200,
        "message": f"成功修改资产共享状态为: {is_shared}"
    })

# ── 共享区上传（所有登录用户均可） ────────────────────────────
@files_bp.route('/shared/upload', methods=['POST'])
@login_required
@require_permission('file:read')   # 只要能登录就能上传到共享区（file:read 是最低权限）
def shared_upload():
    """
    任何角色均可上传文件到共享区。
    上传后自动设置 is_shared=True，无需额外操作。
    """
    if 'file' not in request.files:
        return jsonify({"error": "未选择文件", "code": 400}), 400

    f = request.files['file']
    if f.filename == '':
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
        parent_id    = None,
        owner_id     = current_user.id,
        is_shared    = True,          # 共享区文件直接标记为 shared
    )
    db.session.add(resource)
    db.session.commit()

    write_audit_log(action="file:write", resource_id=resource.id,
                    detail=f"上传到共享区: {filename}")
    return jsonify({"code": 200, "data": resource.to_dict()})


# ── 共享区文件修改（所有登录用户均可重命名） ──────────────────
@files_bp.route('/<int:resource_id>/shared-update', methods=['PUT'])
@login_required
@require_permission('file:read')   # 共享区最低权限即可修改
def shared_update_file(resource_id):
    """
    共享区专用修改接口：任何登录用户均可对共享文件进行重命名。
    非共享文件不允许通过此接口修改（防止绕过权限）。
    """
    resource = Resource.query.get_or_404(resource_id)

    # 安全检查：只能操作共享文件
    if not resource.is_shared:
        return jsonify({"error": "该文件不在共享区，无权修改", "code": 403}), 403

    data = request.get_json() or {}
    old_name = resource.name

    if 'name' in data and data['name'].strip():
        resource.name = data['name'].strip()

    from datetime import datetime
    resource.updated_at = datetime.utcnow()
    db.session.commit()

    write_audit_log(action="file:update", resource_id=resource_id,
                    detail=f"共享区重命名 {old_name} → {resource.name}")
    return jsonify({"code": 200, "data": resource.to_dict()})