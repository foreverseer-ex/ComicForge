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
chat_history_home = app_data_path / 'chat_history'
project_home = app_data_path / 'projects'
database_path = app_data_path / 'database.db'
checkpoint_meta_home.mkdir(parents=True, exist_ok=True)
lora_meta_home.mkdir(parents=True, exist_ok=True)
chat_history_home.mkdir(parents=True, exist_ok=True)
project_home.mkdir(parents=True, exist_ok=True)
