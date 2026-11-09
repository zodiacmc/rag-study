# -*- coding: utf-8 -*-
"""
Chroma 入库 / 检索通用排查脚本
  一、底层 sqlite 核对：只用标准库 sqlite3，不依赖 chromadb / numpy，库没起来也能查
  二、Chroma 客户端核对：需要 chromadb + numpy，正常运行环境已具备
用法：在 week3 目录下执行  python diag_chroma.py
"""
import sqlite3
from pathlib import Path

DB_DIR = Path(__file__).resolve().parent / "chroma_db"
SQLITE = DB_DIR / "chroma.sqlite3"


def report_sqlite():
    """不启动 Chroma，直接读底层 sqlite，核对数据是否真的落盘。"""
    print("=" * 55)
    print("【一、底层 sqlite 核对（无需 chromadb）】")
    if not SQLITE.exists():
        print("  未找到 chroma.sqlite3：库目录不存在，入库从未落盘。")
        return

    con = sqlite3.connect(SQLITE)
    cur = con.cursor()

    # 1. 集合与锁定维度
    print("\n-- 集合 --")
    for cid, name, dim in cur.execute(
        "SELECT id, name, dimension FROM collections"
    ):
        print(f"  {name}  dimension={dim}  id={cid}")

    # 2. 各关键表条数
    print("\n-- 表条数 --")
    for tbl in [
        "embeddings",
        "embedding_metadata",
        "embeddings_queue",
        "embedding_fulltext_search_content",
    ]:
        try:
            cnt = cur.execute(f"SELECT COUNT(*) FROM {tbl}").fetchone()[0]
            print(f"  {tbl}: {cnt} 条")
        except Exception as e:
            print(f"  {tbl}: 读取失败 {e}")

    # 3. 已落盘的文档样本（document 存在 metadata 的 chroma:document 键）
    print("\n-- 已落盘文档样本 --")
    try:
        rows = cur.execute(
            """
            SELECT e.embedding_id, m.string_value
            FROM embeddings e
            JOIN embedding_metadata m ON m.id = e.id
            WHERE m.key = 'chroma:document'
            LIMIT 5
            """
        ).fetchall()
        if not rows:
            print("  无已落盘文档（embeddings / metadata 为空）")
        for eid, doc in rows:
            print(f"  {eid} | {(doc or '')[:50]}")
    except Exception as e:
        print(f"  样本读取失败：{e}")

    # 4. 队列里的向量维度（FLOAT32 = 4 字节/维）
    print("\n-- 队列向量维度 --")
    q = cur.execute(
        "SELECT id, encoding, length(vector) FROM embeddings_queue LIMIT 1"
    ).fetchone()
    if q:
        eid, enc, nbytes = q
        dim = nbytes // 4 if enc == "FLOAT32" else None
        print(f"  样本 {eid}  encoding={enc}  blob={nbytes} 字节  推断维度={dim}")
    else:
        print("  队列为空")

    con.close()


def report_chroma():
    """通过 Chroma 客户端核对条数、样本与向量维度。"""
    print("\n" + "=" * 55)
    print("【二、Chroma 客户端核对】")
    try:
        import chromadb

        client = chromadb.PersistentClient(path=str(DB_DIR))
        for col in client.list_collections():
            c = client.get_collection(col.name)
            print(f"\n集合 {col.name}  条数={c.count()}")
            got = c.peek(limit=3)
            print("  样本文档:", [d[:40] for d in got["documents"]])
            embs = got["embeddings"]
            if embs is not None and len(embs):
                print("  向量维度:", len(embs[0]))
            else:
                print("  向量: 空")
    except Exception as e:
        print(f"  客户端核对跳过：{type(e).__name__}: {e}")


if __name__ == "__main__":
    report_sqlite()
    report_chroma()
