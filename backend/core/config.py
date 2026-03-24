#!/usr/bin/env python3
"""
配置管理模块
负责加载和管理应用配置，包括 API Key 和准点率服务配置
优先级：环境变量 > config.local.json > config.json
"""

import os
import json
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class Config:
    """配置管理类"""

    def __init__(self, config_dir: Optional[str] = None):
        """
        初始化配置管理器

        Args:
            config_dir: 配置文件目录，默认为 backend 目录
        """
        if config_dir is None:
            # 默认配置目录为 backend/
            config_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        self.config_dir = config_dir
        self.config_data = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """
        加载配置文件
        优先级：config.local.json > config.json

        Returns:
            配置字典
        """
        config = {}

        # 尝试加载 config.json
        config_path = os.path.join(self.config_dir, 'config.json')
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                logger.info(f"已加载配置文件: {config_path}")
            except Exception as e:
                logger.warning(f"加载配置文件失败 {config_path}: {e}")

        # 尝试加载 config.local.json（覆盖 config.json）
        local_config_path = os.path.join(self.config_dir, 'config.local.json')
        if os.path.exists(local_config_path):
            try:
                with open(local_config_path, 'r', encoding='utf-8') as f:
                    local_config = json.load(f)
                # 深度合并配置
                config = self._merge_config(config, local_config)
                logger.info(f"已加载本地配置文件: {local_config_path}")
            except Exception as e:
                logger.warning(f"加载本地配置文件失败 {local_config_path}: {e}")

        return config

    def _merge_config(self, base: Dict, override: Dict) -> Dict:
        """
        深度合并两个配置字典

        Args:
            base: 基础配置
            override: 覆盖配置

        Returns:
            合并后的配置
        """
        result = base.copy()
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_config(result[key], value)
            else:
                result[key] = value
        return result

    def get_api_key(self, region: str) -> Optional[str]:
        """
        获取指定地区的 API Key
        优先从环境变量读取，其次从配置文件

        Args:
            region: 地区代码（sf, nyc, sydney）

        Returns:
            API Key 或 None
        """
        # 环境变量映射
        env_var_map = {
            'sf': 'SF_511_API_KEY',
            'nyc': 'MTA_API_KEY',
            'sydney': 'TFNSW_API_KEY',
        }

        # 优先从环境变量读取
        env_var = env_var_map.get(region)
        if env_var:
            api_key = os.getenv(env_var)
            if api_key:
                logger.debug(f"从环境变量 {env_var} 读取 API Key")
                return api_key

        # 从配置文件读取
        api_keys = self.config_data.get('api_keys', {})
        api_key = api_keys.get(region)
        if api_key:
            logger.debug(f"从配置文件读取 {region} 的 API Key")
            return api_key

        logger.warning(f"未找到 {region} 的 API Key")
        return None

    def get_punctuality_config(self) -> Dict[str, Any]:
        """
        获取准点率服务配置

        Returns:
            准点率配置字典
        """
        default_config = {
            'fallback_to_mock': True,
            'collection_interval_minutes': 2,
            'retry_attempts': 3,
            'retry_delay_seconds': 5,
        }

        punctuality_config = self.config_data.get('punctuality', {})
        # 合并默认配置
        return {**default_config, **punctuality_config}

    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置项

        Args:
            key: 配置键（支持点号分隔的嵌套键，如 'punctuality.retry_attempts'）
            default: 默认值

        Returns:
            配置值
        """
        keys = key.split('.')
        value = self.config_data

        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default

        return value if value is not None else default


# 全局配置实例（单例模式）
_config_instance = None


def get_config() -> Config:
    """
    获取全局配置实例

    Returns:
        Config 实例
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = Config()
    return _config_instance
