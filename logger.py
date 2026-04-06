"""
日志管理模块
提供统一的日志记录功能
"""
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional


class Logger:
    """
    日志管理类
    支持控制台和文件日志
    """
    
    LEVELS = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR,
        'CRITICAL': logging.CRITICAL
    }
    
    def __init__(
        self,
        name: str = 'WebShellManager',
        log_file: Optional[str] = None,
        level: str = 'INFO'
    ):
        """
        初始化日志器
        
        Args:
            name: 日志器名称
            log_file: 日志文件路径（可选）
            level: 日志级别
        """
        self._logger = logging.getLogger(name)
        
        # 设置日志级别
        log_level = self.LEVELS.get(level.upper(), logging.INFO)
        self._logger.setLevel(log_level)
        
        # 避免重复添加handler
        if not self._logger.handlers:
            self._setup_handlers(log_file)
    
    def _setup_handlers(self, log_file: Optional[str]) -> None:
        """
        设置日志处理器
        
        Args:
            log_file: 日志文件路径
        """
        # 控制台处理器
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_format = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        )
        console_handler.setFormatter(console_format)
        self._logger.addHandler(console_handler)
        
        # 文件处理器
        if log_file:
            # 确保日志目录存在
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            file_handler = logging.FileHandler(
                log_file,
                encoding='utf-8'
            )
            file_handler.setLevel(logging.DEBUG)
            file_format = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            file_handler.setFormatter(file_format)
            self._logger.addHandler(file_handler)
    
    def debug(self, msg: str) -> None:
        """记录DEBUG级别日志"""
        self._logger.debug(msg)
    
    def info(self, msg: str) -> None:
        """记录INFO级别日志"""
        self._logger.info(msg)
    
    def warning(self, msg: str) -> None:
        """记录WARNING级别日志"""
        self._logger.warning(msg)
    
    def error(self, msg: str) -> None:
        """记录ERROR级别日志"""
        self._logger.error(msg)
    
    def critical(self, msg: str) -> None:
        """记录CRITICAL级别日志"""
        self._logger.critical(msg)
    
    def success(self, msg: str) -> None:
        """记录成功消息"""
        self._logger.info(f'[✓] {msg}')
    
    def fail(self, msg: str) -> None:
        """记录失败消息"""
        self._logger.error(f'[✗] {msg}')
    
    def set_level(self, level: str) -> None:
        """
        设置日志级别
        
        Args:
            level: 日志级别字符串
        """
        log_level = self.LEVELS.get(level.upper(), logging.INFO)
        self._logger.setLevel(log_level)
    
    @property
    def level(self) -> str:
        """获取当前日志级别"""
        return logging.getLevelName(self._logger.level)
