import os
import sys
import time
from pathlib import Path
from typing import Optional, Dict, Any, List, Union
from contextlib import redirect_stdout
from io import StringIO


class TempComponent(object):
    """A component that uses ip_builder to process source files.
    
    This component manages ip_builder configuration and provides an interface
    to build source files with prefixing and macro processing capabilities.
    """
    
    def __init__(self, root_path: Optional[str] = None):
        """Initialize TempComponent.
        
        Args:
            root_path: Path to ip_builder root directory. If None, will search in current directory
                      and parent directories.
        """
        self.name = "TempComponent"
        self.root_path = self._find_ip_builder_root(root_path)
        self._ip_builder_module = None
        self._config: Dict[str, Any] = {
            'prefix': '',  # Default prefix for file names
            'keep_prefix': True,  # Whether to keep existing prefixes
            'exclude_foundation_ip': False,  # Whether to exclude foundation IP
            'macro_yaml': None,  # Path to macro YAML file
            'filelist_env_prefix': None  # Environment prefix for filelist
        }
        
        # 初始化日志缓存
        self._log_buffer = StringIO()
        self._log_path = "IPBUILD.log"
        
        # 检查并删除已存在的日志文件
        if os.path.exists(self._log_path):
            os.remove(self._log_path)
            
        # Try to import ip_builder
        self._import_ip_builder()
    
    def _find_ip_builder_root(self, root_path: Optional[str]) -> str:
        """Find ip_builder root directory.
        
        Will search for ip_builder.py in the specified directory or current directory
        and its parents if not specified.
        
        Args:
            root_path: Optional path to start searching from
            
        Returns:
            Absolute path to ip_builder root directory
            
        Raises:
            RuntimeError: If ip_builder.py cannot be found
        """
        if root_path:
            root = Path(root_path)
            if (root / 'ip_builder.py').exists():
                return str(root.absolute())
            elif (root / 'ip_builder/ip_builder.py').exists():
                return str((root / 'ip_builder').absolute())
            raise RuntimeError(f"ip_builder.py not found in {root}")
            
        # Search in current dir and parents
        current = Path.cwd()
        while current != current.parent:
            if (current / 'ip_builder.py').exists():
                return str(current.absolute())
            elif (current / 'ip_builder/ip_builder.py').exists():
                return str((current / 'ip_builder').absolute())
            current = current.parent
            
        raise RuntimeError("ip_builder.py not found in current directory or its parents")
    
    def _import_ip_builder(self):
        """Import the ip_builder module from the root path."""
        if self._ip_builder_module is not None:
            return
            
        # Add root_path to Python path temporarily
        if self.root_path not in sys.path:
            sys.path.insert(0, self.root_path)
        
        try:
            # 直接执行 ip_builder.py 脚本，这样可以获取所有函数
            import runpy
            self._ip_builder_module = runpy.run_path(
                os.path.join(self.root_path, 'ip_builder.py'),
                run_name='ip_builder'
            )
        except Exception as e:
            raise RuntimeError(f"Failed to import ip_builder: {e}")
        finally:
            if self.root_path in sys.path:
                sys.path.remove(self.root_path)
    
    def _write_log(self, content: str):
        """写入日志到缓存"""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        self._log_buffer.write(f"[{timestamp}] {content}\n")

    def _save_log(self):
        """保存日志到文件"""
        with open(self._log_path, 'a') as f:
            f.write("\n" + "="*80 + "\n")
            f.write(f"Build started at: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("Configuration:\n")
            for key, value in self._config.items():
                f.write(f"  {key}: {value}\n")
            f.write("-"*80 + "\n")
            f.write(self._log_buffer.getvalue())
            f.write("="*80 + "\n")
    
    def configure(self, **kwargs):
        """Configure ip_builder parameters.
        
        Args:
            **kwargs: Configuration parameters. Supported keys:
                - prefix: Prefix to add to file names
                - keep_prefix: Whether to keep existing prefixes
                - exclude_foundation_ip: Whether to exclude foundation IP
                - macro_yaml: Path to macro YAML file
                - filelist_env_prefix: Environment prefix for filelist
        """
        valid_keys = set(self._config.keys())
        for key, value in kwargs.items():
            if key not in valid_keys:
                raise ValueError(f"Unknown configuration key: {key}")
            self._config[key] = value
            
    def build(self, source: Union[str, List[str]], dest_path: str) -> None:
        """Build source files to destination path using ip_builder.
        
        Args:
            source: Can be one of:
                   - A list of source file paths
                   - Path to a filelist (.f) file
                   - Path to a source directory
            dest_path: Destination directory path
            
        Raises:
            RuntimeError: If ip_builder fails or is not properly configured
            ValueError: If source format is invalid
        """
        # 重置日志缓存
        self._log_buffer = StringIO()
        success = False
        filelist = None
        temp_filelist = False
        
        try:
            if not self._ip_builder_module:
                raise RuntimeError("ip_builder module not imported")
            
            # 记录基本信息
            self._write_log(f"Source: {source}")
            self._write_log(f"Destination: {dest_path}")
            
            if isinstance(source, list):
                # List of source files
                self._write_log("Mode: File list from Python list")
                import tempfile
                with tempfile.NamedTemporaryFile(mode='w', suffix='.f', delete=False) as f:
                    for src in source:
                        f.write(f"{src}\n")
                    filelist = f.name
                    temp_filelist = True
                self._write_log(f"Created temporary filelist: {filelist}")
                source_path = Path(filelist)
                
            else:
                source_path = Path(source)
                
            if not source_path.exists():
                raise ValueError(f"Source path does not exist: {source}")
                
            # Create destination directory if it doesn't exist
            dest_path = os.path.abspath(dest_path)
            if not os.path.exists(dest_path):
                os.makedirs(dest_path)
                
            if source_path.is_file() and source_path.suffix == '.f':
                # Filelist mode
                self._write_log("Mode: Filelist file")
                filelist = str(source_path)
                
                # 捕获所有输出到日志
                with redirect_stdout(self._log_buffer):
                    build_from_filelist = self._ip_builder_module['build_from_filelist']
                    build_from_filelist(
                        filelist=filelist,
                        dest_folder=dest_path,
                        prefix=self._config['prefix'],
                        keep_prefix=self._config['keep_prefix'],
                        exclude_foundation_ip=self._config['exclude_foundation_ip'],
                        macro_yaml=self._config['macro_yaml'],
                        filelist_env_prefix=self._config['filelist_env_prefix']
                    )
                
            elif source_path.is_dir():
                # Directory mode
                self._write_log("Mode: Source directory")
                src_folder = str(source_path)
                
                # 捕获所有输出到日志
                with redirect_stdout(self._log_buffer):
                    copy_and_rename = self._ip_builder_module['copy_and_rename']
                    copy_and_rename(
                        src_folder=src_folder,
                        dest_folder=dest_path,
                        prefix=self._config['prefix'],
                        keep_prefix=self._config['keep_prefix']
                    )
                
            else:
                raise ValueError(f"Source must be a .f file or directory: {source}")
            
            # # 如果执行到这里没有异常，标记为成功
            # success = True
            # # 打印简短的成功信息到终端
            # print(f"\nBuild successful!")
            # print(f"Source: {source}")
            # print(f"Destination: {dest_path}")
            
        except Exception as e:
            # 记录错误到日志
            self._write_log(f"ERROR: {str(e)}")
            # 打印简短的错误信息到终端
            print(f"\nBuild failed: {str(e)}")
            raise
            
        finally:
            # 保存日志文件
            self._save_log()
            # 清理临时文件
            if temp_filelist and filelist and os.path.exists(filelist):
                os.unlink(filelist)
                self._write_log(f"Cleaned up temporary filelist: {filelist}")
                
    def clean(self, dest_path: str) -> None:
        """清除构建的目标文件夹及其所有内容
        
        Args:
            dest_path: 要清除的目标文件夹路径
            
        Note:
            此操作会递归删除整个文件夹及其内容，请谨慎使用
        """
        dest_path = os.path.abspath(dest_path)
        if os.path.exists(dest_path):
            import shutil
            try:
                shutil.rmtree(dest_path)
                print(f"\nCleaned destination folder: {dest_path}")
                self._write_log(f"Cleaned destination folder: {dest_path}")
                self._save_log()
            except Exception as e:
                error_msg = f"Failed to clean destination folder {dest_path}: {str(e)}"
                print(f"\nError: {error_msg}")
                self._write_log(f"ERROR: {error_msg}")
                self._save_log()
                raise
