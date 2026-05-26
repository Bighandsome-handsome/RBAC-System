# 🔐 RBAC 文件管理系统 — 补充扩展包

> 基于 [drun16/flask_rbac_project](https://github.com/drun16/flask_rbac_project) 的二次扩展，
> 满足软件安全实验全部要求。

## 📁 本包文件结构

```
rbac_extension/
├── app/
│   ├── models/
│   │   └── models.py        ← ⭐ 数据库模型（6角色/权限/文件/审计）
│   ├── routes/
│   │   ├── files.py         ← ⭐ 文件操作 API（增删改查 + 权限控制）
│   │   └── admin.py         ← ⭐ 审计日志 & 角色管理 API
│   ├── templates/
│   │   └── file_manager.html ← ⭐ 前端资源管理器（完整 UI）
│   └── decorators.py        ← ⭐ 权限装饰器 + 审计日志工具
├── tests/
│   └── test_rbac.py         ← ⭐ 单元测试 & 集成测试（15个用例）
├── seed.py                  ← ⭐ 初始化6个角色和测试用户
└── requirements.txt
```

## 🚀 快速接入原项目

### 第一步：把文件复制到原项目

```bash
# 假设原项目路径为 flask_rbac_project/
cp app/models/models.py        flask_rbac_project/app/models.py     # 替换原 models.py
cp app/routes/files.py         flask_rbac_project/app/routes/
cp app/routes/admin.py         flask_rbac_project/app/routes/
cp app/decorators.py           flask_rbac_project/app/
cp app/templates/file_manager.html  flask_rbac_project/app/templates/
cp seed.py                     flask_rbac_project/
cp tests/test_rbac.py          flask_rbac_project/tests/
```

### 第二步：在原项目 `__init__.py` 注册蓝图

```python
# flask_rbac_project/app/__init__.py
from app.routes.files import files_bp
from app.routes.admin import admin_bp

def create_app(testing=False):
    app = Flask(__name__)
    # ... 原有配置 ...

    # 注册新蓝图
    app.register_blueprint(files_bp)
    app.register_blueprint(admin_bp)

    return app
```

### 第三步：配置 MySQL

```python
# config.py
SQLALCHEMY_DATABASE_URI = (
    "mysql+pymysql://用户名:20041025@localhost:3306/rbac_db?charset=utf8mb4"
)
UPLOAD_FOLDER = "uploads"   # 文件存储路径
```

### 第四步：初始化数据库

```bash
# 创建 MySQL 数据库
& "C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe" -u root -p -e "CREATE DATABASE rbac_db CHARACTER SET utf8mb4;"

mysql -u root -p -e "CREATE DATABASE rbac_db CHARACTER SET utf8mb4;"

# 建表
flask db upgrade

# 写入6个角色和测试用户
python seed.py
```

### 第五步：运行 & 测试

```bash
python run.py
# 访问 http://127.0.0.1:5000

# 跑测试
pytest tests/test_rbac.py -v
```

---

## 🎭 六个角色说明

| 角色 | 账号 | 密码 | 可用权限 |
|---|---|---|---|
| SuperAdmin | superadmin | Super@123 | 全部 14 个权限 |
| Admin | admin | Admin@123 | 文件读写删+用户管理+审计查看 |
| Manager | manager | Mgr@1234 | 文件读写更新（不含删除）|
| Operator | operator | Ops@1234 | 文件读写+下载 |
| Auditor | auditor | Aud@1234 | 文件只读+审计导出 |
| Guest | guest | Guest@123 | 仅文件读取 |

## 🔑 权限列表（共 14 条）

| 权限名 | 分类 | 说明 |
|---|---|---|
| file:read | file | 读取文件内容 |
| file:write | file | 上传/新建文件 |
| file:update | file | 修改/重命名文件 |
| file:delete | file | 删除文件 |
| file:download | file | 下载文件 |
| folder:create | file | 新建文件夹 |
| folder:delete | file | 删除文件夹 |
| user:view | admin | 查看用户列表 |
| user:create | admin | 创建新用户 |
| user:edit | admin | 编辑用户信息 |
| user:delete | admin | 删除用户 |
| role:manage | admin | 管理角色与权限 |
| audit:view | system | 查看审计日志 |
| audit:export | system | 导出审计日志 CSV |

## 📡 API 接口列表

### 文件操作
| 方法 | 路径 | 所需权限 | 说明 |
|---|---|---|---|
| GET | /api/files/ | file:read | 列出文件 |
| POST | /api/files/upload | file:write | 上传文件 |
| GET | /api/files/<id>/download | file:download | 下载文件 |
| PUT | /api/files/<id> | file:update | 重命名/移动 |
| DELETE | /api/files/<id> | file:delete | 删除文件 |
| POST | /api/files/folder | folder:create | 新建文件夹 |

### 管理接口
| 方法 | 路径 | 所需权限 | 说明 |
|---|---|---|---|
| GET | /api/admin/audit | audit:view | 查看审计日志 |
| GET | /api/admin/audit/export | audit:export | 导出 CSV |
| GET | /api/admin/roles | role:manage | 列出角色 |
| POST | /api/admin/roles | role:manage | 新建角色 |
| PUT | /api/admin/roles/<id> | role:manage | 更新角色权限 |
| GET | /api/admin/users | user:view | 列出用户 |
| PUT | /api/admin/users/<id> | user:edit | 更改用户角色 |

## 🧪 测试用例说明

```
tests/test_rbac.py 共 15 个测试用例

TestModels（模型层）:
  ✅ test_user_has_permission_via_role     — 权限继承正确
  ✅ test_guest_limited_permissions        — Guest 仅有只读
  ✅ test_admin_full_file_permissions      — Admin 拥有所有文件权限
  ✅ test_auditor_can_view_audit_not_write — Auditor 只读+审计
  ✅ test_get_all_permissions_returns_set  — 权限聚合返回集合
  ✅ test_password_hashing                 — bcrypt 密码验证
  ✅ test_resource_to_dict                 — 文件序列化
  ✅ test_audit_log_creation               — 审计日志写入

TestFileAPI（文件接口）:
  ✅ test_unauthenticated_cannot_list_files — 未登录 → 401
  ✅ test_guest_can_read_files              — Guest 可读
  ✅ test_guest_cannot_upload               — Guest 不可写 → 403
  ✅ test_operator_can_upload               — Operator 可上传
  ✅ test_operator_cannot_delete            — Operator 不可删 → 403
  ✅ test_admin_can_delete                  — Admin 可删除

TestAdminAPI（管理接口）:
  ✅ test_guest_cannot_view_audit           — Guest 无审计权限 → 403
  ✅ test_auditor_can_view_audit            — Auditor 可查看日志
  ✅ test_guest_cannot_list_roles           — Guest 无角色管理权限
  ✅ test_denied_action_is_logged           — 拒绝操作自动写日志
```
