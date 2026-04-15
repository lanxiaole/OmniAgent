# OmniAgent 测试模块

import os
import re
from langchain_core.messages import HumanMessage, AIMessage
import model
import memory
import tools
import rag


def test_model():
    """测试模型调用"""
    try:
        # 检查 API Key 是否存在
        if not os.getenv("DASHSCOPE_API_KEY") and not os.getenv("OPENAI_API_KEY"):
            print("[警告] 跳过模型测试：未设置 API Key")
            return True
        
        # 测试模型调用
        response = model.chat([HumanMessage(content="你好")])
        assert isinstance(response, str), "模型返回值不是字符串"
        assert len(response) > 0, "模型返回值为空"
        print("[通过] 模型测试通过")
        return True
    except Exception as e:
        print(f"[失败] 模型测试失败: {e}")
        return False


def test_memory():
    """测试记忆模块"""
    try:
        # 清空记忆
        memory.clear()
        
        # 添加用户消息
        memory.add_user_message("测试用户消息")
        
        # 添加 AI 消息
        memory.add_ai_message("测试 AI 消息")
        
        # 获取消息
        messages = memory.get_messages()
        
        # 断言消息数量
        assert len(messages) == 2, f"记忆模块消息数量错误，期望 2，实际 {len(messages)}"
        
        # 断言消息类型
        assert isinstance(messages[0], HumanMessage), "第一条消息不是 HumanMessage"
        assert isinstance(messages[1], AIMessage), "第二条消息不是 AIMessage"
        
        print("[通过] 记忆模块测试通过")
        return True
    except Exception as e:
        print(f"[失败] 记忆模块测试失败: {e}")
        return False


def test_tools():
    """测试工具触发"""
    try:
        # 测试时间工具
        time_result = tools.maybe_use_tool("现在几点")
        assert isinstance(time_result, str), "时间工具返回值不是字符串"
        
        # 验证时间格式
        time_pattern = r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$"
        assert re.match(time_pattern, time_result), "时间格式错误"
        
        # 测试非时间查询
        non_time_result = tools.maybe_use_tool("你好")
        assert non_time_result is None, "非时间查询不应该触发工具"
        
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
        results = rag.retrieve("博客项目", top_k=1)
        assert isinstance(results, list), "RAG 检索返回值不是列表"
        
        # 检查向量库是否存在
        if os.path.exists(rag.PERSIST_DIR):
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
        
        # 清空记忆
        memory.clear()
        
        # 模拟用户输入
        user_input = "现在几点"
        
        # 构建增强消息（复制 main.py 中的逻辑）
        def build_enhanced_message(user_input):
            tool_result = tools.maybe_use_tool(user_input)
            if tool_result is not None:
                return f"用户问：{user_input}\n[工具结果]：{tool_result}\n请根据工具结果回答用户。"
            
            retrieval_results = rag.retrieve(user_input)
            if retrieval_results:
                knowledge = retrieval_results[0]
                return f"用户问：{user_input}\n[参考知识]：{knowledge}\n请基于参考知识回答用户。如果参考知识不足以回答，可以说'我不确定'。"
            
            return user_input
        
        # 构建增强消息
        enhanced_input = build_enhanced_message(user_input)
        
        # 添加用户消息
        memory.add_user_message(enhanced_input)
        
        # 调用模型
        reply = model.chat(memory.get_messages())
        
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
        ("模型测试", test_model),
        ("记忆模块测试", test_memory),
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
