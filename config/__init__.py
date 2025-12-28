"""
配置模块
"""
from .settings import (
    BASE_DIR,
    FACEBOOK_URL,
    DEFAULT_THREAD_COUNT,
    BROWSER_CONFIG,
    LOG_DIR,
    ConfigManager
)

__all__ = [
    'BASE_DIR',
    'FACEBOOK_URL',
    'DEFAULT_THREAD_COUNT',
    'BROWSER_CONFIG',
    'LOG_DIR',
    'ConfigManager'
]