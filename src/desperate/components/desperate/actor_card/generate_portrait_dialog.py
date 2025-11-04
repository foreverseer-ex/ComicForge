"""
生成立绘参数对话框。

用于输入绘图参数并生成立绘。
"""
import flet as ft
from loguru import logger
from flet_toast import flet_toast
from flet_toast.Types import Position
import httpx

from api.services.draw.sd_forge import SdForgeDrawService
from api.settings import app_settings


class GeneratePortraitDialog(ft.AlertDialog):
    """生成立绘参数对话框类。"""
    
    def __init__(self, actor_name: str, project_id: str, actor_id: str, on_generate: callable, on_error: callable):
        """
        初始化生成立绘参数对话框。
        
        Args:
            actor_name: Actor 名称（用于显示）
            project_id: 项目ID
            actor_id: Actor ID
            on_generate: 生成回调函数，接收参数 (title, desc, model, prompt, negative_prompt, 
                       sampler_name, steps, cfg_scale, width, height, seed, clip_skip, vae)
            on_error: 错误回调函数，接收参数 (message: str)
        """
        super().__init__()
        self.actor_name = actor_name
        self.project_id = project_id
        self.actor_id = actor_id
        self.on_generate = on_generate
        self.on_error = on_error
        
        # 配置对话框属性
        self.modal = True
        self.width = 600
        self.height = 700
        
        # 创建输入字段
        self.title_field = ft.TextField(
            label="立绘标题",
            hint_text="如：立绘-2024",
            value="立绘",
            autofocus=True,
        )
        
        self.desc_field = ft.TextField(
            label="立绘说明",
            hint_text="可选，用于描述这个立绘的特点",
            multiline=True,
            min_lines=2,
            max_lines=3,
        )
        
        # 模型下拉框（异步加载）
        self.model_dropdown = ft.Dropdown(
            label="模型",
            hint_text="选择 SD 模型",
            options=[],
            width=300,
        )
        
        self.prompt_field = ft.TextField(
            label="正向提示词",
            hint_text="可选，不填则自动从 Actor 信息生成",
            multiline=True,
            min_lines=3,
            max_lines=5,
        )
        
        self.negative_prompt_field = ft.TextField(
            label="负向提示词",
            value="worst quality, lowres, bad anatomy, extra fingers, deformed, blurry",
            multiline=True,
            min_lines=2,
            max_lines=3,
        )
        
        self.sampler_dropdown = ft.Dropdown(
            label="采样器",
            value="DPM++ 2M Karras",
            options=[
                ft.dropdown.Option("DPM++ 2M Karras"),
                ft.dropdown.Option("DPM++ SDE Karras"),
                ft.dropdown.Option("Euler a"),
                ft.dropdown.Option("Euler"),
                ft.dropdown.Option("LMS"),
                ft.dropdown.Option("Heun"),
                ft.dropdown.Option("DPM2"),
                ft.dropdown.Option("DPM2 a"),
                ft.dropdown.Option("DPM++ 2S a"),
                ft.dropdown.Option("DPM++ 2M"),
                ft.dropdown.Option("DPM++ SDE"),
                ft.dropdown.Option("DPM fast"),
                ft.dropdown.Option("DPM adaptive"),
                ft.dropdown.Option("LMS Karras"),
                ft.dropdown.Option("DPM2 Karras"),
                ft.dropdown.Option("DPM2 a Karras"),
                ft.dropdown.Option("DPM++ 2S a Karras"),
            ],
            width=200,
        )
        
        self.steps_field = ft.TextField(
            label="采样步数",
            value="30",
            keyboard_type=ft.KeyboardType.NUMBER,
            width=150,
        )
        
        self.cfg_scale_field = ft.TextField(
            label="CFG Scale",
            value="7.0",
            keyboard_type=ft.KeyboardType.NUMBER,
            width=150,
        )
        
        self.width_field = ft.TextField(
            label="宽度",
            value="1024",
            keyboard_type=ft.KeyboardType.NUMBER,
            width=150,
        )
        
        self.height_field = ft.TextField(
            label="高度",
            value="1024",
            keyboard_type=ft.KeyboardType.NUMBER,
            width=150,
        )
        
        self.seed_field = ft.TextField(
            label="随机种子",
            value="-1",
            hint_text="-1 表示随机",
            keyboard_type=ft.KeyboardType.NUMBER,
            width=150,
        )
        
        self.clip_skip_field = ft.TextField(
            label="CLIP Skip",
            hint_text="可选，留空使用默认值",
            keyboard_type=ft.KeyboardType.NUMBER,
            width=150,
        )
        
        self.vae_field = ft.TextField(
            label="VAE",
            hint_text="可选，留空使用默认值",
            width=200,
        )
        
        # LoRA 选择区域
        self.lora_container = ft.Container(
            content=ft.Column([
                ft.Text("LoRA 设置", size=14, weight=ft.FontWeight.BOLD),
                ft.Text("点击 + 添加 LoRA", size=12, color=ft.Colors.GREY_600),
            ], tight=True, spacing=5),
        )
        
        # LoRA 列表（动态添加）
        self.lora_rows = ft.Column([], spacing=5)
        
        # 添加 LoRA 按钮
        self.add_lora_button = ft.ElevatedButton(
            text="+ 添加 LoRA",
            icon=ft.Icons.ADD,
            on_click=self._add_lora_row,
            width=150,
        )
        
        # LoRA 下拉框选项（异步加载）
        self.lora_options = []
        
        # 加载状态指示器
        self.loading_indicator = ft.ProgressRing(visible=False, width=20, height=20)
        
        super().__init__(
            modal=True,
            title=ft.Text(f"为 {actor_name} 生成立绘", size=18, weight=ft.FontWeight.BOLD),
            content=ft.Column([
                ft.Row([
                    self.model_dropdown,
                    self.loading_indicator,
                ], spacing=10),
                self.title_field,
                self.desc_field,
                self.prompt_field,
                self.negative_prompt_field,
                ft.Row([
                    self.sampler_dropdown,
                    self.steps_field,
                    self.cfg_scale_field,
                ], spacing=10),
                ft.Row([
                    self.width_field,
                    self.height_field,
                    self.seed_field,
                ], spacing=10),
                ft.Row([
                    self.clip_skip_field,
                    self.vae_field,
                ], spacing=10),
                ft.Divider(),
                ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Text("LoRA 设置", size=14, weight=ft.FontWeight.BOLD),
                            self.add_lora_button,
                        ], spacing=10),
                        self.lora_rows,
                    ], tight=True, spacing=5),
                ),
            ], tight=True, spacing=10, width=580, scroll=ft.ScrollMode.AUTO),
            actions=[
                ft.TextButton("取消", on_click=self._on_cancel),
                ft.ElevatedButton("生成", on_click=self._on_confirm),
            ],
        )
        
        # 异步加载模型列表（在对话框打开后）
        # 通过重写 did_mount 或在打开时触发
    
    def did_mount(self):
        """组件挂载后加载模型列表和 LoRA 列表"""
        if self.page:
            self.page.run_task(self._load_models_and_loras)
    
    def _check_model_file_exists(self, model_name: str, model_filename: str = None) -> bool:
        """检查模型文件是否在本地存在（仅对 sd-forge 后端有效）"""
        # 如果是 civitai 后端，总是返回 True（civitai 后端总是有模型）
        if app_settings.draw.backend == "civitai":
            return True
        
        # 对于 sd-forge 后端，检查文件是否存在
        checkpoint_home = app_settings.sd_forge.checkpoint_home
        
        # 优先使用 filename（如果提供）
        if model_filename:
            checkpoint_path = checkpoint_home / model_filename
            if checkpoint_path.exists():
                logger.debug(f"找到模型文件（通过 filename）: {checkpoint_path}")
                return True
        
        # 如果 filename 不存在，尝试使用 model_name（title）
        # 尝试多种可能的文件名格式
        possible_names = [
            model_name,  # 直接使用名称
            f"{model_name}.safetensors",  # 添加扩展名
            f"{model_name}.ckpt",  # 可能是 ckpt 格式
        ]
        
        for name in possible_names:
            checkpoint_path = checkpoint_home / name
            if checkpoint_path.exists():
                logger.debug(f"找到模型文件（通过 title）: {checkpoint_path}")
                return True
        
        logger.debug(f"模型文件不存在: {model_name} (在 {checkpoint_home})")
        return False
    
    def _check_lora_file_exists(self, lora_name: str) -> bool:
        """检查 LoRA 文件是否在本地存在（仅对 sd-forge 后端有效）"""
        # 如果是 civitai 后端，总是返回 True（civitai 后端总是有模型）
        if app_settings.draw.backend == "civitai":
            return True
        
        # 对于 sd-forge 后端，检查文件是否存在
        # SD-Forge API 返回的 LoRA 名称，需要检查对应的 .safetensors 文件
        lora_path = app_settings.sd_forge.lora_home / f"{lora_name}.safetensors"
        return lora_path.exists()
    
    async def _load_models_and_loras(self):
        """异步加载模型列表和 LoRA 列表。"""
        try:
            self.loading_indicator.visible = True
            if self.page:
                self.page.update()
            
            logger.info(f"开始加载模型列表（后端: {app_settings.draw.backend}）")
            
            # 调用服务获取模型列表
            models_data = SdForgeDrawService._get_sd_models()
            
            logger.debug(f"模型数据: {models_data}")
            logger.debug(f"模型数据类型: {type(models_data)}")
            
            # 解析模型列表
            if isinstance(models_data, list):
                model_options = []
                logger.info(f"接收到 {len(models_data)} 个模型")
                
                for model in models_data:
                    # 尝试多种可能的字段名
                    model_title = (
                        model.get("title") or 
                        model.get("model_name") or
                        model.get("name") or
                        ""
                    )
                    
                    # 获取 filename（如果有）
                    model_filename = model.get("filename")
                    
                    if model_title:
                        logger.debug(f"处理模型: {model_title} (filename: {model_filename})")
                        
                        # 如果是 sd-forge 后端，检查文件是否存在
                        if app_settings.draw.backend == "sd_forge":
                            if not self._check_model_file_exists(model_title, model_filename):
                                logger.debug(f"跳过本地不存在的模型: {model_title}")
                                continue
                        
                        model_options.append(ft.dropdown.Option(key=model_title, text=model_title))
                        logger.debug(f"添加模型选项: {model_title}")
                    else:
                        logger.warning(f"无法解析模型项: {model}")
                
                logger.info(f"共加载 {len(model_options)} 个可用模型")
                
                self.model_dropdown.options = model_options
                
                # 如果有模型，默认选择第一个
                if model_options:
                    self.model_dropdown.value = model_options[0].key
                    logger.info(f"默认选择模型: {model_options[0].key}")
                else:
                    logger.warning("没有可用的模型")
                    if self.on_error:
                        self.on_error("⚠️ 没有找到可用的模型（可能是文件不存在或 API 返回为空）")
            else:
                logger.warning(f"模型列表格式异常: {type(models_data)}, 数据: {models_data}")
                if self.on_error:
                    self.on_error(f"获取模型列表失败：返回格式异常（期望列表，实际是 {type(models_data).__name__}）")
            
            # 调用服务获取 LoRA 列表
            loras_data = SdForgeDrawService._get_loras()
            
            logger.debug(f"LoRA 数据: {loras_data}")
            logger.debug(f"LoRA 数据类型: {type(loras_data)}")
            
            # 解析 LoRA 列表
            if isinstance(loras_data, list):
                lora_options = []
                for lora in loras_data:
                    # 尝试多种可能的字段名
                    lora_name = (
                        lora.get("name") or 
                        lora.get("title") or 
                        lora.get("model_name") or
                        (isinstance(lora, str) and lora) or
                        ""
                    )
                    if lora_name:
                        # 如果是 sd-forge 后端，检查文件是否存在
                        if app_settings.draw.backend == "sd_forge":
                            if not self._check_lora_file_exists(lora_name):
                                logger.debug(f"跳过本地不存在的 LoRA: {lora_name}")
                                continue
                        lora_options.append(ft.dropdown.Option(key=lora_name, text=lora_name))
                    else:
                        logger.warning(f"无法解析 LoRA 项: {lora}")
                
                self.lora_options = lora_options
                logger.info(f"已加载 {len(lora_options)} 个 LoRA 选项")
                
                if len(lora_options) == 0:
                    logger.warning("LoRA 列表为空")
            elif isinstance(loras_data, dict):
                # 如果返回的是字典，尝试不同的键
                logger.warning(f"LoRA 数据是字典格式: {loras_data.keys() if hasattr(loras_data, 'keys') else 'unknown'}")
                # 尝试从字典中提取列表
                if "items" in loras_data:
                    loras_list = loras_data["items"]
                elif "data" in loras_data:
                    loras_list = loras_data["data"]
                else:
                    loras_list = list(loras_data.values()) if loras_data else []
                
                lora_options = []
                for lora in loras_list:
                    lora_name = (
                        lora.get("name") if isinstance(lora, dict) else 
                        (isinstance(lora, str) and lora) or
                        str(lora)
                    )
                    if lora_name:
                        # 如果是 sd-forge 后端，检查文件是否存在
                        if app_settings.draw.backend == "sd_forge":
                            if not self._check_lora_file_exists(lora_name):
                                logger.debug(f"跳过本地不存在的 LoRA: {lora_name}")
                                continue
                        lora_options.append(ft.dropdown.Option(key=lora_name, text=lora_name))
                
                self.lora_options = lora_options
                logger.info(f"已加载 {len(lora_options)} 个 LoRA 选项（从字典格式）")
            else:
                logger.warning(f"LoRA 列表格式异常: {type(loras_data)}")
                self.lora_options = []
            
        except httpx.HTTPError as e:
            logger.exception(f"加载模型/LoRA 列表失败（HTTP 错误）: {e}")
            if self.on_error:
                self.on_error(f"❌ 连接 SD-Forge 失败: {str(e)}\n请检查 SD-Forge 服务是否运行")
        except Exception as e:
            logger.exception(f"加载模型/LoRA 列表失败: {e}")
            if self.on_error:
                self.on_error(f"获取列表失败: {str(e)}")
        finally:
            self.loading_indicator.visible = False
            if self.page:
                self.page.update()
    
    def _add_lora_row(self, e):
        """添加一个 LoRA 行"""
        # 检查 LoRA 选项是否已加载
        if not self.lora_options:
            logger.warning("LoRA 列表尚未加载，无法添加 LoRA 行")
            if self.on_error:
                self.on_error("⚠️ LoRA 列表正在加载中，请稍候...")
            return
        
        lora_dropdown = ft.Dropdown(
            label="LoRA",
            options=self.lora_options.copy(),
            width=250,
        )
        
        weight_field = ft.TextField(
            label="权重",
            value="1.0",
            hint_text="0.0-2.0",
            keyboard_type=ft.KeyboardType.NUMBER,
            width=100,
        )
        
        remove_button = ft.IconButton(
            icon=ft.Icons.DELETE,
            tooltip="删除",
            on_click=lambda _: self._remove_lora_row(lora_row),
        )
        
        lora_row = ft.Row(
            controls=[lora_dropdown, weight_field, remove_button],
            spacing=10,
        )
        
        # 保存引用以便删除
        lora_row.lora_dropdown = lora_dropdown
        lora_row.weight_field = weight_field
        
        self.lora_rows.controls.append(lora_row)
        logger.debug(f"已添加 LoRA 行，当前有 {len(self.lora_options)} 个选项")
        if self.page:
            self.page.update()
    
    def _remove_lora_row(self, lora_row):
        """删除一个 LoRA 行"""
        if lora_row in self.lora_rows.controls:
            self.lora_rows.controls.remove(lora_row)
            if self.page:
                self.page.update()
    
    def _on_confirm(self, e):
        """确认生成"""
        # 验证必填字段
        title = self.title_field.value.strip()
        if not title:
            if self.on_error:
                self.on_error("❌ 请输入立绘标题")
            return
        
        model = self.model_dropdown.value
        if not model:
            if self.on_error:
                self.on_error("❌ 请选择模型")
            return
        
        # 获取其他参数
        desc = self.desc_field.value.strip()
        prompt = self.prompt_field.value.strip()
        negative_prompt = self.negative_prompt_field.value.strip() or "worst quality, lowres, bad anatomy, extra fingers, deformed, blurry"
        sampler_name = self.sampler_dropdown.value or "DPM++ 2M Karras"
        
        # 解析数值参数
        try:
            steps = int(self.steps_field.value) if self.steps_field.value else 30
            cfg_scale = float(self.cfg_scale_field.value) if self.cfg_scale_field.value else 7.0
            width = int(self.width_field.value) if self.width_field.value else 1024
            height = int(self.height_field.value) if self.height_field.value else 1024
            seed = int(self.seed_field.value) if self.seed_field.value else -1
            clip_skip = int(self.clip_skip_field.value) if self.clip_skip_field.value else None
        except ValueError as ve:
            if self.on_error:
                self.on_error(f"❌ 参数格式错误: {ve}")
            return
        
        vae = self.vae_field.value.strip() if self.vae_field.value else None
        
        # 收集 LoRA 配置
        loras = {}
        for lora_row in self.lora_rows.controls:
            if hasattr(lora_row, 'lora_dropdown') and hasattr(lora_row, 'weight_field'):
                lora_name = lora_row.lora_dropdown.value
                weight_str = lora_row.weight_field.value
                if lora_name and weight_str:
                    try:
                        weight = float(weight_str)
                        if 0.0 <= weight <= 2.0:
                            loras[lora_name] = weight
                        else:
                            if self.on_error:
                                self.on_error(f"❌ LoRA 权重必须在 0.0-2.0 之间: {lora_name}")
                            return
                    except ValueError:
                        if self.on_error:
                            self.on_error(f"❌ LoRA 权重格式错误: {lora_name}")
                        return
        
        # 如果没有配置 LoRA，传递 None
        loras = loras if loras else None
        
        # 关闭对话框
        self.open = False
        if self.page:
            self.page.update()
        
        # 调用生成回调
        if self.on_generate:
            self.on_generate(
                title=title,
                desc=desc,
                model=model,
                prompt=prompt,
                negative_prompt=negative_prompt,
                sampler_name=sampler_name,
                steps=steps,
                cfg_scale=cfg_scale,
                width=width,
                height=height,
                seed=seed,
                clip_skip=clip_skip,
                vae=vae,
                loras=loras,
            )
    
    def _on_cancel(self, e):
        """取消生成"""
        self.open = False
        if self.page:
            self.page.update()

