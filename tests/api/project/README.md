# 项目管理功能测试包

本测试包专门测试项目管理相关的所有 CRUD 操作。

## 测试文件结构

```
tests/api/project/
├── __init__.py                # 包初始化
├── conftest.py                # 共享 fixtures
├── test_project_crud.py       # API 端点 CRUD 测试
├── test_project_service.py    # 服务层测试
└── README.md                  # 本文件
```

## 测试说明

### 1. API 端点测试

**文件**: `test_project_crud.py`

使用 FastAPI TestClient 测试所有 API 端点。

**测试用例**:
- `test_create_project`: 测试创建项目
- `test_get_project`: 测试获取项目
- `test_get_nonexistent_project`: 测试获取不存在的项目（404）
- `test_list_projects`: 测试列出项目（包括分页）
- `test_update_project`: 测试更新项目（包括部分更新）
- `test_update_nonexistent_project`: 测试更新不存在的项目（404）
- `test_delete_project`: 测试删除项目
- `test_delete_nonexistent_project`: 测试删除不存在的项目（404）
- `test_update_progress`: 测试更新处理进度
- `test_project_lifecycle`: 测试项目完整生命周期

### 2. 服务层测试

**文件**: `test_project_service.py`

直接测试 `ProjectService` 的方法。

**测试用例**:
- `test_create_and_get`: 测试创建和获取
- `test_update`: 测试更新项目
- `test_list`: 测试列出项目
- `test_delete`: 测试删除项目
- `test_project_directory_initialization`: 测试项目目录初始化

## API 端点覆盖

### 创建项目
- `POST /project/create` - 创建新项目

### 查询项目
- `GET /project/{project_id}` - 获取项目信息
- `GET /project/` - 列出所有项目（支持分页）

### 更新项目
- `PUT /project/{project_id}` - 更新项目信息
- `PUT /project/{project_id}/progress` - 更新处理进度

### 删除项目
- `DELETE /project/{project_id}` - 删除项目

## 运行测试

### 运行所有项目管理测试

```bash
uv run pytest tests/api/project/ -v
```

### 运行特定测试文件

```bash
# 测试 API 端点
uv run pytest tests/api/project/test_project_crud.py -v

# 测试服务层
uv run pytest tests/api/project/test_project_service.py -v
```

### 运行特定测试用例

```bash
# 测试创建项目
uv run pytest tests/api/project/test_project_crud.py::TestProjectCRUD::test_create_project -v

# 测试项目生命周期
uv run pytest tests/api/project/test_project_crud.py::TestProjectCRUD::test_project_lifecycle -v
```

## 注意事项

1. **数据库**: 测试会自动初始化数据库，测试数据会写入实际数据库文件
2. **清理**: 测试会尝试清理创建的测试项目，但建议在测试后手动检查
3. **项目目录**: 测试会创建实际的项目目录结构，测试后可能需要手动清理
4. **路径问题**: 所有测试文件都包含路径设置逻辑，确保 `src` 目录在 Python 路径中

## 测试覆盖

- ✅ 创建项目
- ✅ 获取项目（存在和不存在）
- ✅ 列出项目（包括分页）
- ✅ 更新项目（完整和部分更新）
- ✅ 删除项目
- ✅ 更新进度
- ✅ 项目生命周期
- ✅ 服务层方法
- ✅ 项目目录初始化

所有测试都包含错误处理（404 等）和边界情况验证。
