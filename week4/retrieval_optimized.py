"""
Day27：优化版检索（混合检索 + RRF 融合 + 兜底），接 Day25 本地 RAG 链路。

链路：本地 Chroma(bge-m3) 向量召回 + BM25 关键词召回 → RRF 融合去重 → 兜底判断
      → 本地 Ollama LLM 生成。

复用前序代码：
- local_rag.SafeOllamaEmbeddings：分批 + 重试的本地 embedding（bge-m3）
- ollama_client.local_chat：本地 Ollama 对话（qwen2.5:7b-instruct-q4_K_M）
- 本地库 week4/chroma_local（collection=langchain，Day25 已入库 580 条）
"""
import sys
from pathlib import Path

# 项目根目录与当前脚本目录加入 sys.path，保证子目录直接运行能 import 前序模块
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

from langchain_chroma import Chroma  # noqa: E402
from langchain_core.documents import Document  # noqa: E402
from rank_bm25 import BM25Okapi  # noqa: E402
import jieba  # noqa: E402

from local_rag import SafeOllamaEmbeddings  # noqa: E402
from ollama_client import local_chat  # noqa: E402

DB_DIR = "./chroma_local"
COLLECTION_NAME = "langchain"
EMB_MODEL = "bge-m3"
# LLM 模型名以 ollama_client.MODEL 为准（qwen2.5:7b-instruct-q4_K_M）

VECTOR_K = 5      # 向量召回候选数
BM25_K = 5        # 关键词召回候选数
TOP_K = 3         # 融合后交给模型的片段数
RRF_K = 60        # RRF 融合常数
# 向量 L2 距离上限：越小越相关。本机库实测相关问题 Top1 ≈ 0.55–0.70，
# 无关问题 ≈ 1.18–1.30，阈值取中间 1.0；换库 / 换模型后需按实际分布重调。
VECTOR_DIST_THRESHOLD = 1.0
# BM25 最低分：向量已弱相关时，不单独采信低分关键词命中（通用词偶然匹配会虚高）。
# 实测强相关 ≈ 8.3–9.5，弱相关 ≈ 4.2，跨领域偶然命中 ≈ 5.3；阈值取 6.0，需按评测集微调。
BM25_SCORE_THRESHOLD = 6.0

SYSTEM_PROMPT = """你是知识库助手。严格只根据下面【参考资料】回答，资料没有就说"资料中未提及"，并标注来源。

【参考资料】
{context}
"""


def load_store() -> Chroma:
    """连接 Day25 已入库的本地 Chroma 库。"""
    embedding = SafeOllamaEmbeddings(model=EMB_MODEL)
    return Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=embedding,
        persist_directory=DB_DIR,
    )


def load_corpus(store: Chroma) -> list[Document]:
    """从本地库读出全部片段，作为 BM25 关键词语料（无需重新读文件分块）。"""
    data = store._collection.get(include=["documents", "metadatas"])
    corpus: list[Document] = []
    for content, meta in zip(data["documents"], data["metadatas"]):
        corpus.append(Document(page_content=content, metadata=meta or {}))
    return corpus


def _tokenize(text: str) -> list[str]:
    """中文 jieba 分词，过滤空白 token；停用词可按需再补一个停用词表。"""
    # 过滤：的、了、和
    stop_words = {"的", "了", "和"}
    return [w for w in jieba.lcut(text) if w.strip() and w not in stop_words]


def build_bm25(corpus: list[Document]) -> BM25Okapi:
    return BM25Okapi([_tokenize(d.page_content) for d in corpus])


def vector_search(store: Chroma, query: str, k: int = VECTOR_K) -> list[tuple[Document, float]]:
    """向量语义召回，返回 (Document, 距离) 列表。"""
    hits = store.similarity_search_with_score(query, k=k)
    return [(doc, float(score)) for doc, score in hits]


def bm25_search(bm25: BM25Okapi, corpus: list[Document],
                query: str, k: int = BM25_K) -> list[tuple[Document, float]]:
    """关键词召回，分数为 0（未命中任何词）的片段直接丢弃。"""
    scores = bm25.get_scores(_tokenize(query))
    ranked = sorted(zip(corpus, scores), key=lambda x: x[1], reverse=True)
    return [(doc, float(score)) for doc, score in ranked[:k] if score > 0]


def rrf_fuse(v_hits: list[tuple[Document, float]],
             b_hits: list[tuple[Document, float]],
             top_k: int = TOP_K, rrf_k: int = RRF_K) -> list[Document]:
    """RRF 倒数排名融合：按片段文本去重，两路排名分数累加，取前 top_k。"""
    scores: dict[str, float] = {}
    docs: dict[str, Document] = {}
    for rank, (doc, _) in enumerate(v_hits):
        key = doc.page_content
        scores[key] = scores.get(key, 0.0) + 1 / (rrf_k + rank + 1)
        docs.setdefault(key, doc)
    for rank, (doc, _) in enumerate(b_hits):
        key = doc.page_content
        scores[key] = scores.get(key, 0.0) + 1 / (rrf_k + rank + 1)
        docs.setdefault(key, doc)
    fused = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return [docs[key] for key, _ in fused[:top_k]]


def retrieve_optimized(query: str, store: Chroma, bm25: BM25Okapi,
                       corpus: list[Document], top_k: int = TOP_K) -> tuple[list[Document], str | None]:
    """混合检索 + 融合 + 兜底。返回 (片段列表, 兜底提示)；命中时兜底提示为 None。"""
    v_hits = vector_search(store, query, top_k)
    b_hits = bm25_search(bm25, corpus, query, top_k)

    print("BM25 命中：", len(b_hits))
    for doc, score in b_hits:
        print(f"  {doc.page_content.replace('\n', ' ')} | 分数：{score:.2f}")

    # 向量 Top1 距离超阈值视为弱相关；BM25 最高分低于阈值视为偶然命中。
    # 两路都不达标 → 兜底，不硬凑。
    v_strong = bool(v_hits) and v_hits[0][1] <= VECTOR_DIST_THRESHOLD
    b_strong = bool(b_hits) and b_hits[0][1] >= BM25_SCORE_THRESHOLD
    if not v_strong and not b_strong:
        return [], "资料中未提及"

    chunks = rrf_fuse(v_hits, b_hits, top_k=top_k)
    if not chunks:
        return [], "资料中未提及"
    return chunks, None


def build_context(chunks: list[Document]) -> str:
    return "\n\n".join(
        f"[来自 {c.metadata.get('source', '未知')}]\n{c.page_content}" for c in chunks
    )


def answer(question: str, chunks: list[Document]) -> str:
    """拼上下文后调本地 Ollama 模型生成回答。"""
    context = build_context(chunks)
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT.format(context=context)},
        {"role": "user", "content": question},
    ]
    return local_chat(messages, temperature=0.3)


def main():
    store = load_store()
    total = store._collection.count()
    print(f"本地库条数：{total}")
    if total == 0:
        print("库为空，请先运行 local_rag.py 入库")
        return

    corpus = load_corpus(store)
    bm25 = build_bm25(corpus)
    print(f"BM25 语料：{len(corpus)} 段")

    question = "怎么划分财产"
    chunks, fallback = retrieve_optimized(question, store, bm25, corpus)
    print(f"\n问：{question}")

    if fallback:
        print(f"答：{fallback}")
        return

    print(f"召回 {len(chunks)} 段：")
    for i, c in enumerate(chunks, 1):
        preview = c.page_content[:60].replace("\n", " ")
        print(f"  {i}. {c.metadata.get('source')} | {preview}")

    reply = answer(question, chunks)
    print(f"\n答：{reply}")


if __name__ == "__main__":
    main()
