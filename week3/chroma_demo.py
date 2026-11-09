from pathlib import Path

import chromadb

from week3.chunking_demo import file_text_chunking

# 1. 创建本地客户端（数据存到 ./chroma_db 文件夹）
client = chromadb.PersistentClient(path="./chroma_db")
# 2. 建一个"集合"（类似一张表）
col = client.get_or_create_collection("policy_docs")


def insert_data():
    # 3. 加数据（每条：id + 文本 + 向量 + 元数据）
    col.add(
        ids=["chunk_1", "chunk_2", "chunk_3"],
        documents=[
            "离职补偿金按工作年限算，每满一年支付一个月工资",
            "加班费工作日1.5倍，周末2倍，法定节假日3倍",
            "公司实行996工作制是违法的"
        ],
        embeddings=[
            [0.1, 0.2, 0.3],  # 占位，后面换成真embedding
            [0.5, 0.1, 0.2],
            [0.3, 0.8, 0.1]
        ],
        metadatas=[
            {"source": "合规管理办法.pdf", "page": 3},
            {"source": "劳动用工指南.pdf", "page": 12},
            {"source": "劳动用工指南.pdf", "page": 15}
        ]
    )

    print(f"集合里有 {col.count()} 条")


def select_data():
    # 查：和"被辞退怎么赔偿"最相关的 2 条
    results = col.query(
        query_embeddings=[[0.15, 0.25, 0.28]],  # 换成问题的真embedding；注意是复数 embeddings，且外层包一层列表
        n_results=2
    )
    for doc, dist, meta in zip(results["documents"][0],
                               results["distances"][0],
                               results["metadatas"][0]):
        print(f"距离={dist:.3f} | 来源={meta['source']}")
        print(f"  内容：{doc}")
        print()

def update_data():
    col.update(
        ids=["chunk_1"],
        embeddings=[[0.1, 0.2, 0.3]],
        metadatas=[{"source": "合规管理办法.pdf", "page": 3}],
        documents=["离职补偿金按工作年限算，每满一年支付一个月工资，但不能超过员工两年工资"]
    )
    print(f"更新后的集合里有 {col.count()} 条")

def delete_data():
    col.delete(ids=["chunk_1", "chunk_2", "chunk_3"])
    print(f"删除后的集合里有 {col.count()} 条")



if __name__ == "__main__":
    delete_data()