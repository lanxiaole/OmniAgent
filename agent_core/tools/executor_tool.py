# Python 代码执行工具模块
# 提供安全的 Python 代码执行能力
#
# 重试机制（物理强制，不可被 LLM 绕过）：
#   1. 连续失败达到 max_retries（默认3次）后，工具进入"物理锁定"状态
#   2. 锁定状态下，若新提交的代码与上一次失败代码高度相似（>= 0.4），则直接拒绝执行，
#      不调用 subprocess，不消耗资源
#   3. 只有当用户提出全新任务（代码相似度 < 0.4）时，锁定才自动解除
#   4. 执行成功后，失败计数自动清零
#   这样既防止了无限重试烧钱，又不会误锁全新的任务

from difflib import SequenceMatcher
from langchain_core.tools import tool
from agent_core.executor.python_executor import execute_code
from agent_core.config.settings import EXECUTION_MAX_RETRIES
from agent_core.logger import get_logger

logger = get_logger(__name__)

# ==================== 重试状态（模块级单例） ====================
# 连续失败次数（执行成功后归零）
_consecutive_failures = 0
# 上一次失败的代码内容（用于判断新提交是否为"同一任务"）
_last_failed_code = ""


def _code_similarity(code_a: str, code_b: str) -> float:
    """计算两段代码的相似度（0.0 ~ 1.0）

    基于 difflib.SequenceMatcher，比较代码的字符序列相似性。
    用于判断新提交的代码是否属于"同一任务"的修改。
    """
    if not code_a or not code_b:
        return 0.0
    # 去除空白字符后再比较，避免仅缩进/换行差异导致相似度虚高
    norm_a = " ".join(code_a.split())
    norm_b = " ".join(code_b.split())
    return SequenceMatcher(None, norm_a, norm_b).ratio()


def _is_locked() -> bool:
    """判断当前是否处于物理锁定状态"""
    return _consecutive_failures >= (EXECUTION_MAX_RETRIES or 3)


def _is_new_task(new_code: str) -> bool:
    """判断新提交的代码是否为"全新任务"

    判断依据：与上一次失败代码的相似度低于 0.4（即差异显著）。
    相似度阈值 0.4 的含义：约 40% 字符相同即视为同一任务的微调，不予解锁。
    """
    if not _last_failed_code:
        return True
    return _code_similarity(new_code, _last_failed_code) < 0.4


def _record_failure(code: str) -> None:
    """记录一次失败，更新失败计数与失败代码"""
    global _consecutive_failures, _last_failed_code
    _consecutive_failures += 1
    _last_failed_code = code
    logger.warning(f"代码执行失败，连续失败次数: {_consecutive_failures}/{EXECUTION_MAX_RETRIES or 3}")


def _reset_state() -> None:
    """重置重试状态（执行成功或检测到新任务时调用）"""
    global _consecutive_failures, _last_failed_code
    _consecutive_failures = 0
    _last_failed_code = ""


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
    - 同一任务连续失败 3 次后物理锁定，拒绝继续执行相似代码
    """
    global _consecutive_failures

    max_retries = EXECUTION_MAX_RETRIES or 3

    # ============ 物理锁定检查（核心修复） ============
    # 锁定状态下：若新代码与上次失败代码相似，直接拒绝执行（不调用 subprocess）
    # 只有差异显著的"全新任务"才会解锁
    if _is_locked():
        if _is_new_task(code):
            # 全新任务，解除锁定
            logger.info("检测到全新任务代码，解除执行锁定")
            _reset_state()
        else:
            # 同一任务的重复尝试，物理拒绝（不消耗执行资源）
            logger.warning(f"执行已锁定，拒绝执行相似代码（连续失败 {_consecutive_failures} 次）")
            return (
                f"❌ 代码执行已物理锁定（连续失败 {_consecutive_failures} 次）\n\n"
                f"已尝试修改 {max_retries} 次仍无法执行，建议人工介入。\n"
                f"如需尝试完全不同的方案，请提交全新的代码思路。\n"
                f"如需继续当前任务，请人工检查代码逻辑后手动修改。"
            )

    try:
        logger.debug(f"执行 Python 代码，长度: {len(code)} 字符")

        # 执行代码
        result = execute_code(code)

        # 处理执行结果
        if result.success:
            # 执行成功：清零失败计数
            _reset_state()
            output = f"✅ 代码执行成功（耗时 {result.execution_time:.2f} 秒）\n\n输出结果：\n{result.output}"
            logger.info(f"代码执行成功，耗时: {result.execution_time:.2f}秒")
            return output
        else:
            # 执行失败
            if result.is_dangerous:
                # 危险代码：直接返回错误，不计入重试次数（安全拦截，非逻辑错误）
                return result.error

            # 普通错误：记录失败
            _record_failure(code)
            error_msg = result.error
            current_failures = _consecutive_failures

            if current_failures >= max_retries:
                # 达到最大重试次数：物理锁定，返回终态提示（不再邀请重试）
                return (
                    f"❌ 代码执行失败（连续第 {current_failures} 次失败，已达上限 {max_retries}）\n\n"
                    f"错误信息：\n{error_msg}\n\n"
                    f"已尝试修改 {max_retries} 次仍无法执行，建议人工介入。"
                    f"后续对相似代码的执行请求将被物理拒绝。"
                )
            else:
                # 未达上限：返回错误并提示剩余次数
                remaining = max_retries - current_failures
                return (
                    f"❌ 代码执行失败（第 {current_failures}/{max_retries} 次失败）\n\n"
                    f"错误信息：\n{error_msg}\n\n"
                    f"剩余尝试次数：{remaining} 次。"
                    f"是否希望我修改代码并重新执行？"
                )

    except Exception as e:
        # 执行环境异常：计入失败
        _record_failure(code)
        logger.error(f"执行代码失败: {e}")
        return f"❌ 执行环境错误: {str(e)}"
