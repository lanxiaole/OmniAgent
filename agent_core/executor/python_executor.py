# Python 代码执行引擎
# 在独立进程中安全执行 Python 代码

import subprocess
import tempfile
import os
import time
import re
from dataclasses import dataclass
from typing import Optional
from agent_core.config.settings import EXECUTION_TIMEOUT, EXECUTION_WORK_DIR
from agent_core.logger import get_logger

logger = get_logger(__name__)

# 危险函数调用黑名单
DANGEROUS_PATTERNS = [
    # 系统命令执行
    r'\bos\.system\s*\(',
    r'\bos\.popen\s*\(',
    r'\bos\.spawn',
    r'\bsubprocess\.run\s*\(',
    r'\bsubprocess\.Popen\s*\(',
    r'\bsubprocess\.call\s*\(',
    r'\bsubprocess\.check_output\s*\(',
    # 动态执行
    r'\beval\s*\(',
    r'\bexec\s*\(',
    r'\bcompile\s*\(',
    # 导入危险模块
    r"__import__\s*\(\s*['\"]os['\"]",
    r"__import__\s*\(\s*['\"]subprocess['\"]",
    r"__import__\s*\(\s*['\"]socket['\"]",
    r'\bimport\s+os\b',
    r'\bfrom\s+os\s+import\b',
    r'\bimport\s+subprocess\b',
    r'\bfrom\s+subprocess\s+import\b',
    # 文件系统危险操作
    r'\bos\.remove\s*\(',
    r'\bos\.rmdir\s*\(',
    r'\bshutil\.rmtree\s*\(',
    # 网络操作
    r'\bsocket\.socket\s*\(',
    r'\burllib\.request\s*\(',
    r'\brequests\.(get|post|put|delete)\s*\(',
]


@dataclass
class ExecutionResult:
    """代码执行结果"""
    success: bool
    output: str
    error: str
    execution_time: float
    is_dangerous: bool = False
    danger_reason: str = ""


def _check_dangerous_code(code: str) -> tuple[bool, str]:
    """
    检查代码中是否包含危险调用
    
    返回:
        tuple[bool, str]: (是否危险, 危险原因)
    """
    for pattern in DANGEROUS_PATTERNS:
        match = re.search(pattern, code)
        if match:
            return True, f"检测到危险调用: {match.group()}"
    return False, ""


def execute_code(code: str, timeout: int = None) -> ExecutionResult:
    """
    在独立进程中执行 Python 代码
    
    参数:
        code: 要执行的 Python 代码
        timeout: 超时时间（秒），默认从配置读取
        
    返回:
        ExecutionResult: 执行结果对象
    """
    if timeout is None:
        timeout = EXECUTION_TIMEOUT or 30
    
    # 1. 安全预扫描
    is_dangerous, danger_reason = _check_dangerous_code(code)
    if is_dangerous:
        logger.warning(f"代码安全检查失败: {danger_reason}")
        return ExecutionResult(
            success=False,
            output="",
            error=f"❌ 安全警告：代码包含危险操作，拒绝执行。\n{danger_reason}\n\n禁止的操作包括：系统命令执行、动态代码执行、网络请求等。",
            execution_time=0,
            is_dangerous=True,
            danger_reason=danger_reason
        )
    
    # 2. 准备执行环境
    work_dir = EXECUTION_WORK_DIR or os.path.join(os.getcwd(), "temp_exec")
    os.makedirs(work_dir, exist_ok=True)
    
    start_time = time.time()
    
    try:
        # 3. 创建临时文件
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.py',
            dir=work_dir,
            delete=False,
            encoding='utf-8'
        ) as f:
            f.write(code)
            temp_file = f.name
        
        # 4. 执行代码
        logger.info(f"开始执行代码，超时: {timeout}秒")
        
        result = subprocess.run(
            ['python', temp_file],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=work_dir,
            env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'}
        )
        
        execution_time = time.time() - start_time
        
        # 5. 清理临时文件
        try:
            os.remove(temp_file)
        except Exception:
            pass
        
        # 6. 处理执行结果
        if result.returncode == 0:
            output = result.stdout.strip()
            logger.info(f"代码执行成功，耗时: {execution_time:.2f}秒")
            return ExecutionResult(
                success=True,
                output=output,
                error="",
                execution_time=execution_time
            )
        else:
            error_msg = result.stderr.strip()
            logger.warning(f"代码执行失败: {error_msg}")
            return ExecutionResult(
                success=False,
                output="",
                error=error_msg,
                execution_time=execution_time
            )
    
    except subprocess.TimeoutExpired:
        execution_time = time.time() - start_time
        logger.warning(f"代码执行超时 ({timeout}秒)")
        
        # 清理可能残留的临时文件
        try:
            if 'temp_file' in locals():
                os.remove(temp_file)
        except Exception:
            pass
        
        return ExecutionResult(
            success=False,
            output="",
            error=f"❌ 代码运行超时（超过 {timeout} 秒），已自动终止。\n\n可能原因：\n- 代码包含无限循环\n- 计算量过大\n- 等待用户输入\n\n建议：检查代码逻辑或增加超时时间。",
            execution_time=execution_time
        )
    
    except Exception as e:
        execution_time = time.time() - start_time
        logger.error(f"代码执行异常: {e}")
        
        # 清理临时文件
        try:
            if 'temp_file' in locals():
                os.remove(temp_file)
        except Exception:
            pass
        
        return ExecutionResult(
            success=False,
            output="",
            error=f"❌ 执行环境错误: {str(e)}",
            execution_time=execution_time
        )