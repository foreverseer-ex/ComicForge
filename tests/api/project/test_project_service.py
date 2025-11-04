"""
测试项目服务层功能。

直接测试 ProjectService 的方法。
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
from api.services.db import ProjectService
from api.schemas.project import Project
from api.utils.path import project_home
from datetime import datetime


class TestProjectService:
    """测试项目服务层"""
    
    def test_create_and_get(self):
        """测试创建和获取项目"""
        project_id = "test-service-create-get"
        
        # 清理旧数据
        existing = ProjectService.get(project_id)
        if existing:
            ProjectService.delete(project_id)
        
        # 创建项目
        project = Project(
            project_id=project_id,
            title="服务层测试项目",
            author="测试作者",
            total_lines=1000,
            total_chapters=10,
            project_path=str(project_home / project_id)
        )
        
        created = ProjectService.create(project)
        assert created is not None
        assert created.project_id == project_id
        assert created.title == "服务层测试项目"
        
        print(f"\n[服务层创建] ✅ 成功: {created.project_id}")
        
        # 获取项目
        retrieved = ProjectService.get(project_id)
        assert retrieved is not None
        assert retrieved.project_id == project_id
        assert retrieved.title == "服务层测试项目"
        
        print(f"[服务层获取] ✅ 成功")
        
        # 清理
        ProjectService.delete(project_id)
    
    def test_update(self):
        """测试更新项目"""
        project_id = "test-service-update"
        
        # 清理旧数据
        existing = ProjectService.get(project_id)
        if existing:
            ProjectService.delete(project_id)
        
        # 创建项目
        project = Project(
            project_id=project_id,
            title="原始标题",
            project_path=str(project_home / project_id)
        )
        ProjectService.create(project)
        
        # 更新项目
        updated = ProjectService.update(
            project_id,
            title="更新后的标题",
            author="新作者",
            total_lines=2000
        )
        
        assert updated is not None
        assert updated.title == "更新后的标题"
        assert updated.author == "新作者"
        assert updated.total_lines == 2000
        
        print(f"\n[服务层更新] ✅ 成功")
        print(f"  标题: {updated.title}")
        print(f"  作者: {updated.author}")
        
        # 清理
        ProjectService.delete(project_id)
    
    def test_list(self):
        """测试列出项目"""
        # 创建几个测试项目
        test_ids = []
        for i in range(3):
            project_id = f"test-service-list-{i}"
            test_ids.append(project_id)
            
            existing = ProjectService.get(project_id)
            if existing:
                ProjectService.delete(project_id)
            
            project = Project(
                project_id=project_id,
                title=f"列表测试项目_{i}",
                project_path=str(project_home / project_id)
            )
            ProjectService.create(project)
        
        # 列出项目（使用更大的limit以确保获取所有测试项目）
        projects = ProjectService.list(limit=100, offset=0)
        assert isinstance(projects, list)
        
        # 验证测试项目在列表中
        test_project_ids = {p.project_id for p in projects if p.project_id in test_ids}
        # 由于可能还有其他测试项目，我们只验证至少找到我们创建的测试项目
        assert len(test_project_ids) == 3, f"应该找到3个测试项目，但只找到: {test_project_ids}"
        
        print(f"\n[服务层列表] ✅ 成功")
        print(f"  总项目数量: {len(projects)}")
        print(f"  测试项目数量: {len(test_project_ids)}")
        print(f"  测试项目ID: {sorted(test_project_ids)}")
        
        # 清理
        for project_id in test_ids:
            ProjectService.delete(project_id)
    
    def test_delete(self):
        """测试删除项目"""
        project_id = "test-service-delete"
        
        # 清理旧数据
        existing = ProjectService.get(project_id)
        if existing:
            ProjectService.delete(project_id)
        
        # 创建项目
        project = Project(
            project_id=project_id,
            title="删除测试项目",
            project_path=str(project_home / project_id)
        )
        ProjectService.create(project)
        
        # 验证存在
        assert ProjectService.get(project_id) is not None
        
        # 删除项目
        success = ProjectService.delete(project_id)
        assert success is True
        
        # 验证已删除
        deleted = ProjectService.get(project_id)
        assert deleted is None
        
        print(f"\n[服务层删除] ✅ 成功")
    
    def test_project_directory_initialization(self):
        """测试项目目录初始化"""
        project_id = "test-service-dir-init"
        
        # 清理旧数据
        existing = ProjectService.get(project_id)
        if existing:
            ProjectService.delete(project_id)
        
        # 创建项目
        project = Project(
            project_id=project_id,
            title="目录初始化测试",
            project_path=str(project_home / project_id)
        )
        created = ProjectService.create(project)
        
        # 验证目录已创建
        from pathlib import Path
        project_path = Path(created.project_path)
        assert project_path.exists()
        assert (project_path / "images").exists()
        assert (project_path / "illustration").exists()
        
        print(f"\n[目录初始化] ✅ 成功")
        print(f"  项目路径: {project_path}")
        print(f"  images 目录: {(project_path / 'images').exists()}")
        print(f"  illustration 目录: {(project_path / 'illustration').exists()}")
        
        # 清理
        ProjectService.delete(project_id)
