"""
项目（Project）数据库服务。

提供项目的增删改查操作。
"""
from typing import Optional
from pathlib import Path
from loguru import logger
from sqlmodel import select

from .base import DatabaseSession
from api.schemas.project import Project


class ProjectService:
    """
    项目数据库服务（单例模式）。
    
    使用类方法提供统一的 CRUD 接口。
    """
    
    @classmethod
    def init_project(cls, project: Project) -> bool:
        """
        初始化项目文件夹结构。
        
        创建以下目录：
        - images/: 存放生成的图片
        - illustration/: 存放立绘
        
        如果有原始小说文件，会自动解析并存入数据库。
        
        :param project: 会话对象
        :return: 是否初始化成功
        """
        try:
            project_path = Path(project.project_path)
            
            # 创建项目根目录
            project_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"创建项目目录: {project_path}")
            
            # 创建 images 文件夹（存放生成的图片）
            images_dir = project_path / "images"
            images_dir.mkdir(exist_ok=True)
            logger.info(f"创建 images 目录: {images_dir}")
            
            # 创建 illustration 文件夹（存放立绘）
            illustration_dir = project_path / "illustration"
            illustration_dir.mkdir(exist_ok=True)
            logger.info(f"创建 illustration 目录: {illustration_dir}")
            
            # 如果有小说文件，解析并存入数据库
            if project.novel_path:
                from api.services.transform import transform_service
                from api.services.novel_parser import novel_parser
                from .novel_service import NovelContentService
                
                source_file = Path(project.novel_path)
                
                if source_file.exists():
                    # 如果不是 TXT，先转换为 TXT
                    if source_file.suffix.lower() != '.txt':
                        # 创建临时 TXT 文件
                        temp_txt = project_path / "temp_novel.txt"
                        success = transform_service.transform_to_txt(source_file, temp_txt)
                        if not success:
                            logger.warning(f"小说转换失败: {source_file}")
                            return False
                        parse_file = temp_txt
                    else:
                        parse_file = source_file
                    
                    # 解析小说内容
                    novel_contents = novel_parser.parse_file(parse_file, project.project_id)
                    if not novel_contents:
                        logger.warning(f"小说解析失败: {parse_file}")
                        return False
                    
                    # 批量存入数据库
                    NovelContentService.batch_create(novel_contents)
                    logger.success(f"小说解析并存储成功: {len(novel_contents)} 行")
                    
                    # 删除临时文件
                    if source_file.suffix.lower() != '.txt':
                        temp_txt.unlink(missing_ok=True)
                else:
                    logger.warning(f"小说文件不存在: {source_file}")
            
            return True
            
        except Exception as e:
            logger.exception(f"初始化项目结构失败: {e}")
            return False
    
    @classmethod
    def create(cls, project: Project) -> Project:
        """
        创建项目。
        
        执行以下操作：
        1. 初始化项目文件夹结构（images/, illustration/）
        2. 如果有小说文件，解析并存入数据库
        3. 在数据库中创建 project 记录
        4. 更新小说统计信息（总行数、总章节数）
        
        :param project: 项目对象
        :return: 创建后的项目对象（包含自动生成的字段）
        """
        # 初始化项目文件夹结构（包括解析小说）
        if not cls.init_project(project):
            raise RuntimeError(f"初始化项目结构失败: {project.project_path}")
        
        # 在数据库中创建记录
        with DatabaseSession() as db:
            db.add(project)
            db.flush()  # 刷新以获取自动生成的字段
            db.refresh(project)
            db.expunge(project)  # 分离对象，使其可以在 session 外部使用
            logger.info(f"创建项目: {project.project_id}")
        
        # 如果有小说内容，更新统计信息
        if project.novel_path:
            from .novel_service import NovelContentService
            total_lines = NovelContentService.count_by_session(project.project_id)
            total_chapters = NovelContentService.count_chapters(project.project_id)
            
            # 更新 project 的统计信息
            updated_project = cls.update(
                project.project_id,
                total_lines=total_lines,
                total_chapters=total_chapters
            )
            if updated_project:
                project = updated_project
                logger.info(f"更新项目统计: {total_lines} 行, {total_chapters} 章")
        
        return project
    
    @classmethod
    def get(cls, project_id: str) -> Optional[Project]:
        """
        根据 ID 获取项目。
        
        :param project_id: 项目 ID
        :return: 项目对象，如果不存在则返回 None
        """
        with DatabaseSession() as db:
            project = db.get(Project, project_id)
            if project:
                db.expunge(project)  # 分离对象
                logger.debug(f"获取项目: {project_id}")
            else:
                logger.warning(f"项目不存在: {project_id}")
            return project
    
    @classmethod
    def list(cls, limit: Optional[int] = None, offset: int = 0) -> list[Project]:
        """
        获取项目列表。
        
        :param limit: 返回数量限制（None 表示无限制）
        :param offset: 跳过的记录数
        :return: 项目列表
        """
        with DatabaseSession() as db:
            statement = select(Project).offset(offset)
            if limit is not None:
                statement = statement.limit(limit)
            
            projects = db.exec(statement).all()
            # 分离所有对象
            for project in projects:
                db.expunge(project)
            logger.debug(f"获取项目列表: {len(projects)} 条")
            return list(projects)
    
    @classmethod
    def update(cls, project_id: str, **kwargs) -> Optional[Project]:
        """
        更新项目。
        
        :param project_id: 项目 ID
        :param kwargs: 要更新的字段
        :return: 更新后的项目对象，如果不存在则返回 None
        """
        with DatabaseSession() as db:
            project = db.get(Project, project_id)
            if not project:
                logger.warning(f"项目不存在，无法更新: {project_id}")
                return None
            
            # 更新字段
            for key, value in kwargs.items():
                if hasattr(project, key):
                    setattr(project, key, value)
            
            db.add(project)
            db.flush()
            db.refresh(project)
            db.expunge(project)  # 分离对象
            logger.info(f"更新项目: {project_id}")
            return project
    
    @classmethod
    def delete(cls, project_id: str) -> bool:
        """
        删除项目。
        
        同时删除所有关联数据：
        - 小说内容 (NovelContent)
        - 角色 (Actor)
        - 记忆条目 (MemoryEntry)
        - 聊天消息 (ChatMessage)
        - 聊天摘要 (ChatSummary)
        - 章节摘要 (ChapterSummary)
        
        :param project_id: 项目 ID
        :return: 是否删除成功
        """
        # 删除关联的小说内容
        from .novel_service import NovelContentService
        novel_count = NovelContentService.delete_by_session(project_id)
        logger.info(f"删除项目关联的小说内容: {project_id}, 共 {novel_count} 行")
        
        # 删除关联的角色
        from .actor_service import ActorService
        actors = ActorService.list_by_session(project_id)
        actor_count = 0
        for actor in actors:
            if ActorService.delete(actor.actor_id):
                actor_count += 1
        logger.info(f"删除项目关联的角色: {project_id}, 共 {actor_count} 个")
        
        # 删除关联的记忆条目
        from .memory_service import MemoryService
        memory_count = MemoryService.clear(project_id)
        logger.info(f"删除项目关联的记忆条目: {project_id}, 共 {memory_count} 条")
        
        # 删除关联的聊天消息
        from .history_service import HistoryService
        chat_count = HistoryService.clear(project_id)
        logger.info(f"删除项目关联的聊天消息: {project_id}, 共 {chat_count} 条")
        
        # 删除聊天摘要
        from api.schemas.memory import ChatSummary
        with DatabaseSession() as db:
            summary = db.get(ChatSummary, project_id)
            if summary:
                db.delete(summary)
                logger.info(f"删除项目关联的聊天摘要: {project_id}")
        
        # 删除章节摘要
        from .summary_service import SummaryService
        chapter_summary_count = SummaryService.clear(project_id)
        logger.info(f"删除项目关联的章节摘要: {project_id}, 共 {chapter_summary_count} 条")
        
        # 删除项目记录
        with DatabaseSession() as db:
            project = db.get(Project, project_id)
            if not project:
                logger.warning(f"项目不存在，无法删除: {project_id}")
                return False
            
            db.delete(project)
            logger.info(f"删除项目: {project_id}")
            return True

