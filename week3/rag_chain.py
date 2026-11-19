# week3/rag_chain.py
from pathlib import Path

import chromadb

from retrieve import retrieve as all_retrieve
from week1.requests_py.llm_client import chat

DB_PATH = Path(__file__).resolve().parent / "chroma_db"
client = chromadb.PersistentClient(path=str(DB_PATH))
col = client.get_or_create_collection("policy_docs")

SYSTEM_PROMPT = """你是一个知识库助手。请严格只根据下面提供的【参考资料】回答用户问题。
要求：
1. 只使用参考资料里的内容，不要自己编造资料中没有的信息
2. 如果参考资料里没有相关信息，直接回答"资料中未提及"
3. 回答时尽量标注来自哪份资料

【参考资料】
{context}
"""


def retrieve(question, top_k=3):
    """根据问题检索相关文档，返回 (chunks, sources)；无命中时均为空列表。"""
    res = all_retrieve(question, top_k)
    chunks, sources = [], []

    if not res:
        return chunks, sources

    for doc, dist, meta in res:
        chunks.append(doc)
        sources.append(meta["source"])

    return chunks, sources


def build_context(chunks, sources):
    """根据检索结果构建上下文"""
    return "\n\n".join(f"[来自 {s}]\n{c}" for s, c in zip(sources, chunks))


def rag_answer(question, top_k=3):
    """根据问题获取答案"""
    messages, chunks = get_messages(question, top_k)
    answer = chat(messages)
    return answer, chunks


def get_messages(question, top_k=3):
    """根据问题获取消息列表
        Args:
            question (str): 用户问题
            top_k (int): 检索结果数量
        Returns:
            messages (list): 消息列表
            chunks (list): 检索结果列表
    """
    chunks, sources = retrieve(question, top_k)
    context = build_context(chunks, sources)
    system_text = SYSTEM_PROMPT.format(context=context)
    messages = [
        {"role": "system", "content": system_text},
        {"role": "user", "content": question},
    ]
    return messages, chunks


if __name__ == "__main__":
    q = "什么情形可以索要违约赔偿"
    answer, chunks = rag_answer(q)
    print(f"问：{q}")
    print(f"答：{answer}")
    print(f"\n（基于 {len(chunks)} 段资料生成）")
