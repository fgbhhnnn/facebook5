"""
配置文件模块
"""
import os
import json
from typing import List, Dict, Any

# 项目根目录
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Facebook URL
FACEBOOK_URL = "https://www.facebook.com"

# 默认线程数
DEFAULT_THREAD_COUNT = 1

# 浏览器配置
BROWSER_CONFIG = {
    'headless': False,
    'window_size': (1920, 1080),
    'page_load_timeout': 30,
    'implicit_wait': 10
}

# 日志配置
LOG_DIR = os.path.join(BASE_DIR, 'logs')
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

# 配置文件路径
CONFIG_FILE = os.path.join(BASE_DIR, 'config', 'app_config.json')


class ConfigManager:
    """配置管理器"""
    
    @staticmethod
    def save_config(thread_count: int, cookies: List[str]) -> bool:
        """
        保存配置到文件
        
        Args:
            thread_count: 线程数量
            cookies: Cookie列表
            
        Returns:
            是否保存成功
        """
        try:
            config = {
                'thread_count': thread_count,
                'cookies': cookies
            }
            
            # 确保配置目录存在
            os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
            
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            
            print(f"配置已保存到: {CONFIG_FILE}")
            return True
        except Exception as e:
            print(f"保存配置失败: {e}")
            return False
    
    @staticmethod
    def load_config() -> Dict[str, Any]:
        """
        从文件加载配置
        
        Returns:
            配置字典，包含thread_count和cookies
        """
        try:
            if not os.path.exists(CONFIG_FILE):
                return {'thread_count': DEFAULT_THREAD_COUNT, 'cookies': []}
            
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            print(f"配置已从 {CONFIG_FILE} 加载")
            return config
        except Exception as e:
            print(f"加载配置失败: {e}")
            return {'thread_count': DEFAULT_THREAD_COUNT, 'cookies': []}