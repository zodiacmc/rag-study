import sys
from pathlib import Path

# 把项目根目录加入 sys.path，保证直接运行脚本能 import week1 / week4
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# 中文 Windows 终端默认 stdio 编码非 UTF-8，统一重设为 UTF-8，
# 避免 print 中文抛出 UnicodeEncodeError（无 reconfigure 能力的流自动跳过）
for _stream in (sys.stdin, sys.stdout):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8")

import week4.ollama_client as ollama_client

# ---- 顶部配置：切换后端只改这里 ----
MODEL_BACKEND = "ollama"  # "ollama" | "longcat"
OLLAMA_MODEL = "qwen2.5:7b-instruct-q4_K_M"
SYSTEM_PROMPT = "你是一个简洁准确的助手，不编造信息。"
EXIT_WORDS = {"exit", "退出"}

# 用脚本常量覆盖 ollama_client 的模块级 MODEL（不修改原文件，对后续调用生效）
ollama_client.MODEL = OLLAMA_MODEL


def preflight_ollama() -> bool:
    """探测本地 Ollama 是否可用（使用与正式调用相同的模型名）。"""
    try:
        ollama_client.local_chat(
            [{"role": "user", "content": "ping"}], temperature=0
        )
        return True
    except Exception as e:
        print(f"本地 Ollama 不可用：{e}")
        print(
            "排查建议：确认 Ollama 已启动，且模型已拉取"
            f"（ollama pull {OLLAMA_MODEL}）。"
        )
        return False


def stream_reply(messages, backend: str) -> str:
    """按后端流式生成回答，逐段打印并返回完整文本。"""
    try:
        if backend == "ollama":
            gen = ollama_client.local_chat_stream(messages)
        elif backend == "longcat":
            # 延迟导入，避免本地后端被远程配置耦合
            from week1.requests_py.llm_client import chat_stream2

            gen = chat_stream2(messages)
        else:
            print(f"未知后端：{backend}")
            return ""

        full = ""
        for delta in gen:
            print(delta, end="", flush=True)
            full += delta
        print()
        return full
    except Exception as e:
        print(f"请求异常: {e}")
        return ""


def main() -> None:
    backend = MODEL_BACKEND
    if backend == "ollama" and not preflight_ollama():
        return

    history = [{"role": "system", "content": SYSTEM_PROMPT}]
    while True:
        try:
            user_input = input("你问：")
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if user_input.strip().lower() in EXIT_WORDS:
            break
        history.append({"role": "user", "content": user_input})
        answer = stream_reply(history, backend)
        history.append({"role": "assistant", "content": answer})


if __name__ == "__main__":
    main()
