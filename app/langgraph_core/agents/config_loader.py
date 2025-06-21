import yaml
import os
from typing import Dict, Any

def load_workers_config() -> Dict[str, Any]:
    """加载并解析 workers_config.yaml 文件"""
    config_path = os.path.join(os.path.dirname(__file__), "workers_config.yaml")
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Worker configuration file not found at: {config_path}")
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

# 创建一个全局配置变量，让整个应用在启动时只加载一次配置
# 这使得其他模块可以简单地从这里导入 WORKERS_CONFIG
try:
    WORKERS_CONFIG = load_workers_config()
except Exception as e:
    # 在加载配置失败时提供清晰的错误信息
    print(f"FATAL: Failed to load workers_config.yaml. Error: {e}")
    # 在实际应用中，你可能希望在这里让程序退出
    WORKERS_CONFIG = {"workers": [], "tools": {}} 