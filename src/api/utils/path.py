"""
应用数据路径。
"""
import os
from pathlib import Path


app_data_path = Path(__file__).parent.parent.parent.parent / 'storage' / 'data'


app_temp_path = Path(__file__).parent.parent.parent.parent / 'storage' / 'temp'

model_meta_home = app_data_path / 'model_meta'
checkpoint_meta_home = model_meta_home / 'checkpoint'
lora_meta_home = model_meta_home / 'lora'
project_home = app_data_path / 'projects'
database_path = app_data_path / 'database.db'

# 任务图像缓存目录
jobs_home = app_temp_path / 'jobs'

# 创建必要的目录
checkpoint_meta_home.mkdir(parents=True, exist_ok=True)
lora_meta_home.mkdir(parents=True, exist_ok=True)
project_home.mkdir(parents=True, exist_ok=True)
jobs_home.mkdir(parents=True, exist_ok=True)
