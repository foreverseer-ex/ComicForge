"""
测试项目 CRUD 操作。

测试创建、读取、更新、删除项目的基本功能。
"""
import sys
from pathlib import Path

# 添加 src 目录到 Python 路径
current_file = Path(__file__).resolve()
tests_dir = current_file.parent.parent.parent
project_root = tests_dir.parent
src_path = project_root / "src"
if src_path.exists():
    if str(tests_dir) in sys.path:
        sys.path.remove(str(tests_dir))
    sys.path.insert(0, str(src_path))

import pytest
from fastapi.testclient import TestClient
from api.services.db import ProjectService


class TestProjectCRUD:
    """测试项目 CRUD 操作"""
    
    def test_create_project(self, client):
        """测试创建项目"""
        response = client.post(
            "/project/create",
            params={
                "title": "测试项目_CRUD",
                "novel_path": None
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "project_id" in data
        # 创建 API 现在只返回 project_id
        project_id = data["project_id"]
        
        # 验证项目确实被创建了（通过 GET 接口获取完整信息）
        get_response = client.get(f"/project/{project_id}")
        assert get_response.status_code == 200
        project_data = get_response.json()
        assert project_data["title"] == "测试项目_CRUD"
        assert "project_path" in project_data
        assert "created_at" in project_data
        assert "updated_at" in project_data
        
        print(f"\n[创建项目] ✅ 成功")
        print(f"  Project ID: {project_id}")
        print(f"  标题: {project_data['title']}")
        
        # 保存 project_id 供后续测试使用
        pytest.test_project_id = project_id
    
    def test_get_project(self, client):
        """测试获取项目"""
        # 先创建一个项目
        create_response = client.post(
            "/project/create",
            params={"title": "测试项目_获取"}
        )
        assert create_response.status_code == 200
        project_id = create_response.json()["project_id"]
        
        # 获取项目
        response = client.get(f"/project/{project_id}")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["project_id"] == project_id
        assert data["title"] == "测试项目_获取"
        
        print(f"\n[获取项目] ✅ 成功")
        print(f"  Project ID: {data['project_id']}")
        print(f"  标题: {data['title']}")
    
    def test_get_nonexistent_project(self, client):
        """测试获取不存在的项目"""
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = client.get(f"/project/{fake_id}")
        
        assert response.status_code == 404
        assert "不存在" in response.json()["detail"]
        
        print(f"\n[获取不存在项目] ✅ 正确返回 404")
    
    def test_list_projects(self, client):
        """测试列出所有项目"""
        # 先创建几个项目
        for i in range(3):
            client.post(
                "/project/create",
                params={"title": f"测试项目_列表_{i}"}
            )
        
        # 列出项目
        response = client.get("/project/list", params={"limit": 50, "offset": 0})
        
        assert response.status_code == 200
        projects = response.json()
        
        assert isinstance(projects, list)
        assert len(projects) >= 3
        
        print(f"\n[列出项目] ✅ 成功")
        print(f"  项目数量: {len(projects)}")
        
        # 测试分页
        response_page = client.get("/project/list", params={"limit": 2, "offset": 0})
        assert response_page.status_code == 200
        projects_page = response_page.json()
        assert len(projects_page) <= 2
        
        print(f"  分页测试: limit=2, 返回 {len(projects_page)} 条")
    
    def test_update_project(self, client):
        """测试更新项目"""
        # 先创建项目
        create_response = client.post(
            "/project/create",
            params={"title": "测试项目_更新"}
        )
        project_id = create_response.json()["project_id"]
        
        # 更新项目
        response = client.put(
            f"/project/{project_id}",
            params={
                "title": "更新后的标题",
                "author": "测试作者",
                "total_lines": 1000,
                "total_chapters": 10,
                "current_line": 100,
                "current_chapter": 1
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["title"] == "更新后的标题"
        assert data["author"] == "测试作者"
        assert data["total_lines"] == 1000
        assert data["total_chapters"] == 10
        assert data["current_line"] == 100
        assert data["current_chapter"] == 1
        
        print(f"\n[更新项目] ✅ 成功")
        print(f"  标题: {data['title']}")
        print(f"  作者: {data['author']}")
        print(f"  总行数: {data['total_lines']}")
        
        # 测试部分更新
        response_partial = client.put(
            f"/project/{project_id}",
            params={"title": "部分更新标题"}
        )
        assert response_partial.status_code == 200
        data_partial = response_partial.json()
        assert data_partial["title"] == "部分更新标题"
        assert data_partial["author"] == "测试作者"  # 其他字段应该保持不变
        
        print(f"  部分更新: ✅ 成功")
    
    def test_update_nonexistent_project(self, client):
        """测试更新不存在的项目"""
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = client.put(
            f"/project/{fake_id}",
            params={"title": "新标题"}
        )
        
        assert response.status_code == 404
        assert "不存在" in response.json()["detail"]
        
        print(f"\n[更新不存在项目] ✅ 正确返回 404")
    
    def test_delete_project(self, client):
        """测试删除项目"""
        # 先创建项目
        create_response = client.post(
            "/project/create",
            params={"title": "测试项目_删除"}
        )
        project_id = create_response.json()["project_id"]
        
        # 验证项目存在
        get_response = client.get(f"/project/{project_id}")
        assert get_response.status_code == 200
        
        # 删除项目
        response = client.delete(f"/project/{project_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "项目删除成功"
        assert data["project_id"] == project_id
        
        print(f"\n[删除项目] ✅ 成功")
        print(f"  Project ID: {project_id}")
        
        # 验证项目已被删除
        get_response_after = client.get(f"/project/{project_id}")
        assert get_response_after.status_code == 404
        
        print(f"  验证删除: ✅ 项目已不存在")
    
    def test_delete_nonexistent_project(self, client):
        """测试删除不存在的项目"""
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = client.delete(f"/project/{fake_id}")
        
        assert response.status_code == 404
        assert "不存在" in response.json()["detail"]
        
        print(f"\n[删除不存在项目] ✅ 正确返回 404")
    
    def test_update_progress(self, client):
        """测试更新处理进度"""
        # 先创建项目
        create_response = client.post(
            "/project/create",
            params={"title": "测试项目_进度"}
        )
        project_id = create_response.json()["project_id"]
        
        # 更新进度
        response = client.put(
            f"/project/{project_id}/progress",
            params={
                "current_line": 500,
                "current_chapter": 5
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["current_line"] == 500
        assert data["current_chapter"] == 5
        
        print(f"\n[更新进度] ✅ 成功")
        print(f"  当前行: {data['current_line']}")
        print(f"  当前章节: {data['current_chapter']}")
        
        # 验证 updated_at 已更新
        get_response = client.get(f"/project/{project_id}")
        assert get_response.status_code == 200
        updated_data = get_response.json()
        assert updated_data["updated_at"] is not None
        
        print(f"  更新时间: ✅ 已更新")
    
    def test_project_lifecycle(self, client):
        """测试项目完整生命周期"""
        # 1. 创建
        create_response = client.post(
            "/project/create",
            params={"title": "生命周期测试项目"}
        )
        assert create_response.status_code == 200
        project_id = create_response.json()["project_id"]
        print(f"\n[生命周期测试] 1. 创建项目: {project_id}")
        
        # 2. 获取
        get_response = client.get(f"/project/{project_id}")
        assert get_response.status_code == 200
        print(f"[生命周期测试] 2. 获取项目: ✅")
        
        # 3. 更新
        update_response = client.put(
            f"/project/{project_id}",
            params={"title": "更新后的生命周期测试"}
        )
        assert update_response.status_code == 200
        assert update_response.json()["title"] == "更新后的生命周期测试"
        print(f"[生命周期测试] 3. 更新项目: ✅")
        
        # 4. 更新进度
        progress_response = client.put(
            f"/project/{project_id}/progress",
            params={"current_line": 100, "current_chapter": 1}
        )
        assert progress_response.status_code == 200
        print(f"[生命周期测试] 4. 更新进度: ✅")
        
        # 5. 删除
        delete_response = client.delete(f"/project/{project_id}")
        assert delete_response.status_code == 200
        print(f"[生命周期测试] 5. 删除项目: ✅")
        
        # 6. 验证已删除
        get_after_delete = client.get(f"/project/{project_id}")
        assert get_after_delete.status_code == 404
        print(f"[生命周期测试] 6. 验证删除: ✅")
        print(f"[生命周期测试] ✅ 完整生命周期测试通过")
