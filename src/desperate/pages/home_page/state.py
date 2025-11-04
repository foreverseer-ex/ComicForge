"""
主页状态。

管理项目列表、当前选中的项目、当前段落等信息。
"""
from dataclasses import dataclass, field

import flet as ft

from api.schemas.project import Project
from api.services.db import ProjectService
from api.settings import app_settings


@dataclass
@ft.observable
class HomePageState:
    """主页状态。
    
    管理项目列表、当前选中的项目、当前段落等信息。
    """
    projects: list[Project] = field(default_factory=list)
    current_project_id: str | None = None
    current_paragraph_content: str = ""
    current_paragraph_info: str = ""
    can_go_prev: bool = False
    can_go_next: bool = False

    def load(self) -> None:
        """从数据库和配置加载数据。
        
        加载项目列表，并从 settings 恢复上次选中的项目。
        """
        # 从数据库加载项目列表
        self.projects = ProjectService.list()
        
        # 从 settings 恢复上次选中的项目
        if app_settings.ui.current_project_id:
            project = ProjectService.get(app_settings.ui.current_project_id)
            if project:
                self.current_project_id = project.project_id
                # 加载当前段落
                self.load_current_paragraph()
        elif self.projects:
            # 如果没有保存的项目但有项目列表，选中第一个
            self.current_project_id = self.projects[0].project_id
            self.load_current_paragraph()

    def save(self) -> None:
        """将当前选中的项目ID保存到配置。
        
        只保存 current_project_id，其他属性不需要持久化。
        """
        app_settings.ui.current_project_id = self.current_project_id
        app_settings.save()

    def select_project(self, project_id: str | None):
        """选择项目。"""
        if project_id != self.current_project_id:
            self.current_project_id = project_id
            # 加载当前段落
            self.load_current_paragraph()
            # 保存到配置
            self.save()

    def load_current_paragraph(self):
        """加载当前段落内容。"""
        # TODO: 实现加载逻辑
        pass

    def prev_paragraph(self):
        """切换到上一段。"""
        # TODO: 实现逻辑
        pass

    def next_paragraph(self):
        """切换到下一段。"""
        # TODO: 实现逻辑
        pass

    def create_project(self):
        """打开创建项目对话框。"""
        # TODO: 实现逻辑
        pass

    def delete_project(self):
        """打开删除项目对话框。"""
        # TODO: 实现逻辑
        pass

    @property
    def current_project(self) -> Project | None:
        """获取当前选中的项目对象。"""
        if not self.current_project_id:
            return None
        # 从 projects 列表中查找
        for project in self.projects:
            if project.project_id == self.current_project_id:
                return project
        return None
