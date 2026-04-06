"""
交互式CLI界面
使用prompt_toolkit实现友好的命令行交互
"""
import os
import sys
from typing import Optional, Dict, Any
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.styles import Style
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.syntax import Syntax
from rich import print as rprint

try:
    from .webshell import WebShellManager, WebShell
    from .operations import FileOperations, SystemOperations, PrivilegeEscalation
    from .database import DatabaseManager
    from .config import Config
    from .logger import Logger
except ImportError:
    from webshell import WebShellManager, WebShell
    from operations import FileOperations, SystemOperations, PrivilegeEscalation
    from database import DatabaseManager
    from config import Config
    from logger import Logger


class CLI:
    """命令行界面"""
    
    # 定义样式
    STYLE = Style.from_dict({
        'prompt': 'ansicyan bold',
    })
    
    # 命令补全
    COMMANDS = [
        # 连接管理
        'connect', 'disconnect', 'list', 'use',
        # 文件操作
        'pwd', 'ls', 'cd', 'cat', 'download', 'upload', 'edit', 'rm', 'mkdir', 'mv', 'cp', 'find', 'grep',
        # 系统操作
        'whoami', 'id', 'uname', 'ps', 'netstat', 'ifconfig', 'env', 'kill',
        # 提权辅助
        'suid', 'sgid', 'writable', 'cron', 'kernel',
        # 数据库操作
        'db-connect', 'db-list', 'db-query', 'db-tables', 'db-dump',
        # 其他
        'exec', 'help', 'exit', 'clear', 'config',
    ]
    
    def __init__(self):
        self.console = Console()
        self.config = Config()
        self.logger = Logger(
            log_file=self.config.get('log_file'),
            level=self.config.get('log_level')
        )
        self.manager = WebShellManager(self.config, self.logger)
        self.db_manager: Optional[DatabaseManager] = None
        self.current_shell: Optional[WebShell] = None
        self.current_name: Optional[str] = None
        self.file_ops: Optional[FileOperations] = None
        self.sys_ops: Optional[SystemOperations] = None
        self.priv_ops: Optional[PrivilegeEscalation] = None
        
        # 创建历史文件目录
        history_dir = os.path.expanduser('~/.webshell_manager')
        os.makedirs(history_dir, exist_ok=True)
        self.history_file = os.path.join(history_dir, 'history')
        
        # 创建session
        self.session = PromptSession(
            history=FileHistory(self.history_file),
            auto_suggest=AutoSuggestFromHistory(),
            completer=WordCompleter(self.COMMANDS),
            style=self.STYLE,
        )
    
    def get_prompt(self) -> str:
        """获取提示符"""
        if self.current_name:
            return f'{self.current_name}> '
        return 'webshell> '
    
    def print_help(self):
        """打印帮助信息"""
        help_text = """
[bold cyan]WebShell Manager - 命令行WebShell管理工具[/bold cyan]

[bold yellow]连接管理:[/bold yellow]
  connect <name> <url> <password> [type]  连接WebShell
                                          type: php-eval|php-assert|php-system|jsp|asp
  disconnect <name>                      断开连接
  list                                   列出所有连接
  use <name>                             切换当前连接

[bold yellow]文件操作:[/bold yellow]
  pwd                                    显示当前目录
  ls [path]                              列出目录内容
  cd <path>                              切换目录
  cat <file>                             查看文件内容
  download <remote> <local>              下载文件
  upload <local> <remote>                上传文件
  edit <file>                            编辑文件
  rm <path>                              删除文件/目录
  mkdir <path>                           创建目录
  mv <src> <dst>                         移动/重命名
  cp <src> <dst>                         复制文件
  find <path> [name]                     查找文件
  grep <pattern> <path>                  搜索文件内容

[bold yellow]系统操作:[/bold yellow]
  whoami                                 当前用户
  id                                     用户ID信息
  uname                                  系统信息
  ps                                     进程列表
  netstat                                网络连接
  ifconfig                               网络接口
  env                                    环境变量
  kill <pid>                             杀死进程

[bold yellow]提权辅助:[/bold yellow]
  suid                                   查找SUID文件
  sgid                                   查找SGID文件
  writable                               查找可写目录
  cron                                   查看cron任务
  kernel                                 查看内核版本

[bold yellow]数据库操作:[/bold yellow]
  db-connect <name> <type> <params>      连接数据库
  db-list                                列出数据库连接
  db-query <name> <sql>                  执行SQL查询
  db-tables <name>                       列出表
  db-dump <name> <table> [limit]         导出表数据

[bold yellow]其他:[/bold yellow]
  exec <command>                         执行任意命令
  config [key] [value]                   查看/设置配置
  clear                                  清屏
  help                                   显示帮助
  exit                                   退出
        """
        self.console.print(Panel(help_text, title="帮助", border_style="cyan"))
    
    def cmd_connect(self, args: list):
        """连接WebShell"""
        if len(args) < 3:
            self.console.print("[red]用法: connect <name> <url> <password> [type][/red]")
            return
        
        name, url, password = args[0], args[1], args[2]
        shell_type = args[3] if len(args) > 3 else 'php-eval'
        
        if self.manager.connect(name, url, password, shell_type):
            if not self.current_shell:
                self.cmd_use([name])
    
    def cmd_disconnect(self, args: list):
        """断开连接"""
        if not args:
            self.console.print("[red]用法: disconnect <name>[/red]")
            return
        
        if self.manager.disconnect(args[0]):
            if self.current_name == args[0]:
                self.current_shell = None
                self.current_name = None
    
    def cmd_list(self, args: list):
        """列出连接"""
        shells = self.manager.list_shells()
        if not shells:
            self.console.print("[yellow]没有活动的连接[/yellow]")
            return
        
        table = Table(title="活动连接")
        table.add_column("名称", style="cyan")
        table.add_column("URL", style="green")
        table.add_column("类型", style="yellow")
        
        for name, shell in shells.items():
            table.add_row(
                name,
                shell.url,
                type(shell).__name__
            )
        
        self.console.print(table)
    
    def cmd_use(self, args: list):
        """切换连接"""
        if not args:
            self.console.print("[red]用法: use <name>[/red]")
            return
        
        shell = self.manager.get_shell(args[0])
        if shell:
            self.current_shell = shell
            self.current_name = args[0]
            self.file_ops = FileOperations(shell, self.logger)
            self.sys_ops = SystemOperations(shell, self.logger)
            self.priv_ops = PrivilegeEscalation(shell, self.logger)
            self.db_manager = DatabaseManager(shell, self.logger)
            self.console.print(f"[green]已切换到 {args[0]}[/green]")
        else:
            self.console.print(f"[red]连接 {args[0]} 不存在[/red]")
    
    def require_shell(self) -> bool:
        """检查是否已选择shell"""
        if not self.current_shell:
            self.console.print("[red]请先使用 'use' 命令选择一个连接[/red]")
            return False
        return True
    
    def print_result(self, success: bool, result: str):
        """打印执行结果"""
        if success:
            self.console.print(Panel(result, title="结果", border_style="green"))
        else:
            self.console.print(f"[red]错误: {result}[/red]")
    
    def run(self):
        """运行CLI"""
        self.console.print(Panel.fit(
            "[bold cyan]WebShell Manager v1.0[/bold cyan]\n"
            "适合AI使用的命令行WebShell管理工具\n"
            "输入 'help' 查看帮助",
            border_style="cyan"
        ))
        
        while True:
            try:
                # 获取用户输入
                text = self.session.prompt(self.get_prompt())
                
                # 解析命令
                text = text.strip()
                if not text:
                    continue
                
                parts = text.split()
                cmd = parts[0].lower()
                args = parts[1:]
                
                # 处理命令
                if cmd == 'exit':
                    self.console.print("[yellow]再见！[/yellow]")
                    break
                
                elif cmd == 'help':
                    self.print_help()
                
                elif cmd == 'clear':
                    os.system('cls' if os.name == 'nt' else 'clear')
                
                elif cmd == 'connect':
                    self.cmd_connect(args)
                
                elif cmd == 'disconnect':
                    self.cmd_disconnect(args)
                
                elif cmd == 'list':
                    self.cmd_list(args)
                
                elif cmd == 'use':
                    self.cmd_use(args)
                
                elif cmd == 'config':
                    if not args:
                        # 显示所有配置
                        for k, v in self.config.config.items():
                            self.console.print(f"{k}: {v}")
                    elif len(args) == 1:
                        # 显示指定配置
                        self.console.print(f"{args[0]}: {self.config.get(args[0])}")
                    else:
                        # 设置配置
                        self.config.set(args[0], args[1])
                        self.console.print(f"[green]已设置 {args[0]} = {args[1]}[/green]")
                
                elif cmd == 'exec':
                    if not self.require_shell():
                        continue
                    command = ' '.join(args)
                    success, result = self.current_shell.execute(command)
                    self.print_result(success, result)
                
                # 文件操作
                elif cmd == 'pwd':
                    if not self.require_shell():
                        continue
                    success, result = self.file_ops.pwd()
                    self.print_result(success, result)
                
                elif cmd == 'ls':
                    if not self.require_shell():
                        continue
                    path = args[0] if args else '.'
                    success, result = self.file_ops.ls(path)
                    self.print_result(success, result)
                
                elif cmd == 'cd':
                    if not self.require_shell():
                        continue
                    if not args:
                        self.console.print("[red]用法: cd <path>[/red]")
                        continue
                    success, result = self.file_ops.cd(args[0])
                    self.print_result(success, result)
                
                elif cmd == 'cat':
                    if not self.require_shell():
                        continue
                    if not args:
                        self.console.print("[red]用法: cat <file>[/red]")
                        continue
                    success, result = self.file_ops.cat(args[0])
                    if success:
                        # 尝试语法高亮
                        try:
                            syntax = Syntax(result, "php", theme="monokai", line_numbers=True)
                            self.console.print(syntax)
                        except:
                            self.print_result(success, result)
                    else:
                        self.print_result(success, result)
                
                elif cmd == 'download':
                    if not self.require_shell():
                        continue
                    if len(args) < 2:
                        self.console.print("[red]用法: download <remote> <local>[/red]")
                        continue
                    self.file_ops.download(args[0], args[1])
                
                elif cmd == 'upload':
                    if not self.require_shell():
                        continue
                    if len(args) < 2:
                        self.console.print("[red]用法: upload <local> <remote>[/red]")
                        continue
                    self.file_ops.upload(args[0], args[1])
                
                elif cmd == 'rm':
                    if not self.require_shell():
                        continue
                    if not args:
                        self.console.print("[red]用法: rm <path>[/red]")
                        continue
                    success, result = self.file_ops.rm(args[0])
                    self.print_result(success, result)
                
                elif cmd == 'mkdir':
                    if not self.require_shell():
                        continue
                    if not args:
                        self.console.print("[red]用法: mkdir <path>[/red]")
                        continue
                    success, result = self.file_ops.mkdir(args[0])
                    self.print_result(success, result)
                
                elif cmd == 'mv':
                    if not self.require_shell():
                        continue
                    if len(args) < 2:
                        self.console.print("[red]用法: mv <src> <dst>[/red]")
                        continue
                    success, result = self.file_ops.mv(args[0], args[1])
                    self.print_result(success, result)
                
                elif cmd == 'cp':
                    if not self.require_shell():
                        continue
                    if len(args) < 2:
                        self.console.print("[red]用法: cp <src> <dst>[/red]")
                        continue
                    success, result = self.file_ops.cp(args[0], args[1])
                    self.print_result(success, result)
                
                elif cmd == 'find':
                    if not self.require_shell():
                        continue
                    if not args:
                        self.console.print("[red]用法: find <path> [name][/red]")
                        continue
                    path = args[0]
                    name = args[1] if len(args) > 1 else ''
                    success, result = self.file_ops.find(path, name)
                    self.print_result(success, result)
                
                elif cmd == 'grep':
                    if not self.require_shell():
                        continue
                    if len(args) < 2:
                        self.console.print("[red]用法: grep <pattern> <path>[/red]")
                        continue
                    success, result = self.file_ops.grep(args[0], args[1])
                    self.print_result(success, result)
                
                # 系统操作
                elif cmd == 'whoami':
                    if not self.require_shell():
                        continue
                    success, result = self.sys_ops.whoami()
                    self.print_result(success, result)
                
                elif cmd == 'id':
                    if not self.require_shell():
                        continue
                    success, result = self.sys_ops.id()
                    self.print_result(success, result)
                
                elif cmd == 'uname':
                    if not self.require_shell():
                        continue
                    success, result = self.sys_ops.uname()
                    self.print_result(success, result)
                
                elif cmd == 'ps':
                    if not self.require_shell():
                        continue
                    success, result = self.sys_ops.ps()
                    self.print_result(success, result)
                
                elif cmd == 'netstat':
                    if not self.require_shell():
                        continue
                    success, result = self.sys_ops.netstat()
                    self.print_result(success, result)
                
                elif cmd == 'ifconfig':
                    if not self.require_shell():
                        continue
                    success, result = self.sys_ops.ifconfig()
                    self.print_result(success, result)
                
                elif cmd == 'env':
                    if not self.require_shell():
                        continue
                    success, result = self.sys_ops.env()
                    self.print_result(success, result)
                
                elif cmd == 'kill':
                    if not self.require_shell():
                        continue
                    if not args:
                        self.console.print("[red]用法: kill <pid>[/red]")
                        continue
                    success, result = self.sys_ops.kill(int(args[0]))
                    self.print_result(success, result)
                
                # 提权辅助
                elif cmd == 'suid':
                    if not self.require_shell():
                        continue
                    success, result = self.priv_ops.find_suid()
                    self.print_result(success, result)
                
                elif cmd == 'sgid':
                    if not self.require_shell():
                        continue
                    success, result = self.priv_ops.find_sgid()
                    self.print_result(success, result)
                
                elif cmd == 'writable':
                    if not self.require_shell():
                        continue
                    success, result = self.priv_ops.find_writable()
                    self.print_result(success, result)
                
                elif cmd == 'cron':
                    if not self.require_shell():
                        continue
                    success, result = self.priv_ops.check_cron()
                    self.print_result(success, result)
                
                elif cmd == 'kernel':
                    if not self.require_shell():
                        continue
                    success, result = self.priv_ops.check_kernel_exploit()
                    self.print_result(success, result)
                
                # 数据库操作
                elif cmd == 'db-connect':
                    if not self.require_shell():
                        continue
                    if len(args) < 3:
                        self.console.print("[red]用法: db-connect <name> <type> <params>[/red]")
                        self.console.print("  MySQL: db-connect <name> mysql <host> <port> <user> <pass> [db]")
                        self.console.print("  SQLite: db-connect <name> sqlite <path>")
                        continue
                    
                    db_name = args[0]
                    db_type = args[1].lower()
                    
                    if db_type == 'mysql':
                        if len(args) < 5:
                            self.console.print("[red]用法: db-connect <name> mysql <host> <port> <user> <pass> [db][/red]")
                            continue
                        host, port, user, pwd = args[2], int(args[3]), args[4], args[5]
                        database = args[6] if len(args) > 6 else ''
                        if self.db_manager.add_mysql(db_name, host, port, user, pwd, database):
                            self.console.print(f"[green]数据库 {db_name} 连接成功[/green]")
                    
                    elif db_type == 'sqlite':
                        if len(args) < 3:
                            self.console.print("[red]用法: db-connect <name> sqlite <path>[/red]")
                            continue
                        self.db_manager.add_sqlite(db_name, args[2])
                        self.console.print(f"[green]SQLite数据库 {db_name} 已添加[/green]")
                    
                    else:
                        self.console.print(f"[red]不支持的数据库类型: {db_type}[/red]")
                
                elif cmd == 'db-list':
                    if not self.require_shell():
                        continue
                    connections = self.db_manager.list_connections()
                    if connections:
                        self.console.print("[green]数据库连接:[/green]")
                        for conn in connections:
                            self.console.print(f"  - {conn}")
                    else:
                        self.console.print("[yellow]没有数据库连接[/yellow]")
                
                elif cmd == 'db-query':
                    if not self.require_shell():
                        continue
                    if len(args) < 2:
                        self.console.print("[red]用法: db-query <name> <sql>[/red]")
                        continue
                    db = self.db_manager.get(args[0])
                    if db:
                        sql = ' '.join(args[1:])
                        success, result = db.query(sql)
                        if success:
                            table = Table(title="查询结果")
                            if result:
                                # 添加列
                                for key in result[0].keys():
                                    table.add_column(key)
                                # 添加行
                                for row in result:
                                    table.add_row(*[str(v) for v in row.values()])
                            self.console.print(table)
                        else:
                            self.console.print(f"[red]查询失败[/red]")
                    else:
                        self.console.print(f"[red]数据库连接 {args[0]} 不存在[/red]")
                
                elif cmd == 'db-tables':
                    if not self.require_shell():
                        continue
                    if not args:
                        self.console.print("[red]用法: db-tables <name>[/red]")
                        continue
                    db = self.db_manager.get(args[0])
                    if db:
                        success, tables = db.get_tables()
                        if success:
                            self.console.print("[green]表:[/green]")
                            for table in tables:
                                self.console.print(f"  - {table}")
                        else:
                            self.console.print("[red]获取表失败[/red]")
                    else:
                        self.console.print(f"[red]数据库连接 {args[0]} 不存在[/red]")
                
                elif cmd == 'db-dump':
                    if not self.require_shell():
                        continue
                    if len(args) < 2:
                        self.console.print("[red]用法: db-dump <name> <table> [limit][/red]")
                        continue
                    db = self.db_manager.get(args[0])
                    if db:
                        table_name = args[1]
                        limit = int(args[2]) if len(args) > 2 else 100
                        success, data = db.dump_table(table_name, limit)
                        if success:
                            table = Table(title=f"{table_name} 数据")
                            if data:
                                for key in data[0].keys():
                                    table.add_column(key)
                                for row in data:
                                    table.add_row(*[str(v) for v in row.values()])
                            self.console.print(table)
                        else:
                            self.console.print("[red]导出失败[/red]")
                    else:
                        self.console.print(f"[red]数据库连接 {args[0]} 不存在[/red]")
                
                else:
                    # 未知命令，尝试作为shell命令执行
                    if self.require_shell():
                        success, result = self.current_shell.execute(text)
                        self.print_result(success, result)
                
            except KeyboardInterrupt:
                self.console.print("\n[yellow]使用 'exit' 退出[/yellow]")
                continue
            except EOFError:
                break
            except Exception as e:
                self.console.print(f"[red]错误: {str(e)}[/red]")
