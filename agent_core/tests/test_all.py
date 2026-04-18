# OmniAgent 测试模块

import os
import sys
import re
from langchain_core.messages import HumanMessage, AIMessage

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agent_core.rag import retrieve, build_vector_store
 

def test_tools():
    """测试工具触发"""
    try:
        # 导入工具列表
        from agent_core.tools import TOOLS
        
        # 检查工具列表是否为空
        assert len(TOOLS) > 0, "工具列表为空"
        
        # 检查工具是否为 StructuredTool 对象
        from langchain_core.tools import StructuredTool
        assert isinstance(TOOLS[0], StructuredTool), "工具不是 StructuredTool 对象"
        
        # 检查工具名称
        assert TOOLS[0].name == "get_current_time", "工具名称不正确"
        
        print("[通过] 工具测试通过")
        return True
    except Exception as e:
        print(f"[失败] 工具测试失败: {e}")
        return False


def test_rag():
    """测试 RAG 检索"""
    try:
        # 检查 API Key 是否存在
        if not os.getenv("DASHSCOPE_API_KEY") and not os.getenv("OPENAI_API_KEY"):
            print("[警告] 跳过 RAG 测试：未设置 API Key")
            return True
        
        # 测试检索
        results = retrieve("博客项目", top_k=1)
        assert isinstance(results, list), "RAG 检索返回值不是列表"
        
        # 检查向量库是否存在
        from agent_core.config import PERSIST_DIR
        if os.path.exists(PERSIST_DIR):
            # 如果向量库存在，断言返回结果
            if results:
                assert isinstance(results[0], str), "检索结果不是字符串"
                assert len(results[0]) > 0, "检索结果为空"
                print("[通过] RAG 检索测试通过")
            else:
                print("[警告] RAG 检索返回空结果（可能知识库中无相关内容）")
        else:
            print("[警告] 跳过 RAG 检索测试：向量库不存在")
        
        return True
    except Exception as e:
        print(f"[失败] RAG 测试失败: {e}")
        return False


def test_integration():
    """测试集成流程"""
    try:
        # 检查 API Key 是否存在
        if not os.getenv("DASHSCOPE_API_KEY") and not os.getenv("OPENAI_API_KEY"):
            print("[警告] 跳过集成测试：未设置 API Key")
            return True
        
        # 导入 agent 模块
        from agent_core.agent import run_agent
        
        # 测试时间工具
        user_input = "现在几点"
        reply = run_agent(user_input, "test_thread")
        
        # 断言回复包含时间数字
        time_pattern = r"\d{2}:\d{2}"
        assert re.search(time_pattern, reply), "回复中未包含时间信息"
        
        print("[通过] 集成测试通过")
        return True
    except Exception as e:
        print(f"[失败] 集成测试失败: {e}")
        return False


def run_all_tests():
    """运行所有测试"""
    print("开始测试 OmniAgent 模块...\n")
    
    tests = [
        ("工具测试", test_tools),
        ("RAG 测试", test_rag),
        ("集成测试", test_integration)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"测试: {test_name}")
        if test_func():
            passed += 1
        print()
    
    print(f"测试完成: {passed}/{total} 测试通过")


if __name__ == "__main__":
    run_all_tests()
