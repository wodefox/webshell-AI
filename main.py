#!/usr/bin/env python3
"""
WebShell Manager - 主入口
命令行WebShell管理工具，适合AI使用
"""
import sys
import click

try:
    from .cli import CLI
    from .config import Config
    from .logger import Logger
except ImportError:
    from cli import CLI
    from config import Config
    from logger import Logger


@click.group()
@click.version_option(version='1.0.0', prog_name='webshell-manager')
def cli():
    """WebShell Manager - 命令行WebShell管理工具"""
    pass


@cli.command()
def interactive():
    """启动交互式CLI界面"""
    try:
        cli_instance = CLI()
        cli_instance.run()
    except KeyboardInterrupt:
        print("\n再见！")
        sys.exit(0)


@cli.command()
@click.option('--url', required=True, help='WebShell URL')
@click.option('--password', required=True, help='WebShell密码')
@click.option('--type', 'shell_type', default='php-eval', 
              help='Shell类型: php-eval|php-assert|php-system|jsp|asp')
@click.option('--command', help='要执行的命令')
def connect(url, password, shell_type, command):
    """快速连接并执行命令"""
    try:
        from .webshell import WebShellManager
    except ImportError:
        from webshell import WebShellManager
    
    config = Config()
    logger = Logger()
    manager = WebShellManager(config, logger)
    
    if manager.connect('default', url, password, shell_type):
        shell = manager.get_shell('default')
        
        if command:
            success, result = shell.execute(command)
            if success:
                print(result)
            else:
                print(f"错误: {result}", file=sys.stderr)
        else:
            # 进入交互模式
            try:
                from .operations import FileOperations
            except ImportError:
                from operations import FileOperations
            file_ops = FileOperations(shell, logger)
            
            print(f"已连接到 {url}")
            print("输入命令执行，输入 'exit' 退出")
            
            while True:
                try:
                    cmd = input(f"{url}> ").strip()
                    if not cmd:
                        continue
                    if cmd.lower() == 'exit':
                        break
                    
                    success, result = shell.execute(cmd)
                    print(result if success else f"错误: {result}")
                except KeyboardInterrupt:
                    print("\n使用 'exit' 退出")
                except EOFError:
                    break


@cli.command()
@click.option('--url', required=True, help='WebShell URL')
@click.option('--password', required=True, help='WebShell密码')
@click.option('--remote', required=True, help='远程文件路径')
@click.option('--local', required=True, help='本地文件路径')
def download(url, password, remote, local):
    """下载文件"""
    try:
        from .webshell import WebShellManager
        from .operations import FileOperations
    except ImportError:
        from webshell import WebShellManager
        from operations import FileOperations
    
    config = Config()
    logger = Logger()
    manager = WebShellManager(config, logger)
    
    if manager.connect('default', url, password):
        shell = manager.get_shell('default')
        file_ops = FileOperations(shell, logger)
        
        if file_ops.download(remote, local):
            print(f"文件已下载到 {local}")
        else:
            print("下载失败", file=sys.stderr)


@cli.command()
@click.option('--url', required=True, help='WebShell URL')
@click.option('--password', required=True, help='WebShell密码')
@click.option('--local', required=True, help='本地文件路径')
@click.option('--remote', required=True, help='远程文件路径')
def upload(url, password, local, remote):
    """上传文件"""
    try:
        from .webshell import WebShellManager
        from .operations import FileOperations
    except ImportError:
        from webshell import WebShellManager
        from operations import FileOperations
    
    config = Config()
    logger = Logger()
    manager = WebShellManager(config, logger)
    
    if manager.connect('default', url, password):
        shell = manager.get_shell('default')
        file_ops = FileOperations(shell, logger)
        
        if file_ops.upload(local, remote):
            print(f"文件已上传到 {remote}")
        else:
            print("上传失败", file=sys.stderr)


def main():
    """主函数"""
    # 如果没有参数，直接启动交互模式
    if len(sys.argv) == 1:
        cli_instance = CLI()
        cli_instance.run()
    else:
        cli()


if __name__ == '__main__':
    main()
