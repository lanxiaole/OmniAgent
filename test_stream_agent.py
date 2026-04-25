#!/usr/bin/env python3
"""测试 Agent 流式输出功能"""
import asyncio
import sys
from agent_core.agent.executor import stream_agent

async def test_stream_agent():
    """测试流式输出"""
    print("开始测试 Agent 流式输出...")
    print("输入: 你好，你是谁？，你能帮我做什么，请详细介绍")
    print("输出:")
    print("=" * 50)
    
    try:
        # 直接调用 agent.astream 来测试原始的流式输出
        from agent_core.agent.executor import get_async_agent_executor
        from langchain_core.runnables import RunnableConfig
        
        agent = await get_async_agent_executor()
        config = RunnableConfig(configurable={"thread_id": "test"})
        
        print("开始流式获取回复...")
        print("\n流式输出内容（逐token）:")
        print("-" * 50)
        
        async for chunk in agent.astream(
            {"messages": [{"role": "user", "content": "你好，你是谁？你能帮我做什么，请详细介绍"}]},
            config=config,
            stream_mode="messages"
        ):
            # 根据官方文档，chunk 是 (token, metadata) 元组
            token, metadata = chunk
            if hasattr(token, 'content') and token.content:
                print(f"Token: '{token.content}'")
                # 添加小延迟，让流式效果更明显
                await asyncio.sleep(0.1)
        
        print("-" * 50)
        print("\n测试完成，流式输出成功！")
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # 确保使用 UTF-8 编码
    sys.stdout.reconfigure(encoding='utf-8')
    asyncio.run(test_stream_agent())
