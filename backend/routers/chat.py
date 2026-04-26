from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from backend.schemas.chat import ChatRequest, ChatResponse, HistoryResponse, Message
from backend.services.agent_service import get_agent_reply, get_session_history, clear_session, stream_agent_reply
import json
import asyncio
from agent_core.logger import get_logger

logger = get_logger(__name__)

async def consume_generator(generator):
    """消费异步生成器，将结果收集为列表"""
    results = []
    async for item in generator:
        results.append(item)
    return results

# 创建 APIRouter 实例
router = APIRouter()

@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """聊天端点，处理用户消息并返回 Agent 的回复
    
    Args:
        request: 聊天请求对象，包含用户消息和会话 ID
        
    Returns:
        ChatResponse: 聊天响应对象，包含 Agent 的回复
    """
    reply = await get_agent_reply(request.message, request.thread_id)
    return ChatResponse(reply=reply)


@router.get("/chat/history", response_model=HistoryResponse)
async def get_chat_history(thread_id: str):
    """获取指定会话的历史消息
    
    Args:
        thread_id: 会话 ID，必需参数
        
    Returns:
        HistoryResponse: 包含历史消息列表的响应
    """
    messages = get_session_history(thread_id)
    # 转换为 Message 模型列表
    message_models = [Message(**msg) for msg in messages]
    return HistoryResponse(messages=message_models)


@router.delete("/chat/history")
async def delete_chat_history(thread_id: str):
    """清空指定会话的历史记录
    
    Args:
        thread_id: 会话 ID，必需参数
        
    Returns:
        dict: 操作结果，包含状态和消息
    """
    try:
        clear_session(thread_id)
        return {"status": "success", "message": f"会话 {thread_id} 已清空"}
    except Exception as e:
        return {"status": "error", "message": f"清空失败: {str(e)}"}


@router.post("/chat/stream")
async def chat_stream_endpoint(request: ChatRequest, http_request: Request):
    async def event_generator():
        # 创建一个任务来收集所有 tokens
        result_queue = asyncio.Queue()
        
        async def agent_worker():
            try:
                async for token in stream_agent_reply(request.message, request.thread_id):
                    await result_queue.put(('token', token))
                await result_queue.put(('done', None))
            except asyncio.CancelledError:
                await result_queue.put(('cancelled', None))
            except Exception as e:
                await result_queue.put(('error', f'[ERROR] {str(e)}'))

        async def disconnect_listener():
            while True:
                message = await http_request.receive()
                if message['type'] == 'http.disconnect':
                    await result_queue.put(('disconnect', None))
                    break

        agent_task = asyncio.create_task(agent_worker())
        disconnect_task = asyncio.create_task(disconnect_listener())
        
        try:
            while True:
                msg_type, msg_data = await result_queue.get()
                
                if msg_type == 'token':
                    yield f"data: {json.dumps(msg_data, ensure_ascii=False)}\n\n"
                    
                elif msg_type == 'done':
                    yield f"data: {json.dumps('[DONE]')}\n\n"
                    break
                    
                elif msg_type == 'disconnect':
                    agent_task.cancel()
                    try:
                        await agent_task
                    except asyncio.CancelledError:
                        pass
                    break
                    
                elif msg_type == 'cancelled':
                    break
                    
                elif msg_type == 'error':
                    yield f"data: {json.dumps(msg_data)}\n\n"
                    break
        finally:
            disconnect_task.cancel()
            try:
                await disconnect_task
            except asyncio.CancelledError:
                pass
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )