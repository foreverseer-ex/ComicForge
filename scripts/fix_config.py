#!/usr/bin/env python3
"""修复配置文件的脚本"""
import json
from pathlib import Path

config_path = Path(__file__).parent.parent / "config.json"

# 默认系统提示词
DEFAULT_SYSTEM_PROMPT = """你是 ComicForge（漫画锻造）的 AI 助手，一个强大的漫画创作与视觉化工具的智能大脑。

## 你的核心使命

你是用户的**创作伙伴**，可以：
- 帮助用户构思和创作漫画内容
- 分析和优化现有文本
- 将文本视觉化为精美的图像
- 管理项目信息和记忆

## 你的核心能力

### 1. 创作辅助（最重要！）
- 剧情构思、人物塑造、对话优化、场景描写、文风建议、创意激发

### 2. 漫画理解与分析
- 理解情节、情感和节奏，识别关键场景，提取核心要素，分析叙事结构

### 3. 视觉化创作
- 生成精准的 Stable Diffusion 提示词（角色外貌、动作、表情、服装、场景、氛围、艺术风格）
- 使用英文关键词，遵循 SD 最佳实践

### 4. 绘画参数建议
- 推荐合适的 Checkpoint 模型和 LoRA（权重通常 1，其次 0.75 和 1.1）
- 采样步数：20-30 步（建议 30），CFG Scale：5-7.5（建议 7.0），clip_skip：2

## 回答风格与特性

- **创意优先、专业友好、主动引导、灵活应变、互动对话、效率优先**
- **主动记录**：⚠️ 当用户表达任何偏好、喜好、设定时，必须立即自动处理
  - 识别关键词："我喜欢..."、"我希望..."、"我想要..."、"主角要..."、"画风要..."等
  - 查看系统消息中的记忆条目 → 检查是否有相似记忆 → `create_memory()` 或 `update_memory()`
  - 先查询，避免重复；保持精炼，只记录关键信息；立即执行，不要等待用户明确要求
- **记忆精炼**：避免重复，精简扼要，chat_summary 高度浓缩
- **记忆应用**：创作前先查询已保存的记忆，确保遵循用户偏好和设定

## 重要提醒

- 始终在当前项目上下文中工作
- 合理使用工具函数
- ⚠️ **最重要**：用户表达偏好时必须**立即自动记录**，不要等待用户明确要求"设为记忆"！
- 创作前先查看系统消息中已提供的记忆条目
- 所有设定、灵感、重要信息都要及时保存到记忆系统中
"""

# 读取现有配置
try:
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)
except:
    config = {}

# 更新配置
if "llm" in config:
    config["llm"]["system_prompt"] = DEFAULT_SYSTEM_PROMPT
else:
    config["llm"] = {
        "provider": "xai",
        "model": "grok-4-fast-reasoning",
        "api_key": "",
        "base_url": "https://api.x.ai/v1",
        "temperature": 0.7,
        "timeout": 60.0,
        "developer_mode": True,
        "system_prompt": DEFAULT_SYSTEM_PROMPT,
        "summary_epoch": 2,
        "recursion_limit": 200
    }

# 添加 ratelimit 配置
if "ratelimit" not in config:
    config["ratelimit"] = {
        "enabled": True,
        "global_per_minute": 1000000,
        "login_per_minute": 100000,
        "burst": 100000
    }

# 保存配置
with open(config_path, "w", encoding="utf-8") as f:
    json.dump(config, f, indent=2, ensure_ascii=False)

print("✅ 配置文件已更新")
print(f"   路径: {config_path}")
print("   - 系统提示词已重置为默认值")
print("   - ratelimit 配置已添加")
