# retrieve.py
import sys
import re
import difflib
from pathlib import Path

# 项目根目录与当前脚本目录加入 sys.path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import chromadb

from embedding_client import get_embedding

DB_PATH = Path(__file__).resolve().parent / "chroma_db"
client = chromadb.PersistentClient(path=str(DB_PATH))
col = client.get_or_create_collection("policy_docs")

# 近似重复判定阈值：两段正文相似度高于该值视为重复块
DUP_THRESHOLD = 0.85


def _normalize(text):
    """归一化正文：去掉所有空白字符，便于判重。"""
    return re.sub(r"\s+", "", text or "")


def _is_duplicate(a, b):
    """判断两段归一化正文是否近似重复。

    命中规则：完全相同、互为包含，或 SequenceMatcher 相似度高于阈值。
    """
    if not a or not b:
        return False
    if a == b:
        return True
    if a in b or b in a:
        return True
    return difflib.SequenceMatcher(None, a, b).ratio() >= DUP_THRESHOLD


def retrieve(question, top_k=3):
    """根据问题检索相似的文档，并对近似重复块去重。"""
    total = col.count()
    if total == 0:
        print(f"⚠️ 库为空（0 条），请先运行 ingest.py 入库\n")
        return

    q_vec = get_embedding(question)
    # 先取 top_k 的 3 倍作为候选池，去重后再裁到 top_k，避免重复块占满名额
    pool_size = top_k * 3
    results = col.query(query_embeddings=[q_vec], n_results=pool_size)

    docs = results["documents"][0]
    dists = results["distances"][0]
    metas = results["metadatas"][0]

    print(f"🔍 问题：{question}（库内 {total} 条）\n")
    if not docs or docs[0] is None:
        print("  未检索到相关内容\n")
        return

    kept = []  # (doc, dist, meta, normalized)
    for doc, dist, meta in zip(docs, dists, metas):
        norm = _normalize(doc)
        if any(_is_duplicate(norm, item[3]) for item in kept):
            continue
        kept.append((doc, dist, meta, norm))
        if len(kept) == top_k:
            break

    for i, (doc, dist, meta, _) in enumerate(kept, 1):
        print(f"【Top{i}】距离={dist:.3f} 来源={meta['source']}")
        print(f"  {doc}...\n")


# 测试
retrieve("打印功能提示")
retrieve("加班费标准")
