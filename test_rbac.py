"""
tests/test_rbac.py — RBAC 系统单元测试 & 集成测试

运行方式：
    pytest tests/test_rbac.py -v
"""

import pytest
from app import create_app
from app.models.models import db, User, Role, Permission, Resource, AuditLog


# ──────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────
@pytest.fixture
def app():
    app = create_app(testing=True)   # 使用 SQLite 内存数据库
    with app.app_context():
        db.create_all()
        _seed_test_data()
        yield app
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


def _seed_test_data():
    """插入测试用的权限、角色和用户"""
    # 权限
    p_read   = Permission(name="file:read",   category="file", description="读取")
    p_write  = Permission(name="file:write",  category="file", description="写入")
    p_delete = Permission(name="file:delete", category="file", description="删除")
    p_audit  = Permission(name="audit:view",  category="system", description="审计")
    db.session.add_all([p_read, p_write, p_delete, p_audit])
    db.session.flush()

    # 角色
    r_guest   = Role(name="Guest",   description="访客")
    r_op      = Role(name="Operator", description="操作员")
    r_admin   = Role(name="Admin",   description="管理员")
    r_auditor = Role(name="Auditor", description="审计员")

    r_guest.permissions.append(p_read)
    r_op.permissions   += [p_read, p_write]
    r_admin.permissions += [p_read, p_write, p_delete]
    r_auditor.permissions += [p_read, p_audit]
    db.session.add_all([r_guest, r_op, r_admin, r_auditor])
    db.session.flush()

    # 用户
    u_guest = User(username="guest_user", email="guest@test.com")
    u_guest.set_password("pass1234")
    u_guest.roles.append(r_guest)

    u_op = User(username="op_user", email="op@test.com")
    u_op.set_password("pass1234")
    u_op.roles.append(r_op)

    u_admin = User(username="admin_user", email="admin@test.com")
    u_admin.set_password("pass1234")
    u_admin.roles.append(r_admin)

    u_auditor = User(username="auditor_user", email="auditor@test.com")
    u_auditor.set_password("pass1234")
    u_auditor.roles.append(r_auditor)

    db.session.add_all([u_guest, u_op, u_admin, u_auditor])
    db.session.commit()


def login(client, username, password="pass1234"):
    return client.post("/auth/login", json={"username": username, "password": password})


# ──────────────────────────────────────────────
# 1. 模型层单元测试
# ──────────────────────────────────────────────
class TestModels:
    def test_user_has_permission_via_role(self, app):
        with app.app_context():
            u = User.query.filter_by(username="op_user").first()
            assert u.has_permission("file:read")
            assert u.has_permission("file:write")
            assert not u.has_permission("file:delete")

    def test_guest_limited_permissions(self, app):
        with app.app_context():
            u = User.query.filter_by(username="guest_user").first()
            assert u.has_permission("file:read")
            assert not u.has_permission("file:write")
            assert not u.has_permission("file:delete")

    def test_admin_full_file_permissions(self, app):
        with app.app_context():
            u = User.query.filter_by(username="admin_user").first()
            for perm in ("file:read", "file:write", "file:delete"):
                assert u.has_permission(perm), f"Admin 缺少权限 {perm}"

    def test_auditor_can_view_audit_not_write(self, app):
        with app.app_context():
            u = User.query.filter_by(username="auditor_user").first()
            assert u.has_permission("audit:view")
            assert not u.has_permission("file:write")

    def test_get_all_permissions_returns_set(self, app):
        with app.app_context():
            u = User.query.filter_by(username="admin_user").first()
            perms = u.get_all_permissions()
            assert isinstance(perms, set)
            assert "file:delete" in perms

    def test_password_hashing(self, app):
        with app.app_context():
            u = User.query.filter_by(username="guest_user").first()
            assert u.check_password("pass1234")
            assert not u.check_password("wrongpassword")

    def test_resource_to_dict(self, app):
        with app.app_context():
            owner = User.query.filter_by(username="admin_user").first()
            r = Resource(name="test.txt", path="/tmp/test.txt", owner_id=owner.id)
            db.session.add(r)
            db.session.commit()
            d = r.to_dict()
            assert d["name"] == "test.txt"
            assert d["owner"] == "admin_user"

    def test_audit_log_creation(self, app):
        with app.app_context():
            owner = User.query.filter_by(username="admin_user").first()
            log = AuditLog(user_id=owner.id, action="file:delete",
                           status="success", ip_address="127.0.0.1")
            db.session.add(log)
            db.session.commit()
            assert AuditLog.query.count() == 1
            assert log.to_dict()["action"] == "file:delete"


# ──────────────────────────────────────────────
# 2. 接口集成测试
# ──────────────────────────────────────────────
class TestFileAPI:
    def test_unauthenticated_cannot_list_files(self, client):
        resp = client.get("/api/files/")
        assert resp.status_code == 401

    def test_guest_can_read_files(self, client):
        login(client, "guest_user")
        resp = client.get("/api/files/")
        assert resp.status_code == 200

    def test_guest_cannot_upload(self, client):
        login(client, "guest_user")
        resp = client.post("/api/files/upload", data={})
        assert resp.status_code == 403

    def test_operator_can_upload(self, client, tmp_path, app):
        login(client, "op_user")
        f = tmp_path / "hello.txt"
        f.write_text("hello world")
        with open(f, "rb") as fobj:
            resp = client.post(
                "/api/files/upload",
                data={"file": (fobj, "hello.txt")},
                content_type="multipart/form-data",
            )
        assert resp.status_code == 200

    def test_operator_cannot_delete(self, client, app):
        with app.app_context():
            owner = User.query.filter_by(username="op_user").first()
            r = Resource(name="dummy.txt", path="/tmp/dummy.txt", owner_id=owner.id)
            db.session.add(r)
            db.session.commit()
            rid = r.id
        login(client, "op_user")
        resp = client.delete(f"/api/files/{rid}")
        assert resp.status_code == 403

    def test_admin_can_delete(self, client, app):
        with app.app_context():
            owner = User.query.filter_by(username="admin_user").first()
            r = Resource(name="todelete.txt", path="/tmp/todelete.txt", owner_id=owner.id)
            db.session.add(r)
            db.session.commit()
            rid = r.id
        login(client, "admin_user")
        resp = client.delete(f"/api/files/{rid}")
        assert resp.status_code == 200


class TestAdminAPI:
    def test_guest_cannot_view_audit(self, client):
        login(client, "guest_user")
        resp = client.get("/api/admin/audit")
        assert resp.status_code == 403

    def test_auditor_can_view_audit(self, client):
        login(client, "auditor_user")
        resp = client.get("/api/admin/audit")
        assert resp.status_code == 200
        assert resp.json["code"] == 200

    def test_guest_cannot_list_roles(self, client):
        login(client, "guest_user")
        resp = client.get("/api/admin/roles")
        assert resp.status_code == 403

    def test_denied_action_is_logged(self, client, app):
        """权限拒绝时应自动写入审计日志"""
        login(client, "guest_user")
        client.post("/api/files/upload", data={})  # 无 file:write 权限
        with app.app_context():
            denied = AuditLog.query.filter_by(status="denied").first()
            assert denied is not None
