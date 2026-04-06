"""
WebShell Manager - 命令行WebShell管理工具
适合AI使用的CTF WebShell管理工具
"""

__version__ = '1.0.0'
__author__ = 'WebShell Manager'

from .webshell import WebShellManager, WebShell, PHPWebShell, JSPWebShell, ASPWebShell
from .operations import FileOperations, SystemOperations, PrivilegeEscalation
from .database import DatabaseManager, MySQLOperations, SQLiteOperations
from .config import Config
from .logger import Logger
from .cli import CLI

__all__ = [
    'WebShellManager',
    'WebShell', 
    'PHPWebShell',
    'JSPWebShell',
    'ASPWebShell',
    'FileOperations',
    'SystemOperations',
    'PrivilegeEscalation',
    'DatabaseManager',
    'MySQLOperations',
    'SQLiteOperations',
    'Config',
    'Logger',
    'CLI',
]
