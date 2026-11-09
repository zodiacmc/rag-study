# ingest.py
import os
import sys
from pathlib import Path

# 项目根目录与当前脚本目录加入 sys.path，保证直接运行可 import
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import chromadb
from langchain_text_splitters import RecursiveCharacterTextSplitter

from TextCleaner import TextCleaner
from embedding_client import get_embedding

# 库目录锚定到脚本所在目录，避免工作目录不同导致写到别处
DB_PATH = Path(__file__).resolve().parent / "chroma_db"
client = chromadb.PersistentClient(path=str(DB_PATH))

# 只有在旧集合维度/脏库需要重建时才置 True；正常增量入库保持 False
RESET = False
if RESET:
    try:
        client.delete_collection("policy_docs")
    except Exception as e:
        print(f"旧集合删除跳过：{e}")

col = client.get_or_create_collection("policy_docs")

splitter = RecursiveCharacterTextSplitter(
    chunk_size=400, chunk_overlap=80,
    separators=["\n\n", "\n", "。", "，", " ", ""]
)

TXT_DIR = ROOT / "week2" / "out_text"


def ingest_file(txt_file:Path):
    """将文件 txt_file 加入 Chroma 数据库，对文件分块向量化"""
    text = ""
    try:
       text = txt_file.read_text(encoding='utf-8')
    except Exception as e:
        print(f"Error reading {txt_file.resolve()}: {e}")
        # 抛出异常
        raise e
    if text == "":
        print(f"Error: {txt_file.resolve()} is empty")
        return

    text = TextCleaner().clean(text)  # 先都去清理一下吧

    # 对文档进行分块
    chunks = splitter.split_text(text)
    print(f"  {os.path.basename(txt_file.resolve())} → {len(chunks)} 块")

    ids, docs, vecs, metas = [], [], [], []
    for i, ch in enumerate(chunks):
        print(f"    {i} → {ch[:100]}...")
        vec = get_embedding(ch)  # 获取当前文本的向量数据
        ids.append(f"{os.path.basename(txt_file.resolve())}_{i}")
        docs.append(ch)
        vecs.append(vec)
        metas.append({"source": txt_file.name, "chunk_id": i})

    # upsert：ID 已存在则覆盖，重复灌入不会报重复 ID 错误
    col.upsert(ids=ids, documents=docs, embeddings=vecs, metadatas=metas)




if __name__ == "__main__":
    # 默认先灌一份小文件验证链路；需要全量入库时注释掉下面两行，放开遍历
    txt_path = TXT_DIR / "产品手册类" / "LibreOffice 6.2 快速参考指南.txt"
    ingest_file(txt_path)

    # 遍历所有 txt 全量灌库（民法典/手册等，向量调用较多，耗时较长）
    # for f in TXT_DIR.rglob("*.txt"):
    #     ingest_file(f)

    print(f"完成，共 {col.count()} 块在库")
