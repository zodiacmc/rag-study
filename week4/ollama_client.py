from openai import OpenAI

# 连接本地 Ollama 的 OpenAI 兼容端点
client = OpenAI(
    base_url="http://localhost:11434/v1",
    api_key="ollama",
)

MODEL = "qwen2.5:7b-instruct-q4_K_M"

def local_chat(messages, temperature=0.3):
    resp = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        temperature=temperature,
    )
    return resp.choices[0].message.content


def local_chat_stream(messages: list[dict], temperature: float = 0.3):
    """
    流式请求（生成器版本），逐段 yield delta 文本，供 FastAPI StreamingResponse 使用。

    :param messages: 对话消息列表，如
        [{"role": "system", "content": "..."}, {"role": "user", "content": "..."}]
    :param temperature: 采样温度，默认 0.3
    :yield: 每段增量文本字符串（已过滤 None 与空串）
    """
    resp = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        temperature=temperature,
        stream=True,
    )
    for chunk in resp:
        choices = getattr(chunk, "choices", None)
        if not choices:
            # 跳过空 choices 的 chunk（如仅携带 usage 的尾包），避免 IndexError
            continue
        content = getattr(choices[0].delta, "content", None)
        if content:
            # 过滤 None/空串，避免下游 StreamingResponse 输出 "None"
            yield content

if __name__ == "__main__":
    messages = [
        {"role": "system", "content": "你是知识库助手，回答简洁准确。"},
        {"role": "user", "content": "用一句话解释什么是向量数据库"},
    ]
    print(local_chat(messages))

    # 流式示例
    # stream = client.chat.completions.create(
    #     model=MODEL,
    #     messages=messages,
    #     stream=True,
    # )
    # print("\n【流式】")
    # for chunk in stream:
    #     delta = chunk.choices[0].delta.content
    #     if delta:
    #         print(delta, end="", flush=True)

    # 调用local_chat_stream进行流式输出
    for chunk in local_chat_stream(messages):
        print(chunk, end="", flush=True)
