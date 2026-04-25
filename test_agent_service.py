#!/usr/bin/env python3
"""测试 Agent 服务层的流式输出功能"""
import asyncio
import sys
from backend.services.agent_service import stream_agent_reply

async def test_stream_agent_reply():
    """测试流式输出服务"""
    print("开始测试 Agent 服务层的流式输出...")
    print("输入: 你好，你是谁？")
    print("输出:")
    print("=" * 50)
    
    try:
        async for token in stream_agent_reply("你好，你是谁？你能做什么", "test_thread"):
            # 处理编码问题，忽略无法编码的字符
            print(f"Token: '{token}'")
            # 添加小延迟，让流式效果更明显
            await asyncio.sleep(0.1)
        print("=" * 50)
        print("测试完成，流式输出成功！")
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # 设置输出编码为 UTF-8
    sys.stdout.reconfigure(encoding='utf-8')
    asyncio.run(test_stream_agent_reply())
