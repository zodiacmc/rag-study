import sys
from pathlib import Path

# 把项目根目录加入 sys.path，保证直接运行脚本能 import util
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import requests
from util.GetProperties import GetProperties

API_KEY = GetProperties().get_property("aliyun", "aliyun_apikey")
API_URL = GetProperties().get_property("aliyun", "aliyun_multimodal_embedding_url")
MODEL = "qwen3-vl-embedding"


def get_embedding(text):
    """把一段文字变成向量（数字列表）"""
    input_json = {"contents": [{"text": text}]}
    resp = requests.post(
        API_URL,
        headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
        json={"model": MODEL, "input": input_json},
        timeout=30
    )
    data = resp.json()
    return data["output"]["embeddings"][0]["embedding"]


import math

def cosine_sim(a, b):
    """两个向量的余弦相似度：范围 -1 ~ 1，越接近1越相似"""
    dot = sum(x*y for x, y in zip(a, b))          # 点积
    norm_a = math.sqrt(sum(x*x for x in a))       # a 的长度
    norm_b = math.sqrt(sum(y*y for y in b))      # b 的长度
    return dot / (norm_a * norm_b)

# 也可以用 numpy 一行搞定：
# import numpy as np
# def cosine_sim(a, b):
#     a, b = np.array(a), np.array(b)
#     return float(a @ b / (np.linalg.norm(a) * np.linalg.norm(b)))

# 测试
# vec = get_embedding("今天天气很好")
# print(f"向量维度：{len(vec)}")
# print(f"前5个数字：{vec[:5]}")
#
# texts = [
#     "离职补偿金怎么算",
#     "员工被辞退能拿到多少赔偿",
#     "今天中午吃什么",
# ]
#
# vecs = [get_embedding(t) for t in texts]
# print(f"问题 vs 句子1：{cosine_sim(vecs[0], vecs[1]):.4f}")  # 应该 > 0.8
# print(f"问题 vs 句子2：{cosine_sim(vecs[0], vecs[2]):.4f}")  # 应该 < 0.3

if __name__ == "__main__":
    # 问题
    question = "技术咨询合同和技术服务合同有什么规定"
    question_vec = get_embedding(question)

    sentence_list = ["技术咨询合同的受托人应当按照约定的期限完成咨询报告或者解答问题，提出的咨询报告应当达到约定的要求。",
                     "管理人管理事务不属于前条规定的情形，但是受益人享有管理利益的，受益人应当在其获得的利益范围内向管理人承担前条第一款规定的义务。",
                     "青霉素可以治疗什么?"]

    # 获取三个句子和问题的相关性，并按照相关性进行逆序排列
    sentence_scores = [(sentence, cosine_sim(question_vec, get_embedding(sentence))) for sentence in sentence_list]

    sentence_scores = sorted(sentence_scores, key=lambda x: x[1], reverse=True)
    print(sentence_scores)








