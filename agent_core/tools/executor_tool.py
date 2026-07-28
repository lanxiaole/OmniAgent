# Python 代码执行工具模块
# 提供安全的 Python 代码执行能力

from langchain_core.tools import tool
from agent_core.executor.python_executor import execute_code
from agent_core.config.settings import EXECUTION_MAX_RETRIES
from agent_core.logger import get_logger

logger = get_logger(__name__)

# 会话级别的重试计数器（简单实现）
_retry_counter = {}


def _get_retry_count(session_id: str = "default") -> int:
    """获取当前会话的重试次数"""
    return _retry_counter.get(session_id, 0)


def _increment_retry(session_id: str = "default") -> int:
    """增加重试次数并返回新值"""
    _retry_counter[session_id] = _retry_counter.get(session_id, 0) + 1
    return _retry_counter[session_id]


def _reset_retry(session_id: str = "default") -> None:
    """重置重试次数"""
    _retry_counter[session_id] = 0


@tool
def execute_python(code: str) -> str:
    """执行 Python 代码并返回结果。当需要计算、数据分析、算法验证、文件处理、自动化任务时使用。
    
    参数:
        code: 要执行的 Python 代码
        
    调用示例:
    - 用户: "帮我计算斐波那契数列前10项" -> 调用 execute_python 计算并返回结果
    - 用户: "分析这个CSV文件的数据分布" -> 先 read_file 读取数据，再 execute_python 分析
    - 用户: "画一个正弦函数图像" -> 调用 execute_python 使用 matplotlib 生成图表
    
    安全说明:
    - 禁止执行包含 os.system、subprocess、eval、exec 等危险调用的代码
    - 代码执行超时（默认30秒）会自动终止
    - 同一段代码最多修改执行3次
    """
    try:
        logger.debug(f"执行 Python 代码，长度: {len(code)} 字符")
        
        # 执行代码
        result = execute_code(code)
        
        # 处理执行结果
        if result.success:
            # 执行成功
            output = f"✅ 代码执行成功（耗时 {result.execution_time:.2f} 秒）\n\n输出结果：\n{result.output}"
            logger.info(f"代码执行成功，耗时: {result.execution_time:.2f}秒")
            return output
        else:
            # 执行失败
            if result.is_dangerous:
                # 危险代码，直接返回错误
                return result.error
            
            # 普通错误，尝试重试
            retry_count = _get_retry_count()
            max_retries = EXECUTION_MAX_RETRIES or 3
            
            error_msg = result.error
            
            if retry_count >= max_retries:
                # 已达到最大重试次数
                _reset_retry()
                return f"❌ 代码执行失败（已尝试修改 {max_retries} 次）\n\n错误信息：\n{error_msg}\n\n已尝试修改 {max_retries} 次仍无法执行，建议人工介入。"
            else:
                # 提示用户是否重试
                current_retry = _increment_retry()
                return f"❌ 代码执行失败\n\n错误信息：\n{error_msg}\n\n是否希望我修改代码并重新执行？（已尝试 {current_retry}/{max_retries} 次）"
    
    except Exception as e:
        logger.error(f"执行代码失败: {e}")
        return f"❌ 执行环境错误: {str(e)}"