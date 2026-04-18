import os

def load_prompt(name: str) -> str:
    """从 prompts/ 目录读取指定的 prompt 文件
    
    参数:
        name: prompt 名称，对应 prompts/{name}.txt 文件
        
    返回:
        str: prompt 内容
        
    异常:
        FileNotFoundError: 当指定的 prompt 文件不存在时
    """
    # 构建文件路径
    prompt_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "prompts", f"{name}.txt")
    
    try:
        # 使用 UTF-8 编码读取文件
        with open(prompt_file, "r", encoding="utf-8") as f:
            return f.read().strip()
    except FileNotFoundError:
        raise FileNotFoundError(f"Prompt 文件不存在: {prompt_file}")
    except Exception as e:
        raise Exception(f"读取 Prompt 文件时出错: {e}")
