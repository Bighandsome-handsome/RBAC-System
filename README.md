这是一份为您量身定制的 `README.md` 部署文档。它结合了您项目的实际结构（`app/`、蓝图、MySQL/SQLite 切换、测试套件等），可以直接复制到项目根目录下使用：

```markdown
# 🛡️ 基于 Flask 的安全 RBAC 系统 (RBACSystem)

本项目是一个基于 Flask 框架开发的、具备完善安全防护的**基于角色的访问控制 (RBAC) 系统**。系统实现了用户认证、多角色权限管理（Guest、Operator、Admin、Auditor）、文件安全操作管理以及全自动的安全审计日志留痕功能。

---

## 🚀 功能特性

- **精细化 RBAC 权限模型**：支持多对多关系（用户-角色-权限），实现动态鉴权。
- **文件安全管理 API**：具备文件读取、上传、删除的权限隔离判定。
- **全自动审计留痕**：任何越权行为（403 拒绝）和高危操作将自动记录至审计日志。
- **自动化环境自愈**：系统启动时会自动检测并创建 MySQL 数据库及相关表结构。
- **高覆盖率测试套件**：包含模型层单元测试与接口集成测试，确保核心逻辑零漏洞。

---

## 🛠️ 环境准备

请确保您的开发环境已安装以下软件：
- Python 3.11+
- MySQL 8.0+ (可选，系统默认支持 SQLite 内存/本地模式)
- Git

---

## 📦 部署步骤

### 1. 克隆项目到本地
```bash
git clone <您的项目仓库地址>
cd RBACSystem

```

### 2. 创建并激活虚拟环境

建议使用 `conda` 或 `venv` 管理依赖：

**使用 conda (推荐):**

```bash
conda create -n RBACSystem python=3.11
conda activate RBACSystem

```

**使用 venv:**

```bash
python -m venv venv
# Windows 激活:
.\venv\Scripts\activate
# Mac/Linux 激活:
source venv/bin/activate

```

### 3. 安装项目依赖

```bash
pip install -r requirements.txt

```

### 4. 配置文件引导 (`config.py`)

系统在 `config.py` 中管理配置。您可以根据实际需求切换数据库：

* **生产/开发环境 (MySQL)**：修改 `SQLALCHEMY_DATABASE_URI` 为您的实例地址。项目内置的 `create_database_if_not_exists` 函数会在启动时**自动创建**对应的库。
* **测试环境 (SQLite)**：无需额外配置，运行测试时会自动启用隔离的内存数据库。

---

## 🏃 启动与运行

### 1. 初始化数据库与表结构

在项目根目录下执行 Flask 迁移命令（或直接运行应用，系统会自动触发建表）：

```bash
flask db init
flask db migrate -m "Initial migration"
flask db upgrade

```

### 2. 启动本地开发服务器

```bash
python run.py

```

启动成功后，可在浏览器中访问：`http://127.0.0.1:5000`

---

## 🧪 自动化测试

项目配备了完善的单元测试与集成测试，覆盖了 RBAC 核心模型判定、未登录拦截、越权行为拦截以及审计日志闭环。

运行所有测试用例：

```bash
pytest test_rbac.py -v

```

> **注意**：测试脚本采用了 `session_transaction` 技术模拟登录态，并强制在 `sqlite:///:memory:` 内存数据库中运行，不会污染您的本地开发数据库。

