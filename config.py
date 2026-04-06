"""
配置管理模块
提供配置加载、保存和管理功能
"""
import os
from pathlib import Path
from typing import Any, Dict, Optional

import yaml


class ConfigError(Exception):
    """配置异常"""
    pass


class Config:
    """
    配置管理类
    支持YAML配置文件和默认配置
    """
    
    DEFAULT_CONFIG = {
        'timeout': 10,
        'retry_times': 3,
        'proxy': None,
        'headers': {
            'User-Agent': (
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/91.0.4472.124 Safari/537.36'
            )
        },
        'encoding': 'utf-8',
        'log_level': 'INFO',
        'log_file': 'webshell_manager.log'
    }
    
    def __init__(self, config_file: Optional[str] = None):
        """
        初始化配置
        
        Args:
            config_file: 配置文件路径（可选）
        """
        self._config_file = config_file or 'config.yaml'
        self._config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """
        加载配置文件
        
        Returns:
            Dict[str, Any]: 配置字典
        """
        config = self.DEFAULT_CONFIG.copy()
        
        if os.path.exists(self._config_file):
            try:
                with open(self._config_file, 'r', encoding='utf-8') as f:
                    user_config = yaml.safe_load(f) or {}
                    config = self._merge_config(config, user_config)
            except Exception as e:
                raise ConfigError(f"Failed to load config: {e}")
        
        return config
    
    @staticmethod
    def _merge_config(
        base: Dict[str, Any],
        override: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        合并配置（深度合并）
        
        Args:
            base: 基础配置
            override: 覆盖配置
            
        Returns:
            Dict[str, Any]: 合并后的配置
        """
        result = base.copy()
        
        for key, value in override.items():
            if (
                key in result
                and isinstance(result[key], dict)
                and isinstance(value, dict)
            ):
                result[key] = Config._merge_config(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def save(self) -> None:
        """保存配置到文件"""
        try:
            with open(self._config_file, 'w', encoding='utf-8') as f:
                yaml.dump(
                    self._config,
                    f,
                    default_flow_style=False,
                    allow_unicode=True
                )
        except Exception as e:
            raise ConfigError(f"Failed to save config: {e}")
    
    def get(
        self,
        key: str,
        default: Optional[Any] = None
    ) -> Any:
        """
        获取配置项
        
        Args:
            key: 配置键（支持点号分隔的嵌套键）
            default: 默认值
            
        Returns:
            Any: 配置值
        """
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
            
            if value is None:
                return default
        
        return value
    
    def set(self, key: str, value: Any) -> None:
        """
        设置配置项
        
        Args:
            key: 配置键（支持点号分隔的嵌套键）
            value: 配置值
        """
        keys = key.split('.')
        config = self._config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
    
    def update(self, config_dict: Dict[str, Any]) -> None:
        """
        批量更新配置
        
        Args:
            config_dict: 配置字典
        """
        self._config = self._merge_config(self._config, config_dict)
    
    @property
    def config(self) -> Dict[str, Any]:
        """获取完整配置（只读）"""
        return self._config.copy()
    
    def __repr__(self) -> str:
        return f"Config({self._config})"
